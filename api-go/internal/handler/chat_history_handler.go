// api-go/internal/handler/chat_history_handler.go

package handler

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/takumi-1234/OpenRAG/api-go/internal/middleware"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
	"github.com/takumi-1234/OpenRAG/api-go/internal/service"
)

// ChatHistoryHandlerはチャット履歴関連のHTTPリクエストを処理します。
type ChatHistoryHandler struct {
	service *service.ChatService
}

// NewChatHistoryHandlerは新しいChatHistoryHandlerのインスタンスを生成します。
func NewChatHistoryHandler(service *service.ChatService) *ChatHistoryHandler {
	return &ChatHistoryHandler{service: service}
}

// CreateChatSessionは新しいチャットセッションを作成します。
func (h *ChatHistoryHandler) CreateChatSession(c *gin.Context) {
	var req model.CreateChatSessionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	lectureID, err := strconv.ParseInt(c.Param("lecture_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid lecture ID"})
		return
	}

	// ★★★ ここで `middleware` が正しく使えるようになります ★★★
	userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	session, err := h.service.CreateSession(c.Request.Context(), userID, lectureID, req.Title)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, model.NewChatSessionResponse(*session))
}

// GetChatSessionsは講義に紐づくチャットセッションの一覧を取得します。
func (h *ChatHistoryHandler) GetChatSessions(c *gin.Context) {
	lectureID, err := strconv.ParseInt(c.Param("lecture_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid lecture ID"})
		return
	}

	// ★★★ ここで `middleware` が正しく使えるようになります ★★★
	userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	sessions, err := h.service.GetSessions(c.Request.Context(), userID, lectureID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	res := make([]model.ChatSessionResponse, len(sessions))
	for i, s := range sessions {
		res[i] = model.NewChatSessionResponse(s)
	}

	c.JSON(http.StatusOK, res)
}

// (CreateChatMessage, GetChatMessages は変更なしのため省略)
// ...

// CreateChatMessageはセッションに新しいメッセージを追加します。
// POST /api/v1/sessions/:session_id/messages
func (h *ChatHistoryHandler) CreateChatMessage(c *gin.Context) {
	var req model.CreateChatMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	sessionID, err := strconv.ParseInt(c.Param("session_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session ID"})
		return
	}

	// TODO: このユーザーがこのセッションにメッセージを投稿する権限があるかチェックするロジックが必要
	// userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	message, err := h.service.CreateMessage(c.Request.Context(), sessionID, req.Role, req.Content, req.RetrievedSources)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, model.NewChatMessageResponse(*message))
}

// GetChatMessagesはセッション内のメッセージ履歴を取得します。
// GET /api/v1/sessions/:session_id/messages
func (h *ChatHistoryHandler) GetChatMessages(c *gin.Context) {
	sessionID, err := strconv.ParseInt(c.Param("session_id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid session ID"})
		return
	}

	// TODO: このユーザーがこのセッションのメッセージを閲覧する権限があるかチェックするロジックが必要
	// userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	messages, err := h.service.GetMessages(c.Request.Context(), sessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// レスポンスモデルに変換
	res := make([]model.ChatMessageResponse, len(messages))
	for i, m := range messages {
		res[i] = model.NewChatMessageResponse(m)
	}

	c.JSON(http.StatusOK, res)
}
