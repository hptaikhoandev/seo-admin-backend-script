import csv
import requests
import random
import json

api_token = 'fjtVVMq3P--nYpUJ2kNs9Gq-i4_R5yWd-tC1kXLs'
admin_accounts = [
    {"account_id": "e1c1a8d5af36e261554feeb763bfa9ca", "email": "ting@darasa.io"},
]

server_ip = '11.11.11.11'

def read_json_file(file_path):
    # Open and load the JSON file
    global server_ip, ssl_type, domains
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Print keys and corresponding values
    for key, value in data.items():
        if key == "ip":
            server_ip = value
        if key == "ssl_type":
            ssl_type = value
        if key == "domains":
            domains = value

# Specify the path to your JSON file
file_path = 'input.json'

# Call the function to read the JSON file and print keys and values
read_json_file(file_path)

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

add_domain_url = 'https://api.cloudflare.com/client/v4/zones'

results = []

def clean_url(url):
    # Remove 'https://' from the start
    if url.startswith('https://'):
        url = url[8:]  # Remove the first 8 characters
    if url.startswith('http://'):
        url = url[7:]  # Remove the first 8 characters
    # Remove trailing slashes
    url = url.rstrip('/')

    return url

# def loop_domains(domains):
for domain in domains:
    domain = clean_url(domain)
    print(f"Adding domain: {domain}")

    # Select a random admin account
    account = random.choice(admin_accounts)
    account_id = account['account_id']
    account_email = account['email']

    # Step 1: Add a Domain
    domain_data = {
        "name": domain,
        "account": {
            "id": account_id
        },
        "jump_start": True
    }
    domain_response = requests.post(add_domain_url, headers=headers, json=domain_data)
    domain_result = domain_response.json()
    # print(f"Response Status Code: {domain_result}")

    if not domain_result.get('success'):
        print(f"Error adding domain {domain}: {domain_result.get('errors')}")
        
        continue  # Skip to the next domain

    zone_id = domain_result['result']['id']
    name_servers = domain_result['result']['name_servers']

    # Step 2: Fetch and Remove Existing DNS Records
    dns_record_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
    dns_list_response = requests.get(dns_record_url, headers=headers)
    dns_list_result = dns_list_response.json()

    if dns_list_result.get('success'):
        for record in dns_list_result['result']:
            delete_url = f"{dns_record_url}/{record['id']}"
            delete_response = requests.delete(delete_url, headers=headers)
            delete_result = delete_response.json()
            if delete_result.get('success'):
                print(f"Deleted DNS record {record['name']} ({record['type']})")
            else:
                print(f"Error deleting DNS record {record['name']} ({record['type']}): {delete_result.get('errors')}")

    # Write the result to CSV
    # writer.writerow([domain, ",".join(name_servers)])
    results.append({'domain': domain, 'ns': ",".join(name_servers)})
    # Step 3: Add DNS A Record for root domain
    dns_record_data = {
        "type": "A",
        "name": domain,
        "content": server_ip,
        "ttl": 120,
        "proxied": True
    }
    dns_response = requests.post(dns_record_url, headers=headers, json=dns_record_data)
    dns_result = dns_response.json()

    if not dns_result.get('success'):
        print(f"Error adding DNS A record for domain {domain}: {dns_result.get('errors')}")
        continue  # Skip to the next domain

    # Step 4: Add CNAME Record for www
    cname_record_data = {
        "type": "CNAME",
        "name": "www",
        "content": domain,
        "ttl": 120,
        "proxied": True
    }
    cname_response = requests.post(dns_record_url, headers=headers, json=cname_record_data)
    cname_result = cname_response.json()

    if not cname_result.get('success'):
        print(f"Error adding CNAME record for www.{domain}: {cname_result.get('errors')}")
        continue  # Skip to the next domain

    # Step 5: Enable SSL (Flexible)
    ssl_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl'
    ssl_data = {
        "value": ssl_type
    }
    ssl_response = requests.patch(ssl_url, headers=headers, json=ssl_data)
    ssl_result = ssl_response.json()

    if not ssl_result.get('success'):
        print(f"Error enabling SSL for domain {domain}: {ssl_result.get('errors')}")
        continue  # Skip to the next domain
    
    always_use_https_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/always_use_https'
    always_use_https_data = {
        "value": "on"
    }
    always_use_https_response = requests.patch(always_use_https_url, headers=headers, json=always_use_https_data)
    always_use_https_result = always_use_https_response.json()
    
    if not always_use_https_result.get('success'):
        print(f"Error enabling Always Use HTTPS for domain {domain}: {always_use_https_result.get('errors')}")

# with open("domains.txt", "r") as file:
#     domains = [line.strip() for line in file if line.strip()]
    

with open('domains_list.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Domain','Name Servers'])
    sorted_data = sorted(results, key=lambda x: x['ns'])
    
    writer.writerows([[value['domain'], value['ns']] for value in sorted_data])
    
print("All domains processed and results saved to domain_list.csv.")