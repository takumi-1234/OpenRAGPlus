// api-go/internal/middleware/auth_middleware.go

package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	// このミドルウェアは `internal/auth` パッケージのJWT検証機能を利用します
	"github.com/takumi-1234/OpenRAG/api-go/internal/auth"
)

// ミドルウェアとハンドラ間でデータを渡すために使用する定数
const (
	// AuthorizationHeaderKey はHTTPリクエストヘッダー内の認証情報キーです。
	AuthorizationHeaderKey = "authorization"
	// AuthorizationTypeBearer はサポートする認証タイプです。
	AuthorizationTypeBearer = "bearer"
	// AuthorizationPayloadKey はGinのコンテキストに認証済みユーザーのペイロード（この場合はUserID）を保存するためのキーです。
	AuthorizationPayloadKey = "authorization_payload"
)

// AuthMiddleware はJWTトークンを検証するためのGinミドルウェアを作成します。
func AuthMiddleware(secretKey string) gin.HandlerFunc {
	// gin.HandlerFuncを返すクロージャ
	return func(c *gin.Context) {
		// 1. リクエストヘッダーから "Authorization" の値を取得します。
		authHeader := c.GetHeader(AuthorizationHeaderKey)
		if len(authHeader) == 0 {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "authorization header is not provided"})
			return // 処理を中断します。
		}

		// 2. ヘッダーのフォーマットが "Bearer <token>" であることを確認します。
		fields := strings.Fields(authHeader)
		if len(fields) < 2 {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization header format"})
			return // 処理を中断します。
		}

		// 3. 認証タイプが "bearer" であることを確認します。
		authType := strings.ToLower(fields[0])
		if authType != AuthorizationTypeBearer {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unsupported authorization type, must be 'bearer'"})
			return // 処理を中断します。
		}

		// 4. トークンを検証します。
		accessToken := fields[1]
		jwtAuth := auth.NewJWTAuth(secretKey)
		claims, err := jwtAuth.ValidateToken(accessToken)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid or expired token"})
			return // 処理を中断します。
		}

		// 5. 検証成功後、ペイロード（UserID）をリクエストのコンテキストに保存します。
		// これにより、後続のハンドラで `c.MustGet(AuthorizationPayloadKey)` としてユーザーIDを取得できます。
		c.Set(AuthorizationPayloadKey, claims.UserID)

		// 6. 次のミドルウェアまたはハンドラに処理を移します。
		c.Next()
	}
}
