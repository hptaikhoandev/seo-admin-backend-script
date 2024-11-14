from app.models.domain_request import DomainRequest
import requests
import random
import time

api_token = 'fjtVVMq3P--nYpUJ2kNs9Gq-i4_R5yWd-tC1kXLs'
# api_token = 'Ih9Y3wmkGYvXXgOeVJ-h_DWTl7998POqqK9ijBb5'
admin_accounts = [
    {"team": "seo-3", "account_id": "e1c1a8d5af36e261554feeb763bfa9ca", "email": "ting@darasa.io"},
        # {"team": "seo-3", "account_id": "3b982bfb6af524090fb397e022006c1e", "email": "roylevn215@gmail.com"},

    # Other admin accounts here...
]

add_domain_url = 'https://api.cloudflare.com/client/v4/zones'
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

items_db = []

class DomainController:
    @staticmethod
    def clean_url(url):
        if url.startswith('https://'):
            url = url[8:]
        if url.startswith('http://'):
            url = url[7:]
        return url.rstrip('/')

    @staticmethod
    async def add_domains(request: DomainRequest):
        resultMessage = {"success": 0, "fail": 0}
        results = []
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
            
            max_retries = 2  # Số lần thử tối đa
            retry_count = 0
            while retry_count < max_retries:
                domain_response = requests.post(add_domain_url, headers=headers, json=domain_data)
                domain_result = domain_response.json()
                
                if domain_result.get('success'):
                    # Thành công, tiếp tục luồng chính
                    break
                else:
                    print(f"domain_result===> {domain_result}")
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        print(f"Retrying... Attempt {retry_count + 1} after 30 seconds")
                        time.sleep(30)  # Chờ 30 giây trước khi thử lại
                
            # Nếu không thành công sau 3 lần thử
            if not domain_result.get('success'):
                resultMessage["fail"] += 1
                continue  # Bỏ qua vòng lặp này và tiếp tục với domain tiếp theo

            # Luồng chính sau khi domain được thêm thành công
            zone_id = domain_result['result']['id']
            name_servers = domain_result['result']['name_servers']
            
            # Step 2: Remove Existing DNS Records
            dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            dns_list_response = requests.get(dns_record_url, headers=headers)
            dns_list_result = dns_list_response.json()

            if dns_list_result.get('success'):
                for record in dns_list_result['result']:
                    delete_url = f"{dns_record_url}/{record['id']}"
                    requests.delete(delete_url, headers=headers)

            # Step 3: Add A Record for root domain
            dns_record_data = {
                "type": "A",
                "name": domain,
                "content": request.server_ip,
                "ttl": 120,
                "proxied": True
            }
            dns_response = requests.post(dns_record_url, headers=headers, json=dns_record_data)
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
            cname_response = requests.post(dns_record_url, headers=headers, json=cname_record_data)
            if not cname_response.json().get('success'):
                print(f"cname_response===> {cname_response.json()}")
                continue

            # Step 5: Enable SSL
            ssl_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl'
            ssl_data = {"value": request.ssl_type}
            requests.patch(ssl_url, headers=headers, json=ssl_data)

            # Always Use HTTPS
            always_use_https_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/always_use_https'
            always_use_https_data = {"value": "on"}
            requests.patch(always_use_https_url, headers=headers, json=always_use_https_data)

            # Add to results
            resultMessage["success"] += 1
            results.append({'domain': domain, 'ns': ",".join(name_servers)})

        return {"status": "success", "results": results, "resultMessage": resultMessage}
