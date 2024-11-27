from app.models.server_request import ServerRequest
from app.models.pem_request import PemRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from datetime import datetime
from fastapi import HTTPException
import requests
import random
import time
import boto3 

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

class AdminController:
    @staticmethod
    def append_to_google_sheet(values):
        try:
            # Thông tin Google Sheets
            SPREADSHEET_ID = '1D0fw1ws_ov04IO0PNRV3CbgrH6AvWhIqXRKoTLFRpTM'  # Thay bằng ID của Google Sheet
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
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        current_date = datetime.now().strftime("'%d/%m/%Y")
        try:
            time.sleep(3)
            data_result = {
                "status": "success",
                "result": {
                    "instance_id": "i-0d7eae5958c702ed6",
                    "instance_name": "Eting_Testing_1732600915",
                    "region": "ap-northeast-1",
                    "elastic_ip": "43.206.47.57",
                    "private_ip_address": "172.31.7.247",
                    "public_ip_address": "54.250.71.110",
                    "instance_type": "t2.micro",
                    "cpu_cores": 1,
                    "threads_per_core": 1,
                    "ram": "1 GiB (t2.micro)",
                    "disk_size": "8 GiB",
                    "security_groups": [
                        "default"
                    ],
                    "message": "EC2 instance created successfully."
                }
            }
            valuesGG = [
                [
                    current_date,
                    data_result["result"]["region"],
                    data_result["result"]["instance_name"],
                    'seo3-wptt-05',
                    data_result["result"]["instance_id"],
                    data_result["result"]["elastic_ip"],
                    data_result["result"]["private_ip_address"],
                    data_result["result"]["instance_type"],
                    f'{data_result["result"]["cpu_cores"]}&{data_result["result"]["ram"]}',
                    'running',
                    data_result["result"]["disk_size"],
                    data_result["result"]["public_ip_address"],
                    ", ".join(data_result["result"]["security_groups"]),  # Chuyển đổi danh sách thành chuỗi
                    'Not yet',
                ]
            ]
            AdminController.append_to_google_sheet(valuesGG)


            ec2_client = boto3.client(
                'ec2',
                aws_access_key_id='', 
                aws_secret_access_key='', 
                region_name='ap-northeast-1' 
            )
            timestamp = int(time.time())
            instance_name = f"Eting_testing_{timestamp}"

            # Lấy KeyName từ request
            key_name = f"{request.team}_{timestamp}"
            if not key_name:
                raise ValueError("KeyName is required in the request.")
            # Kiểm tra KeyPair tồn tại
            if not AdminController.check_keypair_exists(ec2_client, key_name):
                # Nếu không tồn tại, tạo KeyPair mới
                key_pair = ec2_client.create_key_pair(KeyName=key_name)
                private_key_content = key_pair['KeyMaterial']

                # Lưu hoặc sử dụng private key (tùy trường hợp)
                print(f"New Key Pair created. Private Key:\n{private_key_content}")

            result["success"] += 1
            # result["fail"]["count"] += 1
            # result["fail"]["messages"].append("AWS bị lỗi gì đó")
            return {
                "status": "success",
                "result": result,
                "data": {
                    "key_name": key_name,
                    "private_key": private_key_content,
                    "public_ip": data_result["result"]["public_ip_address"],
                },
            }


            # # Tạo instance
            # instance_name = f"Eting_Testing_{int(time.time())}"
            # instance_params = {
            #     "ImageId": "ami-0ac6b9b2908f3e20d",  # AMI ID phù hợp
            #     "InstanceType": "t2.micro",
            #     "MinCount": 1,
            #     "MaxCount": 1,
            #     "KeyName": key_name,
            #     "TagSpecifications": [
            #         {
            #             "ResourceType": "instance",
            #             "Tags": [{"Key": "Name", "Value": instance_name}]
            #         }
            #     ]
            # }

            # response = ec2_client.run_instances(**instance_params)
            # instance = response['Instances'][0]
            # instance_id = instance['InstanceId']

            # # Chờ instance sẵn sàng
            # ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])

            # # Lấy thông tin chi tiết về instance
            # instance_details = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]

            # # Lấy thông tin EBS volume
            # volume_id = instance_details['BlockDeviceMappings'][0]['Ebs']['VolumeId']
            # volume_details = ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
            # disk_size = volume_details['Size']

            # # Gán Elastic IP
            # eip_allocation = ec2_client.allocate_address(Domain='vpc')
            # ec2_client.associate_address(InstanceId=instance_id, AllocationId=eip_allocation['AllocationId'])
            # elastic_ip = eip_allocation['PublicIp']


            # resultObj = {
            #     "status": "success",
            #     "result": {
            #         "instance_id": instance_id,
            #         "instance_name": instance_name,
            #         "region": "ap-northeast-1",
            #         "elastic_ip": elastic_ip,
            #         "private_ip_address": instance_details['PrivateIpAddress'],
            #         "public_ip_address": instance_details.get('PublicIpAddress', "N/A"),
            #         "instance_type": instance_details['InstanceType'],
            #         "cpu_cores": instance_details['CpuOptions']['CoreCount'],
            #         "threads_per_core": instance_details['CpuOptions']['ThreadsPerCore'],
            #         "ram": "1 GiB (t2.micro)",  # Tùy chỉnh theo loại instance
            #         "disk_size": f"{disk_size} GiB",
            #         "security_groups": [sg['GroupName'] for sg in instance_details['SecurityGroups']],
            #         "message": "EC2 instance created successfully."
            #     }
            # }

            # # In đối tượng result ra màn hình console
            # print("EC2 Instance Details:")
            # print(resultObj)

            # Trả về đối tượng result
            # return {"status": "success", "result": result, "data": data_result}
        

        except ClientError as e:
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
                aws_access_key_id='', 
                aws_secret_access_key='', 
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
                aws_access_key_id='',
                aws_secret_access_key='',
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
    
    