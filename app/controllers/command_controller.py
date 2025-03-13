import paramiko
import io
from fastapi import Query
import requests
import paramiko
import os
import io
from app.models.command_request import CommandRequest
import asyncio


SSH_TEAM=os.getenv('SSH_TEAM')
api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}
timeout = int(os.getenv('TIMEOUD', 60 * 2))
class CommandController:
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
    async def exec_commands(request: CommandRequest):
        server_ip = request.server_ip
        team = request.team
        command = request.command

        result = {"status": False, "messages": ''}
        username = ["ubuntu", "ec2-user"]
        private_key = None
        connected_user = None
        try:
            key_name = f"{team}_{server_ip}"
            if SSH_TEAM and team in SSH_TEAM:
                username = await CommandController.fetch_username_from_api(key_name)
                connected_user = username
            private_key = await CommandController.fetch_private_key_from_api(key_name)
            # Attempt to connect to the server
            ssh_client = None
            if connected_user:
                ssh_client = await CommandController.connect_to_server(server_ip, username, private_key)
            else:
                # Thử kết nối với từng user
                for element in username:
                    try:
                        ssh_client = await CommandController.connect_to_server(server_ip, element, private_key)
                        if ssh_client:
                            connected_user = element
                            print(f"Successfully connected with {element}")
                            break
                    except paramiko.AuthenticationException:
                        print(f"Authentication failed for username: {element}")
                        continue
                    except Exception as e:
                        print(f"Error connecting with username {element}: {str(e)}")
                        continue

            if not ssh_client:
                result["status"] = False
                result["messages"] = f"{server_ip} - All attempts to connect failed"
                return result
            try:
                # Execute the command and check success
                output, error, success = await asyncio.wait_for(
                    CommandController.execute_command(ssh_client, command), timeout=timeout  # Timeout in seconds
                )

                # If the command failed, raise an error with the output
                if not success:
                    result["status"] = False
                    result["messages"] = f"{server_ip} - Command failed: {error}"
                    return result

                result["status"] = True
                result["messages"] = f"{server_ip} - Command run successfully"
                if output:
                    result["messages"] = f"{server_ip} - {output}"
                return result
            except asyncio.TimeoutError:
                result["status"] = True
                result["messages"] = f"{server_ip} - Command is running. But session was timed out after {timeout} seconds"
                return result
            finally:
                # Ensure the SSH connection is closed
                if ssh_client:
                    ssh_client.close()
        except Exception as e:
            result["status"] = False
            result["messages"] = f"{server_ip} - Failed: {str(e)}"
            return result
        finally:
            # Ensure the SSH connection is closed
            if ssh_client:
                ssh_client.close()

    @staticmethod
    async def connect_to_server(server_ip: str, username: str, private_key_content: str):
        """Connect to the server using SSH."""
        try:
            private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(server_ip, username=username, pkey=private_key)
            print(f"{server_ip} - Connected successfully with username: {username}")
            return ssh_client
        except paramiko.AuthenticationException:
            print(f"Authentication failed for username: {username}")
        except Exception as e:
            print(f"Error connecting to server {server_ip}: {str(e)}")
        return None

    # @staticmethod
    # async def execute_command(ssh_client, command: str):
    #     """Execute a command on the remote server and capture the output."""
    #     stdin, stdout, stderr = ssh_client.exec_command(command)

    #     # Read the output and error
    #     output = stdout.read().decode()
    #     error = stderr.read().decode()

    #     # Check if the command executed successfully by examining stderr
    #     if stderr.channel.recv_exit_status() != 0:
    #         # If exit status is not 0, the command failed
    #         success = False
    #     else:
    #         # Otherwise, the command was successful
    #         success = True

    #     return output, error, success
    
    @staticmethod
    async def execute_command(ssh_client, command: str):
        """Execute a command on the remote server and capture the output."""
        # Offload the blocking command execution to a separate thread
        output, error, success = await asyncio.to_thread(CommandController._exec_command, ssh_client, command)
        return output, error, success

    @staticmethod
    def _exec_command(ssh_client, command: str):
        """This is a blocking function to execute the command."""
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Read the output and error
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Check if the command executed successfully by examining stderr
        if stderr.channel.recv_exit_status() != 0:
            # If exit status is not 0, the command failed
            success = False
        else:
            # Otherwise, the command was successful
            success = True

        return output, error, success
