from app.models.redirect_request import RedirectRequest
from fastapi import HTTPException
import requests
import random

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

class RedirectController:
    @staticmethod
    def get_zone_id(domain):
        url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
        response = requests.get(url, headers=headers)
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
    async def create_redirect(request: RedirectRequest):
        result = {"success": 0, "fail": 0}
        # Kiểm tra nếu số lượng phần tử của source_domains và target_domains không bằng nhau
        if len(request.source_domains) != len(request.target_domains):
            return {"status": "fail", "message": "Số phần tử của 2 dãy domain nhập vào không giống nhau"}

        status_code = 301  # Redirect status code

        # Tạo một dictionary để ánh xạ các trường hợp tương tự như switch-case
        redirect_options = {
            'Wildcard Redirect': {'path': '$1', 'id': 'forwarding_url'},
            'Homepage Redirect': {'path': '', 'id': 'forwarding_url'}
        }

        # Lấy giá trị từ dictionary hoặc gán giá trị mặc định nếu không có trường hợp nào khớp
        option = redirect_options.get(request.redirect_type, {'path': '', 'id': ''})

        # Gán các giá trị từ option vào path và id
        path = option['path']
        id = option['id']

        for index, domain in enumerate(request.source_domains):
            zone_id = RedirectController.get_zone_id(domain)
            if not zone_id:
                result["fail"] += 1
                continue
            # Cloudflare API endpoint to get Page Rules
            list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
            
            # Get existing Page Rules
            response = requests.get(list_url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to retrieve Page Rules for {domain}: {response.text}")
                continue
            
            existing_rules = response.json().get('result', [])

            # Delete all existing Page Rules
            if not existing_rules:
                print(f"No Page Rules found for {domain}")
            else:
                for rule in existing_rules:
                    rule_id = rule['id']
                    delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules/{rule_id}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    if delete_response.status_code == 200:
                        print(f"Deleted Page Rule with ID {rule_id} for {domain}")
                    else:
                        print(f"Failed to delete Page Rule {rule_id} for {domain}: {delete_response.text}")
            
            # Cloudflare API endpoint to create a Page Rule
            create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
            # Data for the Page Rule
            print(f"yyyy {id}")

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
                        "id": id,
                        "value": {
                            "url": f"https://{request.target_domains[index]}/{path}",
                            "status_code": status_code
                        }
                    }
                ],
                "priority": 1,
                "status": "active"
            }

            # Make the request to create the Page Rule for non-www domain
            create_response = requests.post(create_url, headers=headers, json=rule_data)
            
            if create_response.status_code == 200:
                print(f"Page Rule created for domain {domain}")
                
                # Rule for www. domain
                rule_www = {
                    "targets": [
                        {
                            "target": "url",
                            "constraint": {
                                "operator": "matches",
                                "value": f"www.{domain}/*"
                            }
                        }
                    ],
                    "actions": [
                        {
                            "id": id,
                            "value": {
                                "url": f"https://{request.target_domains[index]}/{path}",
                                "status_code": status_code
                            }
                        }
                    ],
                    "priority": 1,
                    "status": "active"
                }
                
                # Make the request to create the Page Rule for www. domain
                create_www_response = requests.post(create_url, headers=headers, json=rule_www)
                if create_www_response.status_code == 200:
                    result["success"] += 1
                    print(f"Page Rule created for domain www.{domain}")
                else:
                    print(f"Failed to create Page Rule for www.{domain}: {create_www_response.text}")
            else:
                print(f"Failed to create Page Rule for {domain}: {create_response.text}")
        
        return {"status": "success", "result": result}
    