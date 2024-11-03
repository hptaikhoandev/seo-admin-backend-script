# seo-admin-backend-script
Step by step run project in local:
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install fastapi uvicorn
$ uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 7200 --reload
OR:
$ python3 -m venv venv && source venv/bin/activate && pip3 install fastapi uvicorn && uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 7200 --reload
=> http://localhost:8000/api/v1/resource