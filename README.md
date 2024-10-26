# seo-admin-backend-script
Step by step run project in local:
$ python3 -m venv venv 
$ source venv/bin/activate
$ pip3 install fastapi uvicorn
$ uvicorn main:app --reload
=> http://localhost:8000/api/v1/resource