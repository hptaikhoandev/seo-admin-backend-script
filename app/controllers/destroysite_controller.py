from app.models.destroysite_request import DestroysiteRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from fastapi import HTTPException
import requests
import random
import time
import paramiko
import os
import io
from datetime import datetime

SSH_TEAM=os.getenv('SSH_TEAM')
api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID0', '')
SHEET_NAME = os.getenv('SHEET_NAME', 'server')
SHEET_CONFIG_FILE = os.getenv('SHEET_CONFIG_FILE', '')

class DestroysiteController:
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
    async def fetch_username_from_api(key_name: str):
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
        return servers[0]["username"]

    @staticmethod
    def append_to_google_sheet(domain, SERVER_IP):
        try:
            # Load credentials từ file service account
            creds = Credentials.from_service_account_file(
                SHEET_CONFIG_FILE,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            service = build('sheets', 'v4', credentials=creds)
            current_date = datetime.now().strftime('%d/%m/%Y')
            # Chuẩn bị dữ liệu để ghi vào sheet
            values = [
                [
                    current_date,
                    'seo3-wptt-05', 
                    SERVER_IP, 
                    domain, 
                    'https://' + domain + '/admin',
                    'admin',
                    'hp@123@a',
                    'Not Yet',
                    'PNB',
                ]
            ]
            body = {'values': values}
            # Append dữ liệu vào Google Sheet
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

            print(f"Appended {domain} to Google Sheet.")
        except HttpError as error:
            print(f"An error occurred: {error}")
            
    @staticmethod
    async def destroy_site(request: DestroysiteRequest):
        SERVER_IP = request.server_ip
        TEAM = request.team
        USERNAMES = ["ubuntu", "ec2-user"]
        LOCAL_SCRIPT_SAOLUU_PATH = "app/script/wptt-saoluu.sh"
        REMOTE_SCRIPT_SAOLUU_PATH = "/tmp/remote_wptt-saoluu.sh"
        LOCAL_SCRIPT_XOA_PATH = "app/script/wptt-xoa-website.sh"
        REMOTE_SCRIPT_XOA_PATH = "/tmp/remote_wptt-xoa-website.sh"
        result = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}} 
        for domain in request.domains:
            try:
                connected_user = None  # Lưu user kết nối thành công
                connection_errors = []  # Lưu danh sách lỗi trong quá trình kết nối
                key_name = f"{TEAM}_{SERVER_IP}"
                if SSH_TEAM and TEAM in SSH_TEAM:
                    current_user = await DestroysiteController.fetch_username_from_api(key_name)
                    USERNAMES = [current_user]
                private_key_content = await DestroysiteController.fetch_private_key_from_api(key_name)
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Thử kết nối với từng user
                for USERNAME in USERNAMES:
                    try:
                        ssh_client.connect(SERVER_IP, username=USERNAME, pkey=private_key)
                        connected_user = USERNAME
                        print(f"Connected successfully with username: {USERNAME}")
                        break  # Thoát vòng lặp khi kết nối thành công
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
                sftp.put(LOCAL_SCRIPT_SAOLUU_PATH, REMOTE_SCRIPT_SAOLUU_PATH)
                sftp.put(LOCAL_SCRIPT_XOA_PATH, REMOTE_SCRIPT_XOA_PATH)
                sftp.chmod(REMOTE_SCRIPT_SAOLUU_PATH, 0o755)
                sftp.chmod(REMOTE_SCRIPT_XOA_PATH, 0o755)
                sftp.close()
                # STEP 1
                command_1 = f"sudo bash {REMOTE_SCRIPT_SAOLUU_PATH} {domain}"
                stdin, stdout, stderr = ssh_client.exec_command(command_1)
                
                # STEP 2
                command_2 = f"sudo bash {REMOTE_SCRIPT_XOA_PATH} {domain}"
                stdin, stdout, stderr = ssh_client.exec_command(command_2)

                output = stdout.read().decode()
                error = stderr.read().decode()
                ssh_client.close()

                if error.strip():
                    result["fail"]["count"] += 1
                    result["fail"]["messages"].append(f"{domain}: {error.strip()}")
                    print(f"1-SSH Client Error: {error.strip()}") 

                else:
                    result["success"]["count"] += 1
                    result["success"]["messages"].append(f"{domain}: destroy site successfully")
            except Exception as e:
                result["fail"]["count"]["count"] += 1
                result["fail"]["messages"].append(f"{domain}: {str(e)}")
                print(f"2-SSH Client Error: {str(e)}") 

        return {"status": "success", "result": result}

