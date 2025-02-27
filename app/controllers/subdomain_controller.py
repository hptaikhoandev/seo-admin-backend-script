from app.models.subdomain_request import SubDomainRequest
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
    async def get_dns_records(server_ip_list):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}}
        url_zones = "https://api.cloudflare.com/client/v4/zones"
        results = []
        server_ip_list = server_ip_list
        # Fetch accounts from API
        domain = None
        zone_list_response = requests.get(url_zones, headers=headers_cf)
        zone_list_result = zone_list_response.json()
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
                            resultMessage["success"]["messages"].append(f"{domain}: created domain in CloudFlare successfully")
                            record["account_id"] = zone["account"]["id"]
                            record["zone_id"] = record["id"]
                            results.append(record)

        return {"status": "success", "results": results, "resultMessage": resultMessage}

