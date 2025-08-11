// api-go/internal/model/model.go

package model

import (
	"encoding/json"
	"time"
)

// --- Database Models ---

type User struct {
	ID             int64     `db:"id"`
	Username       string    `db:"username"`
	Email          string    `db:"email"`
	HashedPassword string    `db:"hashed_password"`
	IsActive       bool      `db:"is_active"`
	CreatedAt      time.Time `db:"created_at"`
	UpdatedAt      time.Time `db:"updated_at"`
}

type Lecture struct {
	ID                     int64     `db:"id"`
	Name                   string    `db:"name"`
	Description            string    `db:"description"`
	VectorDBCollectionName string    `db:"vector_db_collection_name"`
	SystemPrompt           string    `db:"system_prompt"`
	CreatedBy              int64     `db:"created_by"`
	CreatedAt              time.Time `db:"created_at"`
	UpdatedAt              time.Time `db:"updated_at"`
}

// --- API Request/Response Models ---

// User
type RegisterUserRequest struct {
	Username string `json:"username" binding:"required,alphanum,min=4,max=30"`
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
}

type LoginUserRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
}

type UserResponse struct {
	ID        int64     `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}

type LoginUserResponse struct {
	Token string       `json:"token"`
	User  UserResponse `json:"user"`
}

// Lecture
type CreateLectureRequest struct {
	Name         string `json:"name" binding:"required,min=3,max=100"`
	Description  string `json:"description"`
	SystemPrompt string `json:"system_prompt"`
}

type LectureResponse struct {
	ID                     int64     `json:"id"`
	Name                   string    `json:"name"`
	Description            string    `json:"description"`
	VectorDBCollectionName string    `json:"vector_db_collection_name"`
	SystemPrompt           string    `json:"system_prompt"`
	CreatedBy              int64     `json:"created_by"`
	CreatedAt              time.Time `json:"created_at"`
}

type ChatSession struct {
	ID        int64     `db:"id"`
	UserID    int64     `db:"user_id"`
	LectureID int64     `db:"lecture_id"`
	Title     string    `db:"title"`
	CreatedAt time.Time `db:"created_at"`
	UpdatedAt time.Time `db:"updated_at"`
}

type ChatMessage struct {
	ID               int64           `db:"id"`
	SessionID        int64           `db:"session_id"`
	Role             string          `db:"role"` // "user" or "assistant"
	Content          string          `db:"content"`
	RetrievedSources json.RawMessage `db:"retrieved_sources"` // JSON型を扱う
	CreatedAt        time.Time       `db:"created_at"`
}

type CreateChatSessionRequest struct {
	Title string `json:"title" binding:"required,min=1,max=100"`
}

type CreateChatMessageRequest struct {
	Role             string `json:"role" binding:"required,oneof=user assistant"`
	Content          string `json:"content" binding:"required"`
	RetrievedSources string `json:"retrieved_sources,omitempty"` // JSON文字列として受け取る
}

type ChatSessionResponse struct {
	ID        int64     `json:"id"`
	UserID    int64     `json:"user_id"`
	LectureID int64     `json:"lecture_id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

func NewChatSessionResponse(session ChatSession) ChatSessionResponse {
	return ChatSessionResponse{
		ID:        session.ID,
		UserID:    session.UserID,
		LectureID: session.LectureID,
		Title:     session.Title,
		CreatedAt: session.CreatedAt,
		UpdatedAt: session.UpdatedAt,
	}
}

type ChatMessageResponse struct {
	ID               int64           `json:"id"`
	SessionID        int64           `json:"session_id"`
	Role             string          `json:"role"`
	Content          string          `json:"content"`
	RetrievedSources json.RawMessage `json:"retrieved_sources"`
	CreatedAt        time.Time       `json:"created_at"`
}

func NewChatMessageResponse(message ChatMessage) ChatMessageResponse {
	return ChatMessageResponse{
		ID:               message.ID,
		SessionID:        message.SessionID,
		Role:             message.Role,
		Content:          message.Content,
		RetrievedSources: message.RetrievedSources,
		CreatedAt:        message.CreatedAt,
	}
}
