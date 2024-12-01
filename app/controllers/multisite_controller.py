from app.models.multisite_request import MultisiteRequest
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

api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}

class MultisiteController:
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
    def append_to_google_sheet(domain, SERVER_IP):
        try:
            # Thông tin Google Sheets
            SPREADSHEET_ID = '1E6f0UZ_e1Ec4m_vI2coJHebIX8DiEq8gam0PeiEdOXY'  # Thay bằng ID của Google Sheet
            SHEET_NAME = 'server'  # Thay bằng tên sheet

            # Load credentials từ file service account
            creds = Credentials.from_service_account_file(
                'app/key/seo-admin-442609-152c2f330723.json',
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
    async def multi_site(request: MultisiteRequest):
        SERVER_IP = request.server_ip
        TEAM = request.team
        USERNAME = "ubuntu"
        LOCAL_SCRIPT_PATH = "app/script/auto_add_multiple_wp_sites.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_auto_add_multiple_wp_sites.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}} 
        for domain in request.domains:
            try:
                key_name = f"{TEAM}_{SERVER_IP}"
                private_key_content = await MultisiteController.fetch_private_key_from_api(key_name)

                # Load private key content into paramiko.RSAKey
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))

                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to the server using the private key
                ssh_client.connect(SERVER_IP, username=USERNAME, pkey=private_key)



                sftp = ssh_client.open_sftp()
                sftp.put(LOCAL_SCRIPT_PATH, REMOTE_SCRIPT_PATH)
                sftp.chmod(REMOTE_SCRIPT_PATH, 0o755)
                sftp.close()

                command = f"sudo bash {REMOTE_SCRIPT_PATH} {domain}"
                stdin, stdout, stderr = ssh_client.exec_command(command)

                output = stdout.read().decode()
                error = stderr.read().decode()
                ssh_client.close()

                if error.strip():
                    result["fail"]["count"] += 1
                    result["fail"]["messages"].append(f"{domain}: {error.strip()}")
                else:
                    result["success"] += 1
                    MultisiteController.append_to_google_sheet(domain, SERVER_IP)
            except Exception as e:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"{domain}: {str(e)}")
        return {"status": "success", "result": result}

