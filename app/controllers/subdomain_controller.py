from app.models.subdomain_request import SubDomainRequest
from app.models.subdomainHistory_request import SubDomaiHistoryRequest
from dotenv import load_dotenv
import os
import requests
import random
import time

# Xóa cache của biến môi trường
os.environ.clear()
# Tải biến môi trường từ file .env
load_dotenv()
api_token_cf = os.getenv('API_TOKEN_CF')
url_cf = os.getenv('URL_DOMAIN_CF')
headers_cf = {
    'Authorization': f'Bearer {api_token_cf}',
    'Content-Type': 'application/json'
}
api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/accountIds"
url_backend_subdomainHistory = f"{os.getenv('URL_DOMAIN_BACKEND')}/subdomain-history"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}

class SubDomainController:
    @staticmethod
    def get_zone_id(domain):
        url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
        response = requests.get(url, headers=headers_backend)
        result = response.json()

        if response.status_code == 200 and result['success']:
            if result['result']:  # Kiểm tra nếu danh sách không rỗng
                return result['result'][0]['id']
            else:
                print(f"No zone ID found for {domain}")
                return None
        else:
            print(f"Failed to get zone ID for {domain}: {result.get('errors', 'Unknown error')}")
            return None
    
    @staticmethod
    def clean_url(url):
        # Remove 'https://' from the start
        if url.startswith('https://'):
            url = url[8:]  # Remove the first 8 characters
        if url.startswith('http://'):
            url = url[7:]  # Remove the first 8 characters
        # Remove trailing slashes
        url = url.rstrip('/')

        return url
     
    @staticmethod
    async def fetch_accounts_from_api(team: str):
        if team == 'admin':
            team = ''
        params = {
            "page": 1,
            "limit": 10000,
            "search": team,
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
        accounts = data.get("data", []) 
        # Trả về danh sách account
        return accounts
    
    async def get_dns_records(server_ip_list, page, per_page):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        url_zones = "https://api.cloudflare.com/client/v4/zones"
        results = []
        server_ip_list = server_ip_list
        # Fetch accounts from API
        total_page = 0
        try:
            params = {"page": page, "per_page": per_page}
            response = requests.get(url_zones, headers=headers_cf, params=params)
            
            zone_list_result = response.json()
            if zone_list_result.get('success'):
                for zone in zone_list_result['result']:
                    zone_id = zone["id"]

                    # Step 2: Remove Existing DNS Records
                    dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
                    dns_list_response = requests.get(dns_record_url, headers=headers_cf)
                    dns_list_result = dns_list_response.json()
                   
                    if dns_list_result.get('success'):
                        
                        for record in dns_list_result['result']:
                            # delete_url = f"{dns_record_url}/{record['id']}"
                            # requests.delete(delete_url, headers=headers_cf)
                            type_recode = record["type"]
                            if type_recode in ["A", "CNAME"]:
                                # Add to results
                                resultMessage["success"]["count"] += 1
                                resultMessage["success"]["messages"].append(f"{zone_id}: created domain in CloudFlare successfully")
                                record["account_id"] = zone["account"]["id"]
                                record["zone_id"] = zone_id
                                record["dns_id"] = record["id"]
                                record['domain'] = zone["name"]
                                results.append(record)
            total_page = zone_list_result["result_info"]["total_pages"]
        except Exception as e:
            print("error get_dns_records")
        return {"status": "success", "results": results, "page": page, "total_page": total_page, "resultMessage": resultMessage}
    

    async def get_ns_dns_records(search, page, limit, team):
       
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        domain_list_split = [domain.strip() for domain in search.split(",")]
       
        results = []
        admin_accounts = await SubDomainController.fetch_accounts_from_api(team)
        
        accounts = []
        if team == 'admin':
            accounts = [account['account_id'] for account in admin_accounts]
        else:
            accounts = [account['account_id'] for account in admin_accounts if account["team"] == team]
    
        for domain in domain_list_split:
            url_zones = "https://api.cloudflare.com/client/v4/zones"
         
            page = 1
            while True:
                params = {"page": page, "per_page": 50, "name": str(domain)}
                response = requests.get(url_zones, headers=headers_cf, params=params)
                
                zone_list_result = response.json()
                if zone_list_result.get('success'):
                    for zone in zone_list_result['result']:
                        account_id = zone["account"]["id"]
                        if account_id not in accounts:
                            continue
                        team_name = next((item['team'] for item in admin_accounts if item['account_id'] == account_id), None)
                        zone_id = zone["id"]
                        name_servers_str = ", ".join(zone["name_servers"]) if zone.get("name_servers") else None
                        ns_record = {}
                        ns_record['id'] = zone_id
                        ns_record['domain'] = zone["name"]
                        ns_record['name'] = name_servers_str
                        ns_record['type'] = 'NS'
                        ns_record['content'] = name_servers_str
                        ns_record['proxiable'] = False
                        ns_record['proxied'] = False
                        ns_record['ttl'] = 0
                        ns_record['created_on'] = zone["created_on"]
                        ns_record['modified_on'] = zone["modified_on"]
                        ns_record["account_id"] = account_id
                        ns_record["zone_id"] = zone_id
                        ns_record["team"] = team_name

                        results.append(ns_record)
                    
                # Check if there are more pages
                if page >= zone_list_result["result_info"]["total_pages"]:
                    break

                page += 1  # Move to the next page

        return {"status": "success", "data": results, "resultMessage": resultMessage, "total": len(results), "page": page, "limit": limit}

    async def update_dns_records(request: SubDomainRequest):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        results = []
        try:
            # id = request.id
            dns_id = request.dns_id
            zone_id = request.zone_id
            name = request.name
            content = request.content
            account_id = request.account_id
            # type = request.type
            # team = request.team

            url_zones = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_id}'
        
            rule_data = {"content": content}
        
            update_response = requests.patch(url_zones, headers=headers_cf, json=rule_data)

            # if update_response.status_code == 200:
            #     await SubDomainController.add_subdomainHistory(
            #         {
            #             "dns_id": dns_id,
            #             "zone_id" : zone_id,
            #             "type" : type,
            #             "name" : name,
            #             "content" : content,
            #             "account_id" : account_id,
            #             "team" : team
            #         }
            #     )

            resultMessage["success"]["count"] += 1
            resultMessage["success"]["messages"].append(f"{name}: updated in CloudFlare successfully")
            results.append({'name': name, 'content': content})
        except Exception as e:
            resultMessage["fail"]["count"] += 1
            resultMessage["fail"]["messages"].append(f"{name}: updated in CloudFlare failed")
            results.append({'name': '', 'content': ''})
            print("error get_dns_records")

        return {"status": "success", "data": results, "resultMessage": resultMessage}

    async def get_dns_records_by_name(search, team):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        results = []
        admin_accounts = await SubDomainController.fetch_accounts_from_api(team)
        accounts = []
        if team == 'admin':
            accounts = [account['account_id'] for account in admin_accounts]
        else:
            accounts = [account['account_id'] for account in admin_accounts if account["team"] == team]
        
        try:
            url_zones = f'https://api.cloudflare.com/client/v4/zones?name={SubDomainController.clean_url(search)}'
            response = requests.get(url_zones, headers=headers_cf)
            zone_list_result = response.json()
            
            if zone_list_result.get('success'):
                for zone in zone_list_result['result']:
                    zone_id = zone["id"]
                    if(zone["account"]["id"] not in accounts):
                        continue
                    
                    dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
                    dns_list_response = requests.get(dns_record_url, headers=headers_cf)
                    dns_list_result = dns_list_response.json()
                    
                    if dns_list_result.get('success'):
                        # Get latest DNS records from db
                        old_dns_records_request = requests.get(url_backend_subdomainHistory + '/last-subdomain', 
                                                            headers=headers_backend, 
                                                            params={"page": 1, "limit": 10, "search": search, 
                                                                    "sortBy": "account_id", "sortDesc": "false", "team": team})
                        old_dns_records = old_dns_records_request.json()
                        
                        for record in dns_list_result['result']:
                            if(record["type"] in ["A", "CNAME"]):
                                # Check if the record already exists in the database
                                record_exists = False
                                content_changed = False
                                old_record_match = None
                                
                                for old_record in old_dns_records['data']:
                                    if old_record['dns_id'] == record['id']:
                                        record_exists = True
                                        old_record_match = old_record
                                        # Kiểm tra nếu content đã thay đổi
                                        if old_record['content'] != record['content']:
                                            content_changed = True
                                        break
                                
                                # Nếu record chưa tồn tại hoặc đã tồn tại nhưng nội dung đã thay đổi
                                if not record_exists or (record_exists and content_changed):
                                    rule_data = {
                                        "dns_id": record["id"],
                                        "zone_id": zone_id,
                                        "name": record["name"],
                                        "type": record["type"],
                                        "content": record["content"],
                                        "account_id": zone["account"]["id"],
                                        "team": team
                                    }
                                    
                                    update_response = requests.post(url_backend_subdomainHistory, headers=headers_backend, json=rule_data)
                                    print("update_response", update_response.json())
                                    
                                    # Thêm thông báo phù hợp vào resultMessage
                                    if not record_exists:
                                        resultMessage["success"]["messages"].append(f"{zone_id}: created new domain in CloudFlare successfully")
                                    else:
                                        resultMessage["success"]["messages"].append(f"{zone_id}: updated domain content in CloudFlare successfully")
                                
                                # Add to results
                                resultMessage["success"]["count"] += 1
                                record["team"] = team
                                record["account_id"] = zone["account"]["id"]
                                record["zone_id"] = zone_id
                                record["dns_id"] = record["id"]
                                record['domain'] = zone["name"]
                                results.append(record)
        
        except Exception as e:
            print("error get_dns_records_by_name", e)
        
        return {"status": "success", "data": results, "resultMessage": resultMessage, "limit": 10, "page": 1, "total": len(results)}
    
    async def add_subdomainHistory(request: SubDomaiHistoryRequest):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        results = []
        try:
            dns_id = request.dns_id
            zone_id = request.zone_id
            type = request.type
            name = request.name
            content = request.content
            account_id = request.account_id
            team = request.team

            url_zones_info = f'https://api.cloudflare.com/client/v4/zones?name={SubDomainController.clean_url(name)}'
            response = requests.get(url_zones_info, headers=headers_cf)
            print("Domain_info: ", response.json())
        
            # url_zones = f'{url_backend_subdomainHistory}'
        
            rule_data = {
                "dns_id": dns_id,
                "zone_id": zone_id,
                "name": name,
                "type": type,
                "content": content,
                "account_id": account_id,
                "team": team
            }
        
            update_response = requests.post(url_backend_subdomainHistory, headers=headers_backend, json=rule_data)
            print("update_response", update_response.json())
           
            resultMessage["success"]["count"] += 1
            resultMessage["success"]["messages"].append(f"{name}: added in CloudFlare successfully")
            results.append({'name': name, 'content': content})
        except Exception as e:
            resultMessage["fail"]["count"] += 1
            resultMessage["fail"]["messages"].append(f"{name}: added in CloudFlare failed")
            results.append({'name': '', 'content': ''})
            print("error add_subdomainHistory", e)

        return {"status": "success", "data": results, "resultMessage": resultMessage}
