// api-go/internal/repository/user_repository.go
package repository

import (
	"context"

	"github.com/jmoiron/sqlx"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
)

type userRepository struct {
	db *sqlx.DB
}

func NewUserRepository(db *sqlx.DB) UserRepository {
	return &userRepository{db: db}
}

func (r *userRepository) CreateUser(ctx context.Context, user *model.User) (int64, error) {
	query := `INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)`
	result, err := r.db.ExecContext(ctx, query, user.Username, user.Email, user.HashedPassword)
	if err != nil {
		return 0, err
	}
	id, err := result.LastInsertId()
	if err != nil {
		return 0, err
	}
	return id, nil
}

func (r *userRepository) GetUserByEmail(ctx context.Context, email string) (*model.User, error) {
	var user model.User
	query := `SELECT * FROM users WHERE email = ? LIMIT 1`
	err := r.db.GetContext(ctx, &user, query, email)
	if err != nil {
		return nil, err
	}
	return &user, nil
}
