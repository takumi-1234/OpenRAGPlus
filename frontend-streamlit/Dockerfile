# frontend-streamlit/Dockerfile

# ベースイメージ
FROM python:3.10-slim

# 作業ディレクトリの設定
WORKDIR /app

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HF_HOME="/app/.cache/huggingface"

# システム依存関係のインストール (root権限で実行)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt を先にコピー (root権限で実行)
COPY ./requirements.txt .

# Python依存関係のインストール (root権限で実行)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- ここからユーザー設定 ---

# 非rootユーザーの作成と設定
RUN addgroup --system appgroup && adduser --system --group appuser

# アプリケーションとキャッシュディレクトリの所有者を appuser に変更
# /app 全体を chown することで、後でコピーするコードも appuser のものになる
RUN mkdir -p ${HF_HOME} && chown -R appuser:appgroup ${HF_HOME} /app

# アプリケーションを実行するユーザーに切り替える
USER appuser

# アプリケーションコードのコピー (appuserとしてコピー)
# localのappディレクトリの中身を、コンテナのWORKDIRである/appにコピー
COPY app/ .

# Streamlitサーバーの起動
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]