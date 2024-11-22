from app.models.multisite_request import MultisiteRequest
from fastapi import HTTPException
import requests
import random
import time
import paramiko
import os

class MultisiteController:
    @staticmethod
    async def multi_site(request: MultisiteRequest):
        SERVER_IP = request.server_ip
        USERNAME = "ubuntu"
        LOCAL_SCRIPT_PATH = "app/script/auto_add_multiple_wp_sites.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_auto_add_multiple_wp_sites.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}} 
        for domain in request.domains:
            try:
                pem_file_path = f"app/pem/{SERVER_IP}.pem"
                if not os.path.exists(pem_file_path):
                    raise FileNotFoundError(f"Key file {pem_file_path} not registry.")
                
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                private_key = paramiko.RSAKey.from_private_key_file(pem_file_path)
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
            except Exception as e:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"{domain}: {str(e)}")
        return {"status": "success", "result": result}

