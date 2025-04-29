import paramiko.rsakey
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
import re

SSH_TEAM = os.getenv('SSH_TEAM')
SSH_KEY_FILE = os.getenv('SSH_KEY_FILE')
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
    def validate_private_key(key_content: str):
        """
        Validate private key content before uploading.

        Raises ValueError if the key is invalid.
        """
        key_content = key_content.strip()

        # Kiểm tra header/footer chuẩn
        if not (
            key_content.startswith("-----BEGIN") and 
            (key_content.endswith("-----END RSA PRIVATE KEY-----") or key_content.endswith("-----END OPENSSH PRIVATE KEY-----"))
        ):
            raise ValueError("Private key does not have valid BEGIN/END headers")

        # Check xem có base64 bên trong không (rất cơ bản)
        base64_content = re.sub(r"-----.*-----", "", key_content).strip().replace('\n', '')
        if not re.match(r"^[A-Za-z0-9+/=]+$", base64_content):
            raise ValueError("Private key content is not valid base64")

        print("✅ Private key validated successfully.")


    @staticmethod
    async def migrate_site(request: MigratesiteRequest):
        SOURCE_IP = request.source_ip
        TARGET_IP = request.target_ip
        TEAM = request.team
        USERNAMES = ["root", "ec2-user", "ubuntu"]
        LOCAL_SCRIPT_PATH = "app/script/copy-site-between2server.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_copy-site-between2server.sh"
        REMOTE_KEY_PATH = "/tmp/target_server_key"  # Use .pem extension for clarity
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
                source_user = "root"
                target_user = "root"
                TARGET_USERNAMES = USERNAMES
            
            # Get source private key from API
            private_key_content_source = await MigratesiteController.fetch_private_key_from_api(source_key_name)
            # Load source private key for SSH
            source_private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content_source))
            
            # Connect to source server
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connected_user = None
            connection_errors = []
            for USERNAME in TARGET_USERNAMES:
                try:
                    ssh_client.connect(SOURCE_IP, username=USERNAME, pkey=source_private_key)
                    connected_user = USERNAME
                    print(f"Connected successfully to source with username: {USERNAME}")
                    break
                except Exception as e:
                    print(f"Error connecting to source with username {USERNAME}: {str(e)}")
                    connection_errors.append(str(e))

            # Check if connection failed
            if not connected_user:
                if all("Errno 13" in error for error in connection_errors):
                    raise PermissionError("All attempts to connect to source server failed with Errno 13: Permission denied")
                else:
                    raise Exception("All attempts to connect to source server failed with different errors")

            # Upload script and target key to source server
            sftp = ssh_client.open_sftp()
            sftp.put(LOCAL_SCRIPT_PATH, REMOTE_SCRIPT_PATH)
            sftp.chmod(REMOTE_SCRIPT_PATH, 0o755)
            
            with sftp.file(REMOTE_KEY_PATH, 'wb') as remote_key_file:
                data = private_key_content_source
                if not data.endswith('\n'):
                    data += '\n'
                remote_key_file.write(data.encode('utf-8'))
                remote_key_file.chmod(0o600)

            sftp.close()
            
            # Execute the site migration command
            source_domain = request.source_domain
            command = (
                f"bash {REMOTE_SCRIPT_PATH} {TARGET_IP} {target_user} {REMOTE_KEY_PATH} {source_domain} --ssh-opts='-o HostKeyAlgorithms=ssh-rsa -o PubkeyAcceptedKeyTypes=ssh-rsa'"
            )
            print(f"Executing: {command}")
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=300)  # 5 minute timeout

            # Read output in real time
            output = ""
            for line in iter(stdout.readline, ""):
                print(line, end="")
                output += line

            error = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()  

            if exit_status != 0:
                print(f"Command exited with status {exit_status}")
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"Command failed with exit code {exit_status}: {error}")
            else:
                result["success"]["count"] += 1
                result["success"]["messages"].append(f"{request.source_domain}: migrate site successfully")
                
                # Add site to Google Sheet if successful
                if hasattr(request, 'add_to_sheet') and request.add_to_sheet:
                    MigratesiteController.append_to_google_sheet(request.source_domain, TARGET_IP)
                    
            # Clean up temporary files
            # ssh_client.exec_command(f"rm -f {REMOTE_KEY_PATH} {REMOTE_SCRIPT_PATH}")
            
            # Close SSH connection
            ssh_client.close()
            
        except Exception as e:
            print(f"Exception Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))

        return {"status": "success", "result": result}
    