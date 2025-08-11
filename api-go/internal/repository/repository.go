// api-go/internal/repository/repository.go

package repository

import (
	"context"

	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
)

// UserRepository はユーザー関連のDB操作を定義します。
type UserRepository interface {
	CreateUser(ctx context.Context, user *model.User) (int64, error)
	GetUserByEmail(ctx context.Context, email string) (*model.User, error)
}

// LectureRepository は講義関連のDB操作を定義します。
type LectureRepository interface {
	CreateLecture(ctx context.Context, lecture *model.Lecture) (int64, error)
	EnrollUserInLecture(ctx context.Context, userID, lectureID int64, role string) error
	GetLecturesByUserID(ctx context.Context, userID int64) ([]model.Lecture, error)
}

// ChatRepository はチャット関連のDB操作を定義します。
// ★★★ このインターフェース定義を追加・修正します ★★★
type ChatRepository interface {
	CreateChatSession(ctx context.Context, session *model.ChatSession) (int64, error)
	GetChatSessionsByLectureID(ctx context.Context, userID, lectureID int64) ([]model.ChatSession, error)
	CreateChatMessage(ctx context.Context, message *model.ChatMessage) (int64, error)
	GetChatMessagesBySessionID(ctx context.Context, sessionID int64) ([]model.ChatMessage, error)
}
