// api-go/internal/service/chat_service.go

package service

import (
	"context"

	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
	"github.com/takumi-1234/OpenRAG/api-go/internal/repository"
)

// ChatServiceはチャット関連のビジネスロジックを提供します。
type ChatService struct {
	chatRepo repository.ChatRepository
}

// NewChatServiceは新しいChatServiceのインスタンスを生成します。
func NewChatService(chatRepo repository.ChatRepository) *ChatService {
	return &ChatService{chatRepo: chatRepo}
}

// CreateSessionは新しいチャットセッションを作成します。
func (s *ChatService) CreateSession(ctx context.Context, userID, lectureID int64, title string) (*model.ChatSession, error) {
	session := &model.ChatSession{
		UserID:    userID,
		LectureID: lectureID,
		Title:     title,
	}
	sessionID, err := s.chatRepo.CreateChatSession(ctx, session)
	if err != nil {
		return nil, err
	}
	session.ID = sessionID
	return session, nil
}

// GetSessionsはユーザーと講義に紐づくセッション一覧を取得します。
func (s *ChatService) GetSessions(ctx context.Context, userID, lectureID int64) ([]model.ChatSession, error) {
	return s.chatRepo.GetChatSessionsByLectureID(ctx, userID, lectureID)
}

// CreateMessageは新しいチャットメッセージを作成します。
func (s *ChatService) CreateMessage(ctx context.Context, sessionID int64, role, content, sourcesJSON string) (*model.ChatMessage, error) {
	message := &model.ChatMessage{
		SessionID: sessionID,
		Role:      role,
		Content:   content,
	}

	if sourcesJSON != "" {
		message.RetrievedSources = []byte(sourcesJSON)
	}

	messageID, err := s.chatRepo.CreateChatMessage(ctx, message)
	if err != nil {
		return nil, err
	}
	message.ID = messageID
	return message, nil
}

// GetMessagesはセッションに紐づくメッセージ一覧を取得します。
func (s *ChatService) GetMessages(ctx context.Context, sessionID int64) ([]model.ChatMessage, error) {
	return s.chatRepo.GetChatMessagesBySessionID(ctx, sessionID)
}
