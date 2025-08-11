# rag-python/app/auth/middleware.py

import jwt
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, Field
from core.config import settings

class AuthClaims(BaseModel):
    user_id: int = Field(..., alias="user_id")

async def auth_middleware(request: Request, call_next):
    # 認証が不要な公開パスを定義
    public_paths = ["/health", "/docs", "/openapi.json"]
    if request.url.path in public_paths or request.url.path.startswith("/api/v1/guest"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header is missing"},
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
        claims = AuthClaims.model_validate(payload)
        request.state.claims = claims

    except jwt.PyJWTError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Invalid token: {e}"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Could not validate credentials"},
        )

    response = await call_next(request)
    return response