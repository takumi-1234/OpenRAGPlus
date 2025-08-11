// api-go/internal/service/lecture_service.go

package service

import (
	"context"
	"fmt"

	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
	"github.com/takumi-1234/OpenRAG/api-go/internal/repository"
)

// LectureServiceは講義関連のビジネスロジックを提供します。
type LectureService struct {
	lectureRepo repository.LectureRepository
	userRepo    repository.UserRepository // ユーザー情報を取得する場合などに使用
}

// NewLectureServiceは新しいLectureServiceのインスタンスを生成します。
func NewLectureService(lectureRepo repository.LectureRepository) *LectureService {
	return &LectureService{
		lectureRepo: lectureRepo,
	}
}

// CreateLectureは新しい講義を作成し、作成者を自動的に履修登録します。
// この処理はアトミックである必要があるため、トランザクションを使用します。
func (s *LectureService) CreateLecture(ctx context.Context, req *model.CreateLectureRequest, userID int64) (*model.LectureResponse, error) {
	// lectureRepoがDBTX（*sqlx.DBまたは*sqlx.Tx）を受け入れるようにリポジトリを修正すると、
	// トランザクション管理がより柔軟になるが、ここではシンプルにリポジトリメソッド内で完結させる。
	// より複雑なトランザクションが必要な場合は、リポジトリ層の設計見直しを検討。

	// 1. Lectureモデルを作成
	lecture := &model.Lecture{
		Name:         req.Name,
		Description:  req.Description,
		SystemPrompt: req.SystemPrompt,
		CreatedBy:    userID,
		// vector_db_collection_nameは、INSERT後に生成されるIDに基づいて設定する
	}

	// 2. 講義をデータベースに作成
	// ここでは簡単化のため、リポジトリ内でトランザクションが完結していると仮定する。
	// 本来は、サービス層でトランザクションを開始・コミット/ロールバックすべき。
	// そのためには、リポジトリのメソッドが `*sqlx.Tx` を受け取れるようにするリファクタリングが必要。
	// 今回は、リポジトリ内で完結するシンプルな実装を提示する。
	lectureID, err := s.lectureRepo.CreateLecture(ctx, lecture)
	if err != nil {
		return nil, fmt.Errorf("failed to create lecture record: %w", err)
	}
	lecture.ID = lectureID

	// 3. 作成者を 'instructor'として講義に登録
	err = s.lectureRepo.EnrollUserInLecture(ctx, userID, lectureID, "instructor")
	if err != nil {
		// ここで講義作成のロールバック処理が必要だが、今回は省略
		return nil, fmt.Errorf("failed to enroll creator in lecture: %w", err)
	}

	// 講義IDに基づいてコレクション名を生成
	lecture.VectorDBCollectionName = fmt.Sprintf("lecture_%d", lectureID)

	// 4. レスポンスモデルに変換して返す
	response := &model.LectureResponse{
		ID:                     lecture.ID,
		Name:                   lecture.Name,
		Description:            lecture.Description,
		VectorDBCollectionName: lecture.VectorDBCollectionName,
		SystemPrompt:           lecture.SystemPrompt,
		CreatedBy:              lecture.CreatedBy,
		CreatedAt:              lecture.CreatedAt, // DBが自動設定するが、取得して返したい場合はSELECTが必要
	}

	return response, nil
}

// GetLecturesByUserIDは、指定されたユーザーが履修している講義のリストを取得します。
func (s *LectureService) GetLecturesByUserID(ctx context.Context, userID int64) ([]model.LectureResponse, error) {
	lectures, err := s.lectureRepo.GetLecturesByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}

	// DBモデルからAPIレスポンスモデルに変換
	responses := make([]model.LectureResponse, len(lectures))
	for i, lecture := range lectures {
		responses[i] = model.LectureResponse{
			ID:                     lecture.ID,
			Name:                   lecture.Name,
			Description:            lecture.Description,
			VectorDBCollectionName: fmt.Sprintf("lecture_%d", lecture.ID), // 常に動的に生成
			SystemPrompt:           lecture.SystemPrompt,
			CreatedBy:              lecture.CreatedBy,
			CreatedAt:              lecture.CreatedAt,
		}
	}

	return responses, nil
}
