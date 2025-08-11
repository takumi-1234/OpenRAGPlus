FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HF_HOME="/app/.cache/huggingface"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 非rootユーザーの作成と設定
RUN addgroup --system appgroup && adduser --system --group appuser \
    # キャッシュディレクトリを作成し、所有権を渡す
    && mkdir -p ${HF_HOME} \
    && chown -R appuser:appgroup /app ${HF_HOME}

# アプリケーションを実行するユーザーに切り替える
USER appuser

COPY ./app /app

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]