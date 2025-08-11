# --- 1. ビルドステージ ---
FROM golang:1.24-alpine AS base
WORKDIR /app

# gitをインストールして、go modが依存関係を解決できるようにする
RUN apk add --no-cache git

# go.mod と go.sum をコピーして依存関係を先に解決
# これにより、ソースコードの変更だけで依存関係の再ダウンロードが走らなくなる
COPY api-go/go.mod api-go/go.sum ./
RUN go mod download

# ソースコードをコピー
# ディレクトリの末尾にスラッシュを追加することで、中身だけがコピーされる
COPY api-go/ ./
RUN go mod tidy

# アプリケーションをビルド
# -w -s フラグでデバッグ情報を削除し、バイナリサイズを削減
RUN CGO_ENABLED=0 GOOS=linux go build -o /main -ldflags="-w -s" .

# --- 1.5 開発ステージ ---
FROM base AS development
# airをインストール
RUN go install github.com/air-verse/air@latest
WORKDIR /app
CMD ["air", "-c", ".air.toml"]

# --- 2. 実行ステージ ---
FROM alpine:latest
WORKDIR /app

# 非rootユーザーを作成し、ディレクトリの所有権を渡す
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
RUN chown appuser:appgroup /app

# ビルドステージからコンパイル済みバイナリをコピー
COPY --from=base /main .

RUN chmod +x /app/main

# ユーザーを切り替える
USER appuser

EXPOSE 8000
CMD ["/app/main"]
