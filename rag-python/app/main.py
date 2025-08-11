# rag-python/app/main.py

import logging
import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Path
from fastapi.responses import JSONResponse, FileResponse
from werkzeug.utils import secure_filename

from schemas import ChatRequest
from core.config import settings
from rag.chroma_manager import ChromaManager
from rag.document_processor import process_documents, SUPPORTED_EXTENSIONS
from rag.llm_gemini import GeminiChat
from auth.middleware import auth_middleware, AuthClaims

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# pypdfの冗長な警告はエラーが発生しているように見えるため、抑制する
logging.getLogger("pypdf._reader").setLevel(logging.ERROR)
# ChromaDBの不要なテレメトリーエラーとINFOログを抑制する
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.api.segment").setLevel(logging.WARNING)


# FastAPIアプリケーションの初期化
app = FastAPI(title="OpenRAG - RAG Service")

# サービスインスタンスの初期化 (シングルトン)
chroma_manager = ChromaManager(persist_directory=settings.CHROMA_DB_PATH, embedding_model_name=settings.EMBEDDING_MODEL_NAME)
gemini_chat = GeminiChat(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL_NAME)

# ミドルウェアの適用
app.middleware("http")(auth_middleware)

# --- 依存性注入: 認証ミドルウェアからClaimsを取得 ---
def get_current_claims(request: Request) -> AuthClaims:
    """
    リクエストスコープのstateから認証情報を取得する依存性注入関数。
    認証ミドルウェアによって事前にrequest.state.claimsに情報が格納されている必要がある。
    """
    if not hasattr(request.state, "claims"):
        # このエラーは通常、ミドルウェアが正しく適用されていないか、
        # 保護されていないルートで呼び出された場合に発生する
        raise HTTPException(status_code=401, detail="認証情報が見つかりません。")
    return request.state.claims


@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info("RAG Service Started")


# --- Internal Helper Functions ---

async def _handle_document_upload(file: UploadFile, collection_name: str, uploader_context: str):
    """共通のファイルアップロード処理"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名がありません。")

    safe_filename = secure_filename(file.filename)
    # ファイル名にアップローダーのコンテキスト（guest_idなど）を含めて一意性を高める
    unique_filename = f"{uploader_context}_{safe_filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    file_ext = os.path.splitext(safe_filename)[1].lower()

    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"サポートされていないファイル形式です: {file_ext}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # `process_documents` に `unique_filename` を渡すように変更
        documents = process_documents(file_path, unique_filename)
        if not documents:
            raise HTTPException(status_code=400, detail="ファイルからテキストを抽出できませんでした。")

        chroma_manager.add_documents(documents, collection_name=collection_name)
        return {"filename": safe_filename, "chunks_added": len(documents), "collection_name": collection_name}
    except Exception as e:
        # エラーが発生した場合でも、作成されたファイルを削除しないように変更
        logger.error(f"Error processing file {safe_filename}: {e}", exc_info=True)
        # アップロードされたファイルを削除する
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")
    finally:
        await file.close()


def _handle_chat_request(request: ChatRequest, collection_name: str):
    """共通のチャット処理"""
    # 1. ベクトル検索
    search_results = chroma_manager.search(request.query, collection_name=collection_name, k=3)
    sources = sorted(list(set(doc.metadata.get("source", "不明") for doc in search_results)))

    # 2. LLMによる回答生成
    response_text = gemini_chat.generate_response(
        query=request.query, context_docs=search_results, system_prompt_override=request.system_prompt
    )
    return {"response": response_text, "sources": sources}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/v1/download/{filename}", tags=["Download"])
async def download_file(filename: str):
    """
    アップロードされたファイルをダウンロードする
    """
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ファイルが見つかりません。")
    return FileResponse(path=file_path, filename=filename)

@app.post("/api/v1/lectures/{lecture_id}/upload", tags=["RAG"])
async def upload_document(
    lecture_id: int = Path(..., title="講義ID", ge=1),
    file: UploadFile = File(..., description="アップロードするファイル"),
    claims: AuthClaims = Depends(get_current_claims)
):
    # ここでclaims.user_idを使って、アップロード権限があるかなどをチェック可能（ロジックはapi-go側にあると仮定）
    logger.info(f"User {claims.user_id} uploading file for lecture {lecture_id}")

    try:
        collection_name = f"lecture_{lecture_id}"
        uploader_context = f"user_{claims.user_id}_lecture_{lecture_id}"
        return await _handle_document_upload(file, collection_name, uploader_context)
    except Exception as e:
        logger.error(f"File upload failed for lecture {lecture_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")

@app.post("/api/v1/lectures/{lecture_id}/chat", tags=["RAG"])
async def chat_with_document(
    request: ChatRequest,
    lecture_id: int = Path(..., title="講義ID", ge=1),
    claims: AuthClaims = Depends(get_current_claims)
):
    logger.info(f"User {claims.user_id} chatting with lecture {lecture_id}")
    collection_name = f"lecture_{lecture_id}"

    try:
        return _handle_chat_request(request, collection_name)
    except Exception as e:
        logger.error(f"Chat failed for lecture {lecture_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")

# --- Guest Endpoints (No Authentication) ---

@app.post("/api/v1/guest/{guest_id}/upload", tags=["Guest"])
async def guest_upload_document(
    guest_id: str = Path(..., title="ゲストID"),
    file: UploadFile = File(..., description="アップロードするファイル"),
):
    logger.info(f"Guest {guest_id} uploading file.")

    try:
        collection_name = f"guest_{guest_id}"
        uploader_context = f"guest_{guest_id}"
        return await _handle_document_upload(file, collection_name, uploader_context)
    except Exception as e:
        logger.error(f"Guest file upload failed for guest {guest_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")


@app.post("/api/v1/guest/{guest_id}/chat", tags=["Guest"])
async def guest_chat_with_document(
    request: ChatRequest,
    guest_id: str = Path(..., title="ゲストID"),
):
    logger.info(f"Guest {guest_id} chatting.")
    collection_name = f"guest_{guest_id}"

    try:
        return _handle_chat_request(request, collection_name)
    except Exception as e:
        logger.error(f"Guest chat failed for guest {guest_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")