from app.models.clonesite_request import ClonesiteRequest
from fastapi import HTTPException
import requests
import random
import time
import paramiko
import os

api_token = 'Ih9Y3wmkGYvXXgOeVJ-h_DWTl7998POqqK9ijBb5'
admin_accounts = [
    {"team": "seo-3", "account_id": "3b982bfb6af524090fb397e022006c1e", "email": "roylevn215@gmail.com"},
    # Other admin accounts here...
]

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

items_db = []

class ClonesiteController:
    @staticmethod
    async def clone_site(request: ClonesiteRequest):
        # Cấu hình thông tin server
        SERVER_IP = request.server_ip
        USERNAME = "ubuntu"  # Thay bằng tên đăng nhập SSH của bạn
        LOCAL_SCRIPT_PATH = "app/script/wptt-sao-chep-website.sh"  # Đường dẫn script cục bộ
        REMOTE_SCRIPT_PATH = "/tmp/remote_wptt-sao-chep-website.sh"
        result = {"success": 0, "fail": {"count": 0, "messages": []}}

        try:
            # Xác định đường dẫn đến file .pem dựa trên server IP
            pem_file_path = f"app/pem/{SERVER_IP}.pem"
            
            # Kiểm tra nếu file .pem không tồn tại
            if not os.path.exists(pem_file_path):
                raise FileNotFoundError(f"Key file {pem_file_path} not found.")
            
            # Khởi tạo SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Tải file .pem
            private_key = paramiko.RSAKey.from_private_key_file(pem_file_path)
            
            # Kết nối SSH
            ssh_client.connect(SERVER_IP, username=USERNAME, pkey=private_key)
            
            # Sử dụng SFTP để copy file lên server
            sftp = ssh_client.open_sftp()
            sftp.put(LOCAL_SCRIPT_PATH, REMOTE_SCRIPT_PATH)  # Copy file lên server
            sftp.chmod(REMOTE_SCRIPT_PATH, 0o755)  # Đặt quyền thực thi cho file
            sftp.close()

            # Lấy các giá trị từ request
            source_domain = request.source_domain
            target_domain = request.target_domain

            # Thực thi lệnh từ file script trên server với các tham số
            command = f"bash {REMOTE_SCRIPT_PATH} {source_domain} {target_domain}"
            stdin, stdout, stderr = ssh_client.exec_command(command)

            # Đọc kết quả
            output = stdout.read().decode()
            error = stderr.read().decode()

            # # Xóa script sau khi thực thi (nếu cần)
            # ssh_client.exec_command(f"rm -f {REMOTE_SCRIPT_PATH}")

            # Đóng kết nối SSH
            ssh_client.close()

            if error:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"{error}")
            else:
                result["success"]["count"] += 1

            return {"status": "success", "result": result}

        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(f"{str(e)}")
            return {"status": "success", "result": result}
