from app.models.migratesite_request import MigratesiteRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from fastapi import HTTPException
import requests
import random
import time
import paramiko
import os
import json
import io
from datetime import datetime
import threading
import time

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
class MigratesiteController:
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
    async def migrate_site(request: MigratesiteRequest):
        SOURCE_IP = request.source_ip
        TARGET_IP = request.target_ip
        TEAM = request.team
        USERNAMES = ["ubuntu", "ec2-user"]
        LOCAL_SCRIPT_PATH = "app/script/copy-site-between2server.sh"
        REMOTE_SCRIPT_PATH = "/tmp/copy-site-between2server.sh"
        REMOTE_RESTORE_SCRIPT_PATH = "/root/restore-website.sh"
        REMOTE_KEY_PATH = "/tmp/target_server_key.pem"  # We'll use this on target server to connect back to source
        result = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}} 

        try:
            # Get credentials for both servers
            source_key_name = f"{TEAM}_{SOURCE_IP}"
            target_key_name = f"{TEAM}_{TARGET_IP}"
            
            if SSH_TEAM and TEAM in SSH_TEAM:
                source_user = await MigratesiteController.fetch_username_from_api(source_key_name)
                target_user = await MigratesiteController.fetch_username_from_api(target_key_name)
                TARGET_USERNAMES = [target_user]
            else:
                source_user = "ubuntu"
                target_user = "ubuntu"
                TARGET_USERNAMES = USERNAMES
            
            # Get private keys for both servers
            private_key_content_source = await MigratesiteController.fetch_private_key_from_api(source_key_name)
            private_key_content_target = await MigratesiteController.fetch_private_key_from_api(target_key_name)
            
            # Load target private key for SSH
            source_private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content_source))
            target_private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content_target))

            # Connect to target server
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try connecting to target with different usernames
            connected_user = None
            connection_errors = []
            for USERNAME in TARGET_USERNAMES:
                try:
                    ssh_client.connect(SOURCE_IP, username=USERNAME, pkey=source_private_key)
                    connected_user = USERNAME
                    print(f"Connected successfully to target with username: {USERNAME}")
                    break
                except Exception as e:
                    print(f"Error connecting to target with username {USERNAME}: {str(e)}")
                    connection_errors.append(str(e))

            # Check if connection failed
            if not connected_user:
                if all("Errno 13" in error for error in connection_errors):
                    raise PermissionError("All attempts to connect to target server failed with Errno 13: Permission denied")
                else:
                    raise Exception("All attempts to connect to target server failed with different errors")

            # Upload script and source key to target server
            sftp = ssh_client.open_sftp()
            sftp.put(LOCAL_SCRIPT_PATH, REMOTE_SCRIPT_PATH)
            sftp.chmod(REMOTE_SCRIPT_PATH, 0o755)
            
            # Create temporary source key file and upload to target
            temp_key_file = "/tmp/temp_source_key.pem"
            with open(temp_key_file, 'w') as f:
                f.write(private_key_content_source)
            
            sftp.put(temp_key_file, REMOTE_KEY_PATH)
            sftp.chmod(REMOTE_KEY_PATH, 0o600)  # Set correct permissions for key file
            sftp.close()

            # Execute the command on target server
            # Execute the command on target server
            source_domain = request.source_domain

            # Thêm timeout dài hơn
            command = f"sudo bash {REMOTE_SCRIPT_PATH} {TARGET_IP} {target_user} {REMOTE_KEY_PATH} {source_domain}"

            print(f"Executing: {command}")
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=300)  # Tăng timeout lên 5 phút

            # Đọc output theo thời gian thực
            output = ""
            for line in iter(stdout.readline, ""):
                print(line, end="")
                output += line

            error = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()  # Đợi đến khi lệnh hoàn tất

            if exit_status != 0:
                print(f"Command exited with status {exit_status}")
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"Command failed with exit code {exit_status}: {error}")
            else:
                result["success"]["count"] += 1
                result["success"]["messages"].append(f"{request.source_domain}: migrate site successfully")
        except Exception as e:
            print(f"Exception Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))

        return {"status": "success", "result": result}
        