from app.models.dashboard_request import DashboardRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from fastapi import HTTPException, Query
import requests
import random
import time
import paramiko
import os
import json
import io
from datetime import datetime

api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}
class DashboardController:
    @staticmethod
    async def fetch_private_key_from_api(key_name: str):
        params = {
            "page": 1,
            "limit": 10000,
            "search": key_name,
            "sortBy": "team",
            "sortDesc": "false",
        }
        response = requests.get(url_backend, params=params, headers=headers_backend)
        # Kiểm tra lỗi HTTP
        response.raise_for_status()
        try:
            data = response.json()  
        except requests.JSONDecodeError:
            raise ValueError("Response is not a valid JSON")
        servers = data.get("data", []) 
        # Trả về danh sách account
        return servers[0]["private_key"]

    @staticmethod
    async def count_domains(server_ip: str = Query(...), team: str = Query(...)):
        SERVER_IP = server_ip
        TEAM = team
        USERNAMES = ["ubuntu", "ec2-user"]
        LOCAL_SCRIPT_PATH = "app/script/wptt-list-domain.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_wptt-list-domain.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}}

        try:
            connected_user = None  # Lưu user kết nối thành công
            connection_errors = []  # Lưu danh sách lỗi trong quá trình kết nối
            key_name = f"{TEAM}_{SERVER_IP}"
            private_key_content = await DashboardController.fetch_private_key_from_api(key_name)

            # Load private key content into paramiko.RSAKey
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))

            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Thử kết nối với từng user
            for USERNAME in USERNAMES:
                try:
                    ssh_client.connect(SERVER_IP, username=USERNAME, pkey=private_key)
                    connected_user = USERNAME
                    print(f"Connected successfully with username: {USERNAME}")
                    break
                except paramiko.AuthenticationException:
                    print(f"Authentication failed for username: {USERNAME}")
                    connection_errors.append(f"Authentication failed for username: {USERNAME}")
                except Exception as e:
                    print(f"Error connecting with username {USERNAME}: {str(e)}")
                    connection_errors.append(str(e))

            # Kiểm tra nếu không có kết nối thành công
            if not connected_user:
                # Kiểm tra nếu toàn bộ lỗi đều là Errno 13
                if all("Errno 13" in error for error in connection_errors):
                    raise PermissionError("All attempts failed with Errno 13: Permission denied")
                else:
                    raise Exception("All attempts to connect failed with different errors")


            sftp = ssh_client.open_sftp()
            sftp.put(LOCAL_SCRIPT_PATH, REMOTE_SCRIPT_PATH)
            sftp.chmod(REMOTE_SCRIPT_PATH, 0o755)
            sftp.close()

            command = f"sudo bash {REMOTE_SCRIPT_PATH}"
            stdin, stdout, stderr = ssh_client.exec_command(command)


            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh_client.close()
            try:
                if output.strip():  
                    so_luong_website = int(output.strip())
                    print(f"Number of websites: {so_luong_website}")  
                    result["success"] = so_luong_website
                else: 
                    print(f"Error: {error.strip()}") 
                    result["fail"]["count"] += 1
                    result["fail"]["messages"].append("Missing so_luong_website in script output.")
            except ValueError:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append("Invalid format for so_luong_website.")

            return {"status": "success", "result": result}

        except Exception as e:
            print(f"Exception Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            return {"status": "success", "result": result}
