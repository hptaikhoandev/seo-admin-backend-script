from app.models.redirect_request import RedirectRequest
from fastapi import HTTPException
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

class RedirectController:
    @staticmethod
    def get_zone_id(domain):
        url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
        response = requests.get(url, headers=headers)
        result = response.json()
        if response.status_code == 200 and result['success']:
            return result['result'][0]['id']
        else:
            print(f"Failed to get zone ID for {domain}: {result.get('errors', 'Unknown error')}")
            return None
    @staticmethod
    def create_redirect(request: RedirectRequest):
        status_code = 301  # Redirect status code

        # For each target domain, get the Cloudflare zone ID and create redirect rules
        for domain in request.domain_to:
            zone_id = RedirectController.get_zone_id(domain)
            if not zone_id:
                raise HTTPException(status_code=400, detail=f"Zone ID not found for domain {domain}")

            # Cloudflare API endpoint to list Page Rules
            list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
            
            # Retrieve and delete any existing Page Rules
            response = requests.get(list_url, headers=headers)
            if response.status_code == 200:
                existing_rules = response.json().get('result', [])
                for rule in existing_rules:
                    rule_id = rule['id']
                    delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules/{rule_id}"
                    requests.delete(delete_url, headers=headers)

            # Define the base Page Rule URL for creation
            create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
            
            # Create Page Rule for non-www domain
            rule_data = {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://{domain}/*"
                        }
                    }
                ],
                "actions": [
                    {
                        "id": "forwarding_url",
                        "value": {
                            "url": f"https://{request.domain_from}/{request.redirect_type}",
                            "status_code": status_code
                        }
                    }
                ],
                "priority": 1,
                "status": "active"
            }
            
            create_response = requests.post(create_url, headers=headers, json=rule_data)
            if create_response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to create Page Rule for {domain}: {create_response.text}")
            
            # Create Page Rule for www. subdomain
            rule_www_data = {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://www.{domain}/*"
                        }
                    }
                ],
                "actions": [
                    {
                        "id": "forwarding_url",
                        "value": {
                            "url": f"https://{request.domain_from}/{request.redirect_type}",
                            "status_code": status_code
                        }
                    }
                ],
                "priority": 1,
                "status": "active"
            }

            create_www_response = requests.post(create_url, headers=headers, json=rule_www_data)
            if create_www_response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Failed to create Page Rule for www.{domain}: {create_www_response.text}")

        return {"status": "success", "message": f"Page Rules created successfully for {len(request.domain_to)} domains"}
    