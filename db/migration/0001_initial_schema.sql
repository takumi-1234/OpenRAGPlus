-- db/migration/0001_initial_schema.sql

-- データベースが存在しない場合に作成
-- CREATE DATABASE IF NOT EXISTS open_rag_db;
-- USE open_rag_db;

-- ユーザー情報を管理するテーブル
CREATE TABLE `users` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(255) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(255) NOT NULL COMMENT 'ローカル認証用のハッシュ化パスワード',
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 各講義の情報を管理するテーブル
CREATE TABLE `lectures` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `vector_db_collection_name` VARCHAR(255) NOT NULL UNIQUE COMMENT 'この講義に対応するChromaDBコレクション名',
    `system_prompt` TEXT COMMENT 'この講義専用のカスタムシステムプロンプト',
    `created_by` BIGINT NOT NULL COMMENT 'この講義を作成したユーザーID (教員など)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ユーザーと講義の履修関係を管理する中間テーブル
CREATE TABLE `user_lecture_enrollments` (
    `user_id` BIGINT,
    `lecture_id` BIGINT,
    `role` VARCHAR(50) DEFAULT 'student' COMMENT '役割 (例: student, instructor)',
    `enrolled_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`, `lecture_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`lecture_id`) REFERENCES `lectures`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- チャットのセッション（一連の会話）を管理するテーブル
CREATE TABLE `chat_sessions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `lecture_id` BIGINT NOT NULL,
    `title` VARCHAR(255) COMMENT 'チャットのタイトル (例: 最初の質問の要約など)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`lecture_id`) REFERENCES `lectures`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 個別の質問と回答を時系列で記録するテーブル
CREATE TABLE `chat_messages` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `session_id` BIGINT NOT NULL,
    `role` VARCHAR(50) NOT NULL COMMENT 'メッセージの役割 (user or assistant)',
    `content` TEXT NOT NULL,
    `retrieved_sources` JSON COMMENT 'RAGで参照したソースドキュメント情報',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `chat_sessions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;