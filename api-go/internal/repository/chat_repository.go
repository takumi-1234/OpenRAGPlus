// api-go/internal/repository/chat_repository.go

package repository

import (
	"context"

	"github.com/jmoiron/sqlx"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
)

// chatRepository構造体は ChatRepository インターフェースを実装します。
type chatRepository struct {
	db *sqlx.DB
}

// NewChatRepository は ChatRepository の新しいインスタンスを作成します。
// 戻り値の型は `repository.go` で定義したインターフェース `ChatRepository` です。
func NewChatRepository(db *sqlx.DB) ChatRepository {
	return &chatRepository{db: db}
}

// CreateChatSession は新しいチャットセッションをデータベースに作成します。
func (r *chatRepository) CreateChatSession(ctx context.Context, session *model.ChatSession) (int64, error) {
	query := `INSERT INTO chat_sessions (user_id, lecture_id, title) VALUES (?, ?, ?)`
	result, err := r.db.ExecContext(ctx, query, session.UserID, session.LectureID, session.Title)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

// GetChatSessionsByLectureID は指定されたユーザーと講義IDに紐づくチャットセッションの一覧を取得します。
func (r *chatRepository) GetChatSessionsByLectureID(ctx context.Context, userID, lectureID int64) ([]model.ChatSession, error) {
	var sessions []model.ChatSession
	query := `SELECT * FROM chat_sessions WHERE user_id = ? AND lecture_id = ? ORDER BY updated_at DESC`
	err := r.db.SelectContext(ctx, &sessions, query, userID, lectureID)
	return sessions, err
}

// CreateChatMessage は新しいチャットメッセージをデータベースに作成します。
func (r *chatRepository) CreateChatMessage(ctx context.Context, message *model.ChatMessage) (int64, error) {
	query := `INSERT INTO chat_messages (session_id, role, content, retrieved_sources) VALUES (?, ?, ?, ?)`
	result, err := r.db.ExecContext(ctx, query, message.SessionID, message.Role, message.Content, message.RetrievedSources)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

// GetChatMessagesBySessionID は指定されたセッションIDに紐づくメッセージの一覧を時系列で取得します。
func (r *chatRepository) GetChatMessagesBySessionID(ctx context.Context, sessionID int64) ([]model.ChatMessage, error) {
	var messages []model.ChatMessage
	query := `SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC`
	err := r.db.SelectContext(ctx, &messages, query, sessionID)
	return messages, err
}
