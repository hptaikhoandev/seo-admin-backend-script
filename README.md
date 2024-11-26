# seo-admin-backend-script
Step by step run project in local:
$ make run
OR:
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install fastapi uvicorn requests paramiko boto3 google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib
$ uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 7200 --reload
OR:
$ python3 -m venv venv && source venv/bin/activate && pip3 install fastapi uvicorn requests paramiko && uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 7200 --reload
=> http://localhost:8000/api/v1/resource

// Homepage Redirect: /* ==> /
https://oldsite.com/about       → https://newsite.com
https://oldsite.com/products    → https://newsite.com
https://oldsite.com/contact     → https://newsite.com
https://oldsite.com/anything    → https://newsite.com

// Wildcard Redirect https://olddomain.com/* → https://newdomain.com/$1 

Cụ thể:
- https://olddomain.com/about → https://newdomain.com/about
- https://olddomain.com/products → https://newdomain.com/products
- https://olddomain.com/blog/post-1 → https://newdomain.com/blog/post-1

ducla.uk
royandsom.uk