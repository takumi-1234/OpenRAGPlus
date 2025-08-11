import os
import requests
import uuid

# --- 設定 ---
# 認証情報 (ここにメールアドレスとパスワードを入力)
# ゲストとしてアップロードする場合は、両方を "Guest" に設定
EMAIL = "sample@gmail.com"  # 例: "test@example.com"
PASSWORD = "sample@gmail.com"  # 例: "password123"

# アップロードするファイルがあるディレクトリ
UPLOAD_DIR = "upload_files_test"

# APIのベースURL
API_GO_URL = "http://localhost:8000"
API_PYTHON_RAG_URL = "http://localhost:8001"

# --- ディレクトリとテストファイルの準備 ---
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    with open(os.path.join(UPLOAD_DIR, "file1.txt"), "w") as f:
        f.write("This is a test file 1.")
    with open(os.path.join(UPLOAD_DIR, "file2.txt"), "w") as f:
        f.write("This is a test file 2.")

# --- APIクライアント関数 ---

def login(email, password):
    """Go APIにログインして認証トークンを取得する"""
    url = f"{API_GO_URL}/api/v1/users/login"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("token")
    except requests.exceptions.RequestException as e:
        print(f"ログインに失敗しました: {e}")
        return None

def get_first_lecture_id(token):
    """Go APIから最初のワークスペースIDを取得する"""
    url = f"{API_GO_URL}/api/v1/lectures"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        lectures = response.json()
        if lectures:
            return lectures[0]["id"]
        else:
            print("利用可能なワークスペースがありません。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"ワークスペースの取得に失敗しました: {e}")
        return None

def upload_files_for_user(token, lecture_id, directory):
    """認証ユーザーとしてファイルをアップロードする"""
    url = f"{API_PYTHON_RAG_URL}/api/v1/lectures/{lecture_id}/upload"
    headers = {"Authorization": f"Bearer {token}"}
    upload_files(url, directory, headers)

def upload_files_for_guest(directory):
    """ゲストとしてファイルをアップロードする"""
    guest_id = str(uuid.uuid4())
    url = f"{API_PYTHON_RAG_URL}/api/v1/guest/{guest_id}/upload"
    print(f"ゲストID: {guest_id} でアップロードします。")
    upload_files(url, directory)

def upload_files(url, directory, headers=None):
    """指定されたURLにファイルを一括でアップロードする"""
    files_to_upload = []
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            files_to_upload.append(('file', (filename, open(path, 'rb'), 'application/octet-stream')))

    if not files_to_upload:
        print("アップロードするファイルがありません。")
        return

    try:
        # rag-pythonは単一の`file`を想定しているため、1ファイルずつ送信する
        for file_tuple in files_to_upload:
            print(f"{file_tuple[1][0]} をアップロード中...")
            # `files`パラメータは辞書型である必要がある
            response = requests.post(url, files={'file': file_tuple[1]}, headers=headers, timeout=300)
            response.raise_for_status()
            print(f"  -> 完了: {response.json()}")
        print("すべてのファイルのアップロードが完了しました。")
    except requests.exceptions.RequestException as e:
        print(f"アップロード中にエラーが発生しました: {e}")
        if e.response:
            print(f"エラー詳細: {e.response.text}")

# --- メイン処理 ---
if __name__ == "__main__":
    if EMAIL.lower() == "guest" and PASSWORD.lower() == "guest":
        print("ゲストとしてファイルアップロードを実行します。")
        upload_files_for_guest(UPLOAD_DIR)
    else:
        print("認証ユーザーとしてファイルアップロードを実行します。")
        token = login(EMAIL, PASSWORD)
        if token:
            lecture_id = get_first_lecture_id(token)
            if lecture_id:
                upload_files_for_user(token, lecture_id, UPLOAD_DIR)