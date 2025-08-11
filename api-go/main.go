// api-go/main.go

package main

import (
	"log"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/jmoiron/sqlx"
	"github.com/takumi-1234/OpenRAG/api-go/internal/auth"
	"github.com/takumi-1234/OpenRAG/api-go/internal/config"
	"github.com/takumi-1234/OpenRAG/api-go/internal/handler"

	// ★★★ ここを修正: "auth" という別名を削除します ★★★
	"github.com/takumi-1234/OpenRAG/api-go/internal/middleware"
	"github.com/takumi-1234/OpenRAG/api-go/internal/repository"
	"github.com/takumi-1234/OpenRAG/api-go/internal/service"
)

func main() {
	// 1. 設定の読み込み
	cfg, err := config.LoadConfig(".")
	if err != nil {
		log.Fatalf("could not load config: %v", err)
	}

	// 2. データベース接続 (リトライロジック付き)
	var db *sqlx.DB
	maxRetries := 10
	retryInterval := 3 * time.Second

	for i := 0; i < maxRetries; i++ {
		db, err = sqlx.Connect("mysql", cfg.DBSource)
		if err == nil {
			log.Println("Database connection successful")
			break
		}
		log.Printf("could not connect to the database (attempt %d/%d): %v", i+1, maxRetries, err)
		time.Sleep(retryInterval)
	}

	if err != nil {
		log.Fatalf("failed to connect to the database after %d attempts: %v", maxRetries, err)
	}
	defer db.Close()

	// 3. 依存性の注入 (リポジトリ -> サービス -> ハンドラ)
	jwtAuth := auth.NewJWTAuth(cfg.JWTSecretKey)

	userRepo := repository.NewUserRepository(db)
	userService := service.NewUserService(userRepo, jwtAuth)
	userHandler := handler.NewUserHandler(userService)

	lectureRepo := repository.NewLectureRepository(db)
	lectureService := service.NewLectureService(lectureRepo)
	lectureHandler := handler.NewLectureHandler(lectureService)

	chatRepo := repository.NewChatRepository(db)
	chatService := service.NewChatService(chatRepo)
	chatHandler := handler.NewChatHistoryHandler(chatService)

	// 4. Ginルーターの設定
	router := gin.Default()

	api := router.Group("/api/v1")

	// --- ユーザー認証エンドポイント ---
	api.POST("/users/register", userHandler.Register)
	api.POST("/users/login", userHandler.Login)

	// --- 認証必須のエンドポイントグループ ---
	// ★★★ ここで `middleware` が正しく使えるようになります ★★★
	authRoutes := api.Group("/").Use(middleware.AuthMiddleware(cfg.JWTSecretKey))
	{
		// --- 講義関連エンドポイント ---
		authRoutes.POST("/lectures", lectureHandler.CreateLecture)
		authRoutes.GET("/lectures", lectureHandler.GetLecturesByUserID)
		authRoutes.POST("/lectures/:id/enroll", lectureHandler.EnrollInLecture)

		// --- チャットセッション関連エンドポイント ---
		authRoutes.POST("/lectures/:id/sessions", chatHandler.CreateChatSession)
		authRoutes.GET("/lectures/:id/sessions", chatHandler.GetChatSessions)

		// --- チャットメッセージ関連エンドポイント ---
		authRoutes.POST("/sessions/:session_id/messages", chatHandler.CreateChatMessage)
		authRoutes.GET("/sessions/:session_id/messages", chatHandler.GetChatMessages)
	}

	// 5. サーバーの起動
	log.Printf("Server starting on port %s", cfg.ServerAddress)
	if err := router.Run(cfg.ServerAddress); err != nil {
		log.Fatalf("failed to run server: %v", err)
	}
}
