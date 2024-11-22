from app.models.clonesite_request import ClonesiteRequest
from fastapi import HTTPException
import requests
import random
import time
import paramiko
import os

class ClonesiteController:
    @staticmethod
    async def clone_site(request: ClonesiteRequest):
        SERVER_IP = request.server_ip
        USERNAME = "ubuntu"
        LOCAL_SCRIPT_PATH = "app/script/wptt-sao-chep-website.sh"
        REMOTE_SCRIPT_PATH = "/tmp/remote_wptt-sao-chep-website.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}}

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

            source_domain = request.source_domain
            target_domain = request.target_domain
            command = f"sudo bash {REMOTE_SCRIPT_PATH} {source_domain} {target_domain}"
            stdin, stdout, stderr = ssh_client.exec_command(command)

            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh_client.close()

            if error.strip():
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(error.strip())
            else:
                result["success"] += 1

            return {"status": "success", "result": result}

        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            return {"status": "success", "result": result}

