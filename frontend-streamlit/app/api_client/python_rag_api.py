# frontend-streamlit/app/api_client/python_rag_api.py

import os
import requests
import json
from typing import Dict, Any, IO

# 環境変数からPython RAG APIのベースURLを取得
API_PYTHON_RAG_URL = os.getenv("API_PYTHON_RAG_URL", "http://localhost:8001")

def upload_document(token: str, lecture_id: int, file: IO) -> Dict[str, Any]:
    """指定された講義にドキュメントをアップロードする"""
    url = f"{API_PYTHON_RAG_URL}/api/v1/lectures/{lecture_id}/upload"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": file}
    
    # 認証はヘッダーで行うため、不要なクエリパラメータは削除する
    response = requests.post(url, headers=headers, files=files, timeout=300)
    response.raise_for_status()
    return response.json()

def post_chat_message(token: str, lecture_id: int, query: str, system_prompt: str = None) -> Dict[str, Any]:
    """チャットメッセージを送信し、RAGによる回答を取得する"""
    url = f"{API_PYTHON_RAG_URL}/api/v1/lectures/{lecture_id}/chat"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query}
    if system_prompt:
        payload["system_prompt"] = system_prompt
        
    response = requests.post(url, headers=headers, json=payload, timeout=300) # タイムアウトを長めに設定
    response.raise_for_status()
    return response.json()

def guest_upload_document(guest_id: str, file: IO) -> Dict[str, Any]:
    """ゲストとしてドキュメントをアップロードする"""
    url = f"{API_PYTHON_RAG_URL}/api/v1/guest/{guest_id}/upload"
    files = {"file": file}
    
    response = requests.post(url, files=files, timeout=300)
    response.raise_for_status()
    return response.json()

def guest_post_chat_message(guest_id: str, query: str, system_prompt: str = None) -> Dict[str, Any]:
    """ゲストとしてチャットメッセージを送信する"""
    url = f"{API_PYTHON_RAG_URL}/api/v1/guest/{guest_id}/chat"
    payload = {"query": query}
    if system_prompt:
        payload["system_prompt"] = system_prompt
        
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()