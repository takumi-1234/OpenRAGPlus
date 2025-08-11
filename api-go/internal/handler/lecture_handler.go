package handler

import (
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/takumi-1234/OpenRAG/api-go/internal/middleware"
	"github.com/takumi-1234/OpenRAG/api-go/internal/model"
	"github.com/takumi-1234/OpenRAG/api-go/internal/service"
)

type LectureHandler struct {
	service *service.LectureService
}

func NewLectureHandler(service *service.LectureService) *LectureHandler {
	return &LectureHandler{service: service}
}

func (h *LectureHandler) CreateLecture(c *gin.Context) {
	var req model.CreateLectureRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// ★★★ middlewareパッケージを直接使用します ★★★
	userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	lecture, err := h.service.CreateLecture(c.Request.Context(), &req, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, lecture)
}

func (h *LectureHandler) GetLecturesByUserID(c *gin.Context) {
	// ★★★ middlewareパッケージを直接使用します ★★★
	userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	lectures, err := h.service.GetLecturesByUserID(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, lectures)
}

func (h *LectureHandler) EnrollInLecture(c *gin.Context) {
	lectureIDStr := c.Param("id")
	lectureID, err := strconv.ParseInt(lectureIDStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid lecture ID"})
		return
	}

	userID := c.MustGet(middleware.AuthorizationPayloadKey).(int64)

	err = h.service.EnrollInLecture(c.Request.Context(), userID, lectureID)
	if err != nil {
		if err.Error() == "enrollment limit (20) exceeded" {
			c.JSON(http.StatusForbidden, gin.H{"error": err.Error()})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Successfully enrolled in lecture"})
}

func (h *LectureHandler) DownloadDocument(c *gin.Context) {
	filename := c.Param("filename")
	if filename == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Filename is required"})
		return
	}

	// RAG PythonサービスのダウンロードURLを構築
	// これはdocker-compose.yml内のサービス名に依存します
	ragServiceURL := "http://rag-python:8000"
	downloadURL := fmt.Sprintf("%s/api/v1/download/%s", ragServiceURL, filename)

	// RAGサービスにリクエストをプロキシ
	req, err := http.NewRequestWithContext(c.Request.Context(), "GET", downloadURL, nil)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create download request"})
		return
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "Failed to download file from RAG service"})
		return
	}
	defer resp.Body.Close()

	// クライアントにファイルをストリーミング
	c.DataFromReader(resp.StatusCode, resp.ContentLength, resp.Header.Get("Content-Type"), resp.Body, nil)
}