from app.models.domain_request import DomainRequest
from dotenv import load_dotenv
import os
import requests
import random
import time

# api_token = 'fjtVVMq3P--nYpUJ2kNs9Gq-i4_R5yWd-tC1kXLs' # ting
# api_token = 'Ih9Y3wmkGYvXXgOeVJ-h_DWTl7998POqqK9ijBb5' # roylevn215
# api_token = '-nlmFYjVx_SHBQf8rKdyzTdbX-Qw3zmTLmBs4HnP' # Digital01
# api_token = 'd5EbNK2YUYYzDCJIaM2OGdoGgjU3ZFylrcZeXN2y' # Digital03
# api_token = 'sFzfy7n9hm2gmXvTKwtAsyPPNW57eCAh6FAGu8GQ' # Seo-03
# admin_accounts = [
#     {"team": "seo-3", "account_id": "e1c1a8d5af36e261554feeb763bfa9ca", "email": "ting@darasa.io"}, # ting
#     # {"team": "seo-3", "account_id": "3b982bfb6af524090fb397e022006c1e", "email": "roylevn215@gmail.com"}, # roylevn215
#     # {"team": "seo-3", "account_id": "b1061b061ed92d71433390eaa116a3fa", "email": "digital01@rocketagency.media"}, # Digital01
#     # {"team": "seo-3", "account_id": "6f6a04e8b2bd38a81bda2fccdaf2a0ce", "email": "digital03@rocketagency.media"}, # Digital03

#     # Other admin accounts here...
#     # SEO3
#     # {"team": "seo-3", "account_id": "85c65ef8a51daa2dfec6809736d27ab3", "email": "Curiefronkg@mailinator.com"},
#     # {"team": "seo-3", "account_id": "e79457dd4769671653d954a621d30a3e", "email": "Doconcettinanz93580@mailinator.com"},
#     # {"team": "seo-3", "account_id": "163423c3e0ba14334f09dab49fd664da", "email": "Doconcettinanz@mailinator.com"},
#     # {"team": "seo-3", "account_id": "d0b602c2070202405c69948bff35c4e2", "email": "Gothamjetonniu@mailinator.com"},
#     # {"team": "seo-3", "account_id": "24537b7bb9e22907d07434b7ac52b6f9", "email": "Lwahidalwinas@mailinator.com"},
#     # {"team": "seo-3", "account_id": "7be5919afa6a9363902dca589a1d3b93", "email": "Maylonewiy44812@mailinator.com"},
#     # {"team": "seo-3", "account_id": "20f1d92785afa8c39879d96b34034713", "email": "Shekohonoda6@mailinator.com"},
#     # {"team": "seo-3", "account_id": "8176ef42cd35d552d5fd9d9988d44dcd", "email": "Soiferiyn241928@mailinator.com"},
#     # {"team": "seo-3", "account_id": "260776374b3d550e88f3fcc736436c57", "email": "Ziobrodobiej@mailinator.com"},
#     # {"team": "seo-3", "account_id": "5a4e5b8f40ab7d398666dd069fba89d5", "email": "H5@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "82bf11a73e85cb5f7f55d617396fbc54", "email": "H6@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "5842ade9627b800e8b1c8b65de2e7c1d", "email": "Hi1@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "f2e99fab7fde5de3f58bf76c54d1935f", "email": "Hi2@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "08230919d044e133202dcf147b3cae6a", "email": "Hi3@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "a859d4aea7df9d4ae90b17c429bb7ea4", "email": "Hi4@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "4ad89b579b12e1c1fd81ae28cb00078e", "email": "Hi@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "9362daa790150b31f72749dd06033b92", "email": "nickojl932961@hyperpush.net"},
#     # {"team": "seo-3", "account_id": "a004d199a57abf4f1fbc47293faba1db", "email": "Shroutvwg498373@hotmail.com"},
#     # {"team": "seo-3", "account_id": "4452c5c862d895fb12fdaf6b91994bf8", "email": "Crotherslws411062@hotmail.com"},
#     # {"team": "seo-3", "account_id": "b575544e6783294e97bfcecf31150225", "email": "olstenlhd984462@hotmail.com"},
#     # {"team": "seo-3", "account_id": "1c1cbdccec4c46bbea533fe45ea0b996", "email": "landaulgj533680@hotmail.com"}

# ]

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

