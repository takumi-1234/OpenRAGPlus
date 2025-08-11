// api-go/internal/service/user_service.go
package service

import (
	"context"
	"database/sql"
	"errors"

	"github.com/takumi-1234/OpenRAG/api-go/internal/auth"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
	"github.com/takumi-1234/OpenRAG/api-go/internal/repository"
)

type UserService struct {
	repo    repository.UserRepository
	jwtAuth *auth.JWTAuth
}

func NewUserService(repo repository.UserRepository, jwtAuth *auth.JWTAuth) *UserService {
	return &UserService{repo: repo, jwtAuth: jwtAuth}
}

func (s *UserService) Register(ctx context.Context, req *model.RegisterUserRequest) (*model.UserResponse, error) {
	// ユーザーが既に存在するか確認
	existingUser, err := s.repo.GetUserByEmail(ctx, req.Email)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return nil, err
	}
	if existingUser != nil {
		return nil, errors.New("user with this email already exists")
	}

	hashedPassword, err := auth.HashPassword(req.Password)
	if err != nil {
		return nil, err
	}

	user := &model.User{
		Username:       req.Username,
		Email:          req.Email,
		HashedPassword: hashedPassword,
	}

	id, err := s.repo.CreateUser(ctx, user)
	if err != nil {
		return nil, err
	}
	user.ID = id

	return &model.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		CreatedAt: user.CreatedAt,
	}, nil
}

func (s *UserService) Login(ctx context.Context, req *model.LoginUserRequest) (*model.LoginUserResponse, error) {
	user, err := s.repo.GetUserByEmail(ctx, req.Email)
	if err != nil {
		return nil, errors.New("invalid email or password")
	}

	err = auth.CheckPassword(req.Password, user.HashedPassword)
	if err != nil {
		return nil, errors.New("invalid email or password")
	}

	token, err := s.jwtAuth.GenerateToken(user.ID)
	if err != nil {
		return nil, err
	}

	return &model.LoginUserResponse{
		Token: token,
		User: model.UserResponse{
			ID:        user.ID,
			Username:  user.Username,
			Email:     user.Email,
			CreatedAt: user.CreatedAt,
		},
	}, nil
}
