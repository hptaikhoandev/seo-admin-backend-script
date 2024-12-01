from app.models.clonesite_request import ClonesiteRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from fastapi import HTTPException
import pymysql
import requests
import random
import time
import paramiko
import os
import json
import io
from datetime import datetime

api_token_backend = os.getenv('API_TOKEN_BACKEND')
url_backend = f"{os.getenv('URL_DOMAIN_BACKEND')}/servers"
headers_backend = {
    'Authorization': f'Bearer {api_token_backend}',
    'Content-Type': 'application/json'
}
class TrackinglinkController:
    @staticmethod
    async def tracking_links():
        result = {"success": 0, "fail": {"count": 0, "messages": []}}
        # Kết nối đến cơ sở dữ liệu
        connection = pymysql.connect(
            host='localhost', 
            user='wp_user',  
            password='wp_password',  
            database='wp_database',
            port=8002,
        )
        search_text = "https://thethao8xbet.top/"

        try:
            # cursor = connection.cursor()

            # # Lấy danh sách tất cả các cột trong bảng wp_posts
            # cursor.execute("SHOW COLUMNS FROM `wp_posts`")
            # columns = cursor.fetchall()

            # for column in columns:
            #     column_name = column[0]

            #     # Truy vấn để tìm kiếm đoạn văn bản trong cột
            #     query = f"SELECT ID, `{column_name}` FROM `wp_posts` WHERE `{column_name}` LIKE %s"
            #     cursor.execute(query, (f'%{search_text}%',))
            #     results = cursor.fetchall()

            #     if results:
            #         for row in results:
            #             post_id = row[0]
            #             value = row[1]
            #             print(f"Found in column: {column_name}, Post ID: {post_id}, value: {value}")
            #             result["success"] += 1
            
            return {
                "status": "success",
                "result": result,
            }

        except pymysql.connect.Error as e:
            print(f"Error: {e}")
            result["fail"]["count"] += 1
            result["fail"]["messages"].append(f"Error: {str(e)}") 

        finally:
            cursor.close()
            connection.close()


        print(f"Key Pair already exists.")
        return {"status": "error", "result": result}
        # params = {
        #     "page": 1,
        #     "limit": 10000,
        #     "search": key_name,
        #     "sortBy": "team",
        #     "sortDesc": "false",
        # }
        # response = requests.get(url_backend, params=params, headers=headers_backend)
        # # Kiểm tra lỗi HTTP
        # response.raise_for_status()
        # try:
        #     data = response.json()  
        # except requests.JSONDecodeError:
        #     raise ValueError("Response is not a valid JSON")
        # servers = data.get("data", []) 
        # # Trả về danh sách account
        # return servers[0]["private_key"]
    
    

