// api-go/internal/repository/lecture_repository.go
package repository

import (
	"context"

	"github.com/jmoiron/sqlx"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
)

type lectureRepository struct {
	db *sqlx.DB
}

func NewLectureRepository(db *sqlx.DB) LectureRepository {
	return &lectureRepository{db: db}
}

func (r *lectureRepository) CreateLecture(ctx context.Context, lecture *model.Lecture) (int64, error) {
	query := `INSERT INTO lectures (name, description, vector_db_collection_name, system_prompt, created_by) VALUES (?, ?, ?, ?, ?)`
	result, err := r.db.ExecContext(ctx, query, lecture.Name, lecture.Description, lecture.VectorDBCollectionName, lecture.SystemPrompt, lecture.CreatedBy)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

func (r *lectureRepository) EnrollUserInLecture(ctx context.Context, userID, lectureID int64, role string) error {
	query := `INSERT INTO user_lecture_enrollments (user_id, lecture_id, role) VALUES (?, ?, ?)`
	_, err := r.db.ExecContext(ctx, query, userID, lectureID, role)
	return err
}

func (r *lectureRepository) GetLecturesByUserID(ctx context.Context, userID int64) ([]model.Lecture, error) {
	var lectures []model.Lecture
	query := `SELECT l.* FROM lectures l JOIN user_lecture_enrollments ule ON l.id = ule.lecture_id WHERE ule.user_id = ?`
	err := r.db.SelectContext(ctx, &lectures, query, userID)
	return lectures, err
}
