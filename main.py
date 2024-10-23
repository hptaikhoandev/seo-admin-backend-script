from fastapi import FastAPI

app = FastAPI()

# Endpoint API
@app.get("/api/v1/resource")
def get_resource():
    return {"message": "Hello, this is a FastAPI response!", "status": "okkkk"}

