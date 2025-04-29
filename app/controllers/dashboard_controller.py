from app.models.dashboard_request import DashboardRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from fastapi import HTTPException, Query
import requests
import paramiko
import os
import json
import io
from datetime import datetime
import boto3 
from dotenv import load_dotenv
from app.constants.constants import ec2_params

# Xóa cache của biến môi trường
os.environ.clear()
load_dotenv()
AWS_ACCESS_KEY=os.getenv('AWS_ACCESS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')
SSH_TEAM=os.getenv('SSH_TEAM')
api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend_private_key = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
url_backend_sites = f"{os.getenv('URL_DOMAIN_BACKEND')}/tasks"
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
        response = requests.get(url_backend_private_key, params=params, headers=headers_backend)
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
    async def fetch_sites_from_api(server_ip: str, team: str):
        params = {
            "page": 1,
            "limit": 10000,
            "search": team,
            "sortBy": "team",
            "sortDesc": "false",
        }

        response = requests.get(url_backend_sites, params=params, headers=headers_backend)

        # Kiểm tra lỗi HTTP
        response.raise_for_status()
        try:
            data = response.json()  
        except requests.JSONDecodeError:
            raise ValueError("Response is not a valid JSON")
        siteList = data.get("data", []) 
        site = next((item for item in siteList if item["server_ip"] == server_ip), None)
        print(f"===>ffff: {site}")

        # Trả về danh sách sites
        if site is not None:
            return site["sites"]
        else:
            return 0
        
    @staticmethod
    async def fetch_cpu_from_api(server_ip: str, team: str):
        params = {
            "page": 1,
            "limit": 10000,
            "search": team,
            "sortBy": "team",
            "sortDesc": "false",
        }

        response = requests.get(url_backend_sites, params=params, headers=headers_backend)

        # Kiểm tra lỗi HTTP
        response.raise_for_status()
        try:
            data = response.json()  
        except requests.JSONDecodeError:
            raise ValueError("Response is not a valid JSON")
        siteList = data.get("data", []) 
        site = next((item for item in siteList if item["server_ip"] == server_ip), None)

        # Trả về danh sách sites
        if site is not None:
            return site["cpu"]
        else:
            return 0
    
    @staticmethod
    async def fetch_ram_from_api(server_ip: str, team: str):
        params = {
            "page": 1,
            "limit": 10000,
            "search": team,
            "sortBy": "team",
            "sortDesc": "false",
        }

        response = requests.get(url_backend_sites, params=params, headers=headers_backend)

        # Kiểm tra lỗi HTTP
        response.raise_for_status()
        try:
            data = response.json()  
        except requests.JSONDecodeError:
            raise ValueError("Response is not a valid JSON")
        siteList = data.get("data", []) 
        site = next((item for item in siteList if item["server_ip"] == server_ip), None)

        # Trả về danh sách sites
        if site is not None:
            return site["ram"]
        else:
            return 0
        
    @staticmethod
    async def fetch_username_from_api(key_name: str):
        params = {
            "page": 1,
            "limit": 10000,
            "search": key_name,
            "sortBy": "team",
            "sortDesc": "false",
        }
        response = requests.get(url_backend_private_key, params=params, headers=headers_backend)
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
    async def count_domains(server_ip: str = Query(...), team: str = Query(...)):
        SERVER_IP = server_ip
        TEAM = team
        USERNAMES = ["root", "ec2-user", "ubuntu"]
        LOCAL_SCRIPT_PATH = "app/script/wptt-list-domain.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_wptt-list-domain.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        try:
            connected_user = None  # Lưu user kết nối thành công
            connection_errors = []  # Lưu danh sách lỗi trong quá trình kết nối
            key_name = f"{TEAM}_{SERVER_IP}"

            if SSH_TEAM and TEAM in SSH_TEAM:
                current_user = await DashboardController.fetch_username_from_api(key_name)
                USERNAMES = [current_user]
            
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
        
    @staticmethod
    async def param_dashboard(server_ip: str = Query(...), team: str = Query(...)):
        ec2_param = next((item for item in ec2_params if item["team"] == team), None)
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        outputCPU = 0
        outputRAM = 0
        outputSite = 0
        try:
            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY, 
                aws_secret_access_key=AWS_SECRET, 
                region_name=ec2_param["region"]
            )

            # Tìm InstanceId bằng IP
            response = ec2_client.describe_instances(
                Filters=[
                    {'Name': 'ip-address', 'Values': [server_ip]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
            
            if not response['Reservations']:
                print(f"No instance found with IP: {server_ip}")
            else:
                instance = response['Reservations'][0]['Instances'][0]
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                print(f"Instance ID: {instance_id}")
                print(f"Instance Type: {instance_type}")
                # Lấy thông tin RAM và CPU từ loại instance
                instance_type_info = ec2_client.describe_instance_types(
                    InstanceTypes=[instance_type]
                )
                instance_details = instance_type_info['InstanceTypes'][0]
                outputCPU = instance_details['VCpuInfo']['DefaultVCpus']
                outputRAM = instance_details['MemoryInfo']['SizeInMiB']

            outputSite = await DashboardController.fetch_sites_from_api(server_ip, team)
            
            return {
                "status": "success",
                "result": result,
                "data": {
                    "cpu": outputCPU,
                    "ram": outputRAM,
                    "site": outputSite,
                },
            }
        
        except Exception as e:
            print(f"Exception Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            return {"status": "success", "result": result}
        

    @staticmethod
    async def param_dashboard_ssh(server_ip: str = Query(...), team: str = Query(...), username: str = Query(...), private_key: str = Query(...)):
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        outputCPU = 0
        outputRAM = 0
        outputSite = 0
        SERVER_IP = server_ip
        TEAM = team
        USERNAME = username
        
        LOCAL_SCRIPT_PATH = "app/script/wptt-list-domain.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_wptt-list-domain.sh"

        LOCAL_SCRIPT_PATH_SERVER_INFO = "app/script/wptt-server-information.sh"
        REMOTE_SCRIPT_PATH_SERVER_INFO = "/tmp/remote_wptt-server-information.sh"
     
        try:
            connected_user = None  # Lưu user kết nối thành công
            connection_errors = []  # Lưu danh sách lỗi trong quá trình kết nối
           
            key_name = f"{TEAM}_{SERVER_IP}"
            private_key_content = private_key

            # Load private key content into paramiko.RSAKey
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))

            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh_client.connect(SERVER_IP, username=USERNAME, pkey=private_key)
                connected_user = USERNAME
                print(f"Connected successfully with username: {USERNAME}")
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
            # ssh_client.close()
            outputSite = await DashboardController.fetch_sites_from_api(server_ip, team)
            try:
                if output.strip():  
                    so_luong_website = int(output.strip()) 
                    outputSite = so_luong_website
                else: 
                    print(f"Error: {error.strip()}") 
                    result["fail"]["count"] += 1
                    result["fail"]["messages"].append("Missing so_luong_website in script output.")
            except ValueError:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append("Invalid format for so_luong_website.")


            sftp = ssh_client.open_sftp()
            sftp.put(LOCAL_SCRIPT_PATH_SERVER_INFO, REMOTE_SCRIPT_PATH_SERVER_INFO)
            sftp.chmod(REMOTE_SCRIPT_PATH_SERVER_INFO, 0o755)
            sftp.close()
        
            command = f"sudo bash {REMOTE_SCRIPT_PATH_SERVER_INFO}"
            stdin, stdout, stderr = ssh_client.exec_command(command)


            output_lines = stdout.read().decode().split("\n")
            error = stderr.read().decode()
            ssh_client.close()
            outputCPU = 0
            try:
                if len(output_lines) >= 2:
                    cpu_count = output_lines[0]
                    ram_total = output_lines[1]
                    outputCPU = int(cpu_count.strip())
                    outputRAM = int(ram_total.strip()) * 1024 
                else: 
                    result["fail"]["count"] += 1
                    result["fail"]["messages"].append("Missing server info in script output.")
            except ValueError:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append("Invalid format for server info.")

            return {
                "status": "success",
                "result": result,
                "data": {
                    "cpu": outputCPU,
                    "ram": outputRAM,
                    "site": outputSite,
                },
            }
        
        except Exception as e:
            print(f"Exception Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            return {"status": "success", "result": result}

