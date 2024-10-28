import requests
import configparser

# Replace these with your actual values
api_token = 'bbSCt1OpOxh3-23IY4zg_cWUhsecFyuzuQMdQr_V'
# api_token = 'T86Ju94Mb9CUeMphdvn0Mo2-MxOcd8JRXELRptoa'

domains = [
    # Add more domains here
    'sunwin188.pro',
]
target = 'jvahomestaging.com'  # Put the target URL here
path = '$1'  # Put the path here
status_code = 301

# Headers with your API token
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

def get_zone_id(domain):
    url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
    response = requests.get(url, headers=headers)
    result = response.json()
    if response.status_code == 200 and result['success']:
        return result['result'][0]['id']
    else:
        print(f"Failed to get zone ID for {domain}: {result['errors']}")
        return None

for domain in domains:
    zone_id = get_zone_id(domain)
    if not zone_id:
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
                    "url": f"https://{target}/{path}",
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
                    "id": "forwarding_url",
                    "value": {
                        "url": f"https://{target}/{path}",
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
            print(f"Page Rule created for domain www.{domain}")
        else:
            print(f"Failed to create Page Rule for www.{domain}: {create_www_response.text}")
    else:
        print(f"Failed to create Page Rule for {domain}: {create_response.text}")