from app.models.redirect_request import RedirectRequest
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
    async def add_domains(request: RedirectRequest):
        results = []
        

        return {"message": "Domains processed successfully", "results": results}

    