# frontend-streamlit/app/api_client/go_api.py

import os
import requests
from typing import Dict, Any, List

# 環境変数からGo APIのベースURLを取得
API_GO_BASE_URL = os.getenv("API_GO_URL", "http://localhost:8000")

def login(email: str, password: str) -> Dict[str, Any]:
    """ログインAPIを呼び出し、トークンとユーザー情報を返す"""
    url = f"{API_GO_BASE_URL}/api/v1/users/login"
    payload = {"email": email, "password": password}
    
    response = requests.post(url, json=payload)
    response.raise_for_status()  # エラーがあればHTTPErrorを送出
    return response.json()

def get_lectures(token: str) -> List[Dict[str, Any]]:
    """ユーザーが履修している講義一覧を取得する"""
    url = f"{API_GO_BASE_URL}/api/v1/lectures"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def register(username: str, email: str, password: str) -> Dict[str, Any]:
    """新しいユーザーを登録する"""
    url = f"{API_GO_BASE_URL}/api/v1/users/register"
    payload = {
        "username": username,
        "email": email,
        "password": password
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def create_lecture(token: str, name: str, system_prompt: str) -> Dict[str, Any]:
    """新しいワークスペース（講義）を作成する"""
    url = f"{API_GO_BASE_URL}/api/v1/lectures"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "system_prompt": system_prompt
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()