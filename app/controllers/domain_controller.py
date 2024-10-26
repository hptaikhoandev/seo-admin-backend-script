from app.models.domain_request import DomainRequest
import requests
import random

api_token = 'fjtVVMq3P--nYpUJ2kNs9Gq-i4_R5yWd-tC1kXLs'
admin_accounts = [
    {"team": "seo-3", "account_id": "e1c1a8d5af36e261554feeb763bfa9ca", "email": "ting@darasa.io"},
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
            domain_response = requests.post(add_domain_url, headers=headers, json=domain_data)
            domain_result = domain_response.json()
            
            if not domain_result.get('success'):
                continue

            zone_id = domain_result['result']['id']
            name_servers = domain_result['result']['name_servers']
            # Step 2: Remove Existing DNS Records
            dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            dns_list_response = requests.get(dns_record_url, headers=headers)
            dns_list_result = dns_list_response.json()

            if dns_list_result.get('success'):
                for record in dns_list_result['result']:
                    delete_url = f"{dns_record_url}/{record['id']}"
                    delete_response = requests.delete(delete_url, headers=headers)

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
                continue

            # Step 5: Enable SSL
            if request.ssl_type == "flexible":
                ssl_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl'
                ssl_data = {"value": request.ssl_type}
                requests.patch(ssl_url, headers=headers, json=ssl_data)

            # Always Use HTTPS
            always_use_https_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/always_use_https'
            always_use_https_data = {"value": "on"}
            requests.patch(always_use_https_url, headers=headers, json=always_use_https_data)
            # Add to results
            results.append({'domain': domain, 'ns': ",".join(name_servers)})

        return {"message": "Domains processed successfully", "results": results}

    