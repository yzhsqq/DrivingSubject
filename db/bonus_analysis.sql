-- 题库智能分析模块新增表
-- 数据库：driving_subject1
USE driving_subject1;

-- AI 自动分类结果
CREATE TABLE IF NOT EXISTS question_ai_classification (
  q_id BIGINT NOT NULL,
  suggested_cat_id INT NOT NULL,
  confidence DECIMAL(6,4) NOT NULL,
  needs_review TINYINT NOT NULL DEFAULT 0,
  algorithm VARCHAR(100) NOT NULL,
  update_time DATETIME NOT NULL,
  PRIMARY KEY (q_id),
  KEY idx_ai_cat (suggested_cat_id),
  KEY idx_ai_review (needs_review)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 题目完全重复/语义相似关系
CREATE TABLE IF NOT EXISTS question_similarity (
  id BIGINT NOT NULL AUTO_INCREMENT,
  q_id_a BIGINT NOT NULL,
  q_id_b BIGINT NOT NULL,
  semantic_similarity DECIMAL(6,4) NOT NULL,
  lexical_similarity DECIMAL(6,4) NOT NULL,
  similarity_level VARCHAR(30) NOT NULL,
  polarity_difference TINYINT NOT NULL DEFAULT 0,
  answer_conflict TINYINT NOT NULL DEFAULT 0,
  update_time DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_similarity_pair (q_id_a, q_id_b),
  KEY idx_similarity_score (semantic_similarity),
  KEY idx_similarity_conflict (answer_conflict)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 分类字典由原有 question_category 表保存，分析脚本负责写入分类结果。