class DomainController:
    @staticmethod
    def check_domain_exists(headers_cf, domain_name):
        url_check = "https://api.cloudflare.com/client/v4/zones"
        params = {
            "name": domain_name,
        }

        response = requests.get(url_check, headers=headers_cf, params=params)
        response_data = response.json()

        if response_data.get("success"):
            zones = response_data.get("result", [])
            if zones:
                print(f"Domain {domain_name} đã tồn tại trong Cloudflare.")
                return True
        return False    
    @staticmethod
    async def fetch_accounts_from_api(team: str):
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
    
    @staticmethod
    def clean_url(url):
        if url.startswith('https://'):
            url = url[8:]
        if url.startswith('http://'):
            url = url[7:]
        return url.rstrip('/')

    @staticmethod
    async def add_domains(request: DomainRequest):
        resultMessage = {"success": {"count": 0, "messages": []}, "fail": {"count": 0, "messages": []}} 
        results = []
        # Fetch accounts from API
        admin_accounts = await DomainController.fetch_accounts_from_api(request.team)
        if not admin_accounts:
            resultMessage["fail"]["count"] += 1
            resultMessage["fail"]["messages"].append("No accounts found for the specified team.")
            return {"status": "error", "result": resultMessage}
        for domain in request.domains:
            domain = DomainController.clean_url(domain)
            account = random.choice([account for account in admin_accounts if account["team"] == request.team])
            account_id = account['account_id']
            
            # Step 1: Add Domain
            domain_data = {
                "name": domain,
                "account": {"id": account_id},
                "jump_start": True
            }
            
            domain_result = {"success": False}
            if DomainController.check_domain_exists(headers_cf, domain_name=domain_data["name"]):
                print(f"Domain {domain_data['name']} đã tồn tại. Bỏ qua việc tạo.")
                resultMessage["fail"]["count"] += 1
                resultMessage["fail"]["messages"].append(f"{domain_data['name']} always exists.")
                continue  # Bỏ qua vòng lặp này và tiếp tục với domain tiếp theo
            domain_response = requests.post(url_cf, headers=headers_cf, json=domain_data)
            domain_result = domain_response.json()
                
            # Nếu không thành công sau các lần thử
            if not domain_result.get('success'):
                resultMessage["fail"]["count"] += 1
                fail_message = domain_result.get("errors", [{"message": "Unknown error"}])[0].get("message")
                resultMessage["fail"]["messages"].append(f"{domain}: {fail_message}")
                continue  # Bỏ qua vòng lặp này và tiếp tục với domain tiếp theo

            # Luồng chính sau khi domain được thêm thành công
            zone_id = domain_result['result']['id']
            name_servers = domain_result['result']['name_servers']
            
            # Step 2: Remove Existing DNS Records
            dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            dns_list_response = requests.get(dns_record_url, headers=headers_cf)
            dns_list_result = dns_list_response.json()

            if dns_list_result.get('success'):
                for record in dns_list_result['result']:
                    delete_url = f"{dns_record_url}/{record['id']}"
                    requests.delete(delete_url, headers=headers_cf)

            # Step 3: Add A Record for root domain
            dns_record_data = {
                "type": "A",
                "name": domain,
                "content": request.server_ip,
                "ttl": 120,
                "proxied": True
            }
            dns_response = requests.post(dns_record_url, headers=headers_cf, json=dns_record_data)
            if not dns_response.json().get('success'):
                print(f"dns_response===> {dns_response.json()}")
                continue

            # Step 4: Add CNAME Record for www
            cname_record_data = {
                "type": "CNAME",
                "name": "www",
                "content": domain,
                "ttl": 120,
                "proxied": True
            }
            cname_response = requests.post(dns_record_url, headers=headers_cf, json=cname_record_data)
            if not cname_response.json().get('success'):
                print(f"cname_response===> {cname_response.json()}")
                continue

            # Step 5: Enable SSL
            ssl_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl'
            ssl_data = {"value": request.ssl_type}
            requests.patch(ssl_url, headers=headers_cf, json=ssl_data)

            # Always Use HTTPS
            always_use_https_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/always_use_https'
            always_use_https_data = {"value": "on"}
            requests.patch(always_use_https_url, headers=headers_cf, json=always_use_https_data)

            # Add to results
            resultMessage["success"]["count"] += 1
            resultMessage["success"]["messages"].append(f"{domain}: created domain in CloudFlare successfully")
            results.append({'domain': domain, 'ns': ",".join(name_servers)})

        return {"status": "success", "results": results, "resultMessage": resultMessage}

