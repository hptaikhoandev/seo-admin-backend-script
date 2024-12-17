from app.models.server_request import ServerRequest
from app.models.pem_request import PemRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError, WaiterError
from datetime import datetime
from fastapi import HTTPException
import requests
import random
import time
import boto3 
import json
from dotenv import load_dotenv
import os
from app.constants.constants import ec2_params

load_dotenv()
api_token_cf = os.getenv('API_TOKEN_CF')
AWS_ACCESS_KEY=os.getenv('AWS_ACCESS_KEY')
AWS_SECRET=os.getenv('AWS_SECRET')

class AdminController:
    @staticmethod
    def send_to_telegram(valuesGG):
        # Cấu hình Bot và Chat ID
        BOT_TOKEN = "7778868331:AAFW4Hp6eNtHsHE8O46VwxQpbL_2U-hkk5c"
        CHAT_ID = "-4705994114"

        # Định dạng dữ liệu từ valuesGG
        formatted_security_groups = "\n".join([f"--{sg}" for sg in valuesGG[0][12].split(", \n    --")])
        message = f"""
        *{valuesGG[0][3]} team vừa tạo một EC2 Server*
        **Instance Information:**
        - Date: {valuesGG[0][0]}
        - Region: {valuesGG[0][1]}
        - Instance Name: {valuesGG[0][2]}
        - Instance ID: {valuesGG[0][4]}
        - Elastic IP: {valuesGG[0][5]}
        - Private IP: {valuesGG[0][6]}
        - Instance Type: {valuesGG[0][7]}
        - CPU & RAM: {valuesGG[0][8]}
        - Status: {valuesGG[0][9]}
        - Disk Size: {valuesGG[0][10]}
        - Public IP: {valuesGG[0][11]}
        - Security Groups: 
            {formatted_security_groups}
        """

        # URL API Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        # Payload cho API Telegram
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"  # Để định dạng text
        }

        # Gửi yêu cầu POST tới Telegram
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            print("Thông tin đã được gửi tới nhóm Telegram thành công.")
        else:
            print(f"Lỗi khi gửi tin nhắn: {response.status_code}, {response.text}")
    @staticmethod
    def append_to_google_sheet(values):
        try:
            # Thông tin Google Sheets
            SPREADSHEET_ID = '1D0fw1ws_ov04IO0PNRV3CbgrH6AvWhIqXRKoTLFRpTM'
            SHEET_NAME = 'server'  # Thay bằng tên sheet

            # Load credentials từ file service account
            creds = Credentials.from_service_account_file(
                'app/key/seo-admin-442609-152c2f330723.json',
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            service = build('sheets', 'v4', credentials=creds)
            # Chuẩn bị dữ liệu để ghi vào sheet
            body = {'values': values}
            # Append dữ liệu vào Google Sheet
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()

        except HttpError as error:
            print(f"An error occurred: {error}")
    @staticmethod
    def check_keypair_exists(ec2_client, key_name):
        try:
            ec2_client.describe_key_pairs(KeyNames=[key_name])
            print(f"Key Pair '{key_name}' already exists.")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                print(f"Key Pair '{key_name}' does not exist.")
                return False
            else:
                raise e
    @staticmethod
    async def add_server_domains(request: ServerRequest):
        print(f"0===> Instance create process start")
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        current_date = datetime.now().strftime("'%d/%m/%Y")
        try:
            ec2_param = next((item for item in ec2_params if item["team"] == request.team), None)

            # Định nghĩa các tham số
            region_name = ec2_param["region"]
            subnet_id = ec2_param["subnet_id"]
            security_group_ids = ec2_param["security_group_id"]
            key_name = ec2_param["key_name"]
            instance_type = ec2_param["instance_type"]
            ami_id = ec2_param["ami_id"]
            instance_name = f"pro-seoadmin-{ec2_param['region']}-ec2-{ec2_param['team']}-{int(time.time())}"

            # Tạo instance param
            instance_params = {
                "ImageId": ami_id,
                "InstanceType": instance_type,
                "MinCount": 1,
                "MaxCount": 1,
                "KeyName": key_name,
                "NetworkInterfaces": [
                    {
                        "SubnetId": subnet_id,
                        "DeviceIndex": 0,
                        "AssociatePublicIpAddress": True,
                        "Groups": security_group_ids,
                    }
                ],
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/xvda",
                        "Ebs": {
                            "VolumeSize": 120,
                            "VolumeType": "gp3",
                            "DeleteOnTermination": True
                        }
                    }
                ],
                "TagSpecifications": [
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": instance_name},
                            {"Key": "CostCenter", "Value": request.team.upper()},
                            ]
                    }
                ]
            }

            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY, 
                aws_secret_access_key=AWS_SECRET, 
                region_name=region_name
            )

            # Bước 1: Tạo EC2 instance
            response = ec2_client.run_instances(**instance_params)

            instance = response['Instances'][0]
            instance_id = instance['InstanceId']

            print(f"1===> Instance created with ID: {instance_id}")

            # Chờ instance sẵn sàng
            ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
            print(f"2===> Instance with ID: {instance_id} is running.")
            # Tạo Elastic IP
            elastic_ip_response = ec2_client.allocate_address(Domain='vpc')
            elastic_ip = elastic_ip_response['PublicIp']
            allocation_id = elastic_ip_response['AllocationId']

            # Gán Elastic IP cho instance
            ec2_client.associate_address(InstanceId=instance_id, AllocationId=allocation_id)
            print(f"3===> Tạo và gán Elastic IP cho instance {instance_id} is success.")


            # Lấy thông tin chi tiết về instance và EBS volume
            instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
            volume_id = instance_details['BlockDeviceMappings'][0]['Ebs']['VolumeId']
            volume_details = ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
            disk_size = volume_details['Size']

            # Tạo đối tượng kết quả trả về
            resultObj = {
                "status": "success",
                "result": {
                    "instance_id": instance_id,
                    "instance_name": instance_name,
                    "region": region_name,
                    "elastic_ip": elastic_ip,
                    "private_ip_address": instance_details['PrivateIpAddress'],
                    "public_ip_address": instance_details.get('PublicIpAddress', "N/A"),
                    "instance_type": instance_details['InstanceType'],
                    "cpu_cores": instance_details['CpuOptions']['CoreCount'],
                    "threads_per_core": instance_details['CpuOptions']['ThreadsPerCore'],
                    "ram": "8 GiB",
                    "disk_size": f"{disk_size} GiB",
                    "security_groups": [sg['GroupName'] for sg in instance_details['SecurityGroups']],
                    "message": "EC2 instance created successfully."
                }
            }

            # In đối tượng result ra màn hình console
            print(f"4===> EC2 Instance Details: \n{json.dumps(resultObj, indent=4)}")

            # Chuẩn bị kết quả đưa qua Google sheet
            valuesGG = [
                [
                    current_date,
                    resultObj["result"]["region"],
                    resultObj["result"]["instance_name"],
                    request.team.upper(),
                    resultObj["result"]["instance_id"],
                    resultObj["result"]["elastic_ip"],
                    resultObj["result"]["private_ip_address"],
                    resultObj["result"]["instance_type"],
                    f'{resultObj["result"]["cpu_cores"]}CPU & 8Gib',
                    'running',
                    resultObj["result"]["disk_size"],
                    resultObj["result"]["public_ip_address"],
                    ",\n ".join(resultObj["result"]["security_groups"]),
                    'Not yet',
                ]
            ]

            AdminController.append_to_google_sheet(valuesGG)
            print("5===> Đã chuyển thông tin sang Google Sheet.")

            # Gọi hàm gửi tin nhắn
            AdminController.send_to_telegram(valuesGG)
            print("5===> Đã chuyển thông tin sang Telegram.")


            result["success"] += 1
            return {
                "status": "success",
                "result": result,
                "data": {
                    "key_name": key_name,
                    "public_ip": elastic_ip,
                },
            }
        
        except ClientError as e:
            print(f"1-AWS Client Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(f"AWS Client Error: {str(e)}") 
        except NoCredentialsError: 
            print(f"2-NoCredentialsError Error: {str(e)}")     
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("AWS credentials not found.")

        except PartialCredentialsError: 
            print(f"3-PartialCredentialsError Error: {str(e)}")   
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("Incomplete AWS credentials.")
        except Exception as e:
            print(f"4-Exception Error: {str(e)}")   
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
        except WaiterError as e:
            print(f"5-WaiterError Error: Instance {instance_id} did not enter 'running' state.")
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
        return {"status": "error", "result": result}
    
    @staticmethod
    async def add_pem_key(request: PemRequest):
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        try:
            # Lấy thông tin team từ request
            team_name = request.team
            if not team_name:
                raise ValueError("Team name is required")

            # Tạo tên keypair từ team name
            key_name = f"{team_name}"
            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY, 
                aws_secret_access_key=AWS_SECRET, 
                region_name='ap-northeast-1' 
            )
            print(f"KeyPair created successfully.")
            # Tạo Key Pair
            key_pair = ec2_client.create_key_pair(KeyName=key_name)
            # Lấy nội dung của private key
            private_key = key_pair.get('KeyMaterial')
            
            # Thêm thành công vào kết quả
            result["success"] += 1
            return {
                "status": "success",
                "result": result,
                "data": {
                    "KeyName": key_name,
                    "PrivateKey": private_key,
                },
            }
        
        except ClientError as e:
            # Kiểm tra nếu KeyPair đã tồn tại
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(str(e))
                print(f"1-AWS Client Error: {str(e)}") 
                return {"status": "error", "result": result}    

            else:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"AWS Client Error: {str(e)}") 
        except NoCredentialsError: 
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("AWS credentials not found.")
            print(f"2-AWS Client Error: {str(e)}")     

        except PartialCredentialsError: 
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("Incomplete AWS credentials.")
            print(f"3-AWS Client Error: {str(e)}")   
        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            print(f"4-AWS Client Error: {str(e)}")   

        return {"status": "error", "result": result}
    @staticmethod
    async def delete_pem_key(request: PemRequest):
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        try:
            # Lấy thông tin team từ request
            team_name = request.team
            if not team_name:
                raise ValueError("Team name is required")

            # Tạo tên keypair từ team name
            key_name = f"{team_name}_keypairs"

            # Khởi tạo EC2 client
            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET,
                region_name='ap-northeast-1'
            )

            # Xóa Key Pair
            ec2_client.delete_key_pair(KeyName=key_name)
            print(f"KeyPair '{key_name}' deleted successfully.")

            # Thêm thành công vào kết quả
            result["success"] += 1
            return {
                "status": "success",
                "result": result,
                "message": f"KeyPair '{key_name}' deleted successfully."
            }

        except ClientError as e:
            # Xử lý lỗi liên quan đến AWS
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'InvalidKeyPair.NotFound':
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"KeyPair '{key_name}' not found.")
                print(f"1-AWS Client Error: {str(e)}")
                return {"status": "error", "result": result}

            else:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"AWS Client Error: {str(e)}")
                print(f"2-AWS Client Error: {str(e)}")

        except NoCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("AWS credentials not found.")
            print(f"3-AWS Client Error: No AWS credentials found.")

        except PartialCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("Incomplete AWS credentials.")
            print(f"4-AWS Client Error: Incomplete AWS credentials.")

        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            print(f"5-Error: {str(e)}")

        return {"status": "error", "result": result}
    @staticmethod
    async def status_servers(request: ServerRequest):
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        try:
            ec2_param = next((item for item in ec2_params if item["team"] == request.team), None)
            # Định nghĩa các tham số
            region_name = ec2_param["region"]

            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY, 
                aws_secret_access_key=AWS_SECRET, 
                region_name=region_name
            )
            # Gọi API AWS để tìm instance theo public IP address
            response = ec2_client.describe_instances(
                Filters=[{'Name': 'ip-address', 'Values': [request.server_ip]}]
            )
            
            # Kiểm tra xem có instance nào được tìm thấy không
            reservations = response.get('Reservations', [])
            if not reservations or not reservations[0].get('Instances'):
                # Không tìm thấy instance nào tương ứng với IP
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"No instance found for IP: {request.server_ip}")
                return {
                    "status": "error",
                    "result": result,
                    "message": f"No instance associated with IP {request.server_ip}"
                }

            instance = reservations[0]['Instances'][0]
            instance_state = instance.get('State', {}).get('Name')

            # Trả về kết quả thành công
            result["success"] += 1
            return {
                "status": "success",
                "result": result,
                "data": {
                    "instance_state": instance_state,
                }
            }

        except ClientError as e:
            # Xử lý lỗi liên quan đến AWS
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'InvalidKeyPair.NotFound':
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"1-AWS Client Error: {str(e)}")
                print(f"1-AWS Client Error: {str(e)}")
                return {"status": "error", "result": result}

            else:
                result["fail"]["count"] += 1
                result["fail"]["messages"].append(f"AWS Client Error: {str(e)}")
                print(f"2-AWS Client Error: {str(e)}")

        except NoCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("AWS credentials not found.")
            print(f"3-AWS Client Error: No AWS credentials found.")

        except PartialCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("Incomplete AWS credentials.")
            print(f"4-AWS Client Error: Incomplete AWS credentials.")

        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            print(f"5-Error: {str(e)}")

        return {"status": "error", "result": result}
    
    @staticmethod
    async def transitions_server(request: ServerRequest):
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        try:
            # Tìm tham số EC2 theo team
            ec2_param = next((item for item in ec2_params if item["team"] == request.team), None)
            if not ec2_param:
                raise Exception(f"No EC2 parameters found for team {request.team}")

            region_name = ec2_param["region"]
            server_ip = request.server_ip
            transitions = request.transitions.lower()

            if transitions not in ["start", "restart", "stop"]:
                raise Exception(f"Invalid transition: {transitions}")

            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET,
                region_name=region_name
            )

            # Gọi API AWS để tìm instance theo public IP address
            response = ec2_client.describe_instances(
                Filters=[{'Name': 'ip-address', 'Values': [server_ip]}]
            )
            instances = response.get("Reservations", [])
            if not instances:
                raise Exception(f"No instances found with IP {server_ip}")

            instance_id = instances[0]["Instances"][0]["InstanceId"]

            if transitions == "stop":
                # Dừng instance
                stop_response = ec2_client.stop_instances(InstanceIds=[instance_id])

                # Chờ trạng thái chuyển sang "stopped"
                waiter = ec2_client.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[instance_id])
                instance_state = "stopped"

            elif transitions == "start":
                # Khởi động instance
                start_response = ec2_client.start_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter('instance_running')
                waiter.wait(InstanceIds=[instance_id])
                instance_state = "running"

            elif transitions == "restart":
                # Khởi động lại instance
                reboot_response = ec2_client.reboot_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter('instance_running')
                waiter.wait(InstanceIds=[instance_id])
                instance_state = "running"

            result["success"] += 1
            return {
                "status": "success",
                "result": result,
                "data": {
                    "instance_state": instance_state,
                }
            }

        except ClientError as e:
            # Xử lý lỗi liên quan đến AWS
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(f"AWS Client Error: {str(e)}")
            print(f"AWS Client Error: {str(e)}")

        except NoCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("AWS credentials not found.")
            print(f"AWS Client Error: No AWS credentials found.")

        except PartialCredentialsError:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append("Incomplete AWS credentials.")
            print(f"AWS Client Error: Incomplete AWS credentials.")

        except Exception as e:
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(str(e))
            print(f"Error: {str(e)}")

        return {"status": "error", "result": result}

    
