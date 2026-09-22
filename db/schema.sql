-- ============================================================
-- 科目一考试系统 建表脚本  (MySQL 8.0+ / 本机 9.0.1 已通过)
-- 库名 driving_subject1  字符集 utf8mb4，不使用外键，代码维护关联
-- ============================================================
CREATE DATABASE IF NOT EXISTS driving_subject1 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE driving_subject1;

-- 角色表
DROP TABLE IF EXISTS sys_role;
CREATE TABLE sys_role (
    role_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    role_name VARCHAR(30) NOT NULL COMMENT '角色名称',
    role_code VARCHAR(30) UNIQUE NOT NULL COMMENT '角色编码：STUDENT、QUESTION_ADMIN、SYS_ADMIN',
    description VARCHAR(200) COMMENT '角色描述'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 权限表
DROP TABLE IF EXISTS sys_permission;
CREATE TABLE sys_permission (
    perm_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
    perm_name VARCHAR(50) NOT NULL COMMENT '权限名称',
    perm_code VARCHAR(50) UNIQUE NOT NULL COMMENT '权限标识字符串'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 角色权限中间表，多对多
DROP TABLE IF EXISTS sys_role_perm;
CREATE TABLE sys_role_perm (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT '角色id',
    perm_id INT NOT NULL COMMENT '权限id',
    INDEX idx_roleid(role_id),
    INDEX idx_permid(perm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户表
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '登录账号',
    password VARCHAR(100) NOT NULL COMMENT 'BCrypt加密密码，不存明文',
    real_name VARCHAR(20) COMMENT '真实姓名',
    phone VARCHAR(11) COMMENT '手机号',
    role_id INT NOT NULL COMMENT '关联角色id',
    status TINYINT DEFAULT 1 COMMENT '0禁用，1启用',
    create_time DATETIME DEFAULT NOW() COMMENT '创建时间',
    last_login DATETIME NULL COMMENT '最后登录时间',
    INDEX idx_role(role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 题目分类表
DROP TABLE IF EXISTS question_category;
CREATE TABLE question_category (
    cat_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    cat_name VARCHAR(50) NOT NULL COMMENT '分类名称',
    sort INT DEFAULT 0 COMMENT '排序号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 科目一题目表
DROP TABLE IF EXISTS question;
CREATE TABLE question (
    q_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '题目ID',
    cat_id INT COMMENT '分类ID',
    title TEXT NOT NULL COMMENT '题干内容',
    image VARCHAR(1000) NULL COMMENT '题目配图文件名，多图用逗号分隔，对应 frontend/public/question-images/ 下文件',
    q_type TINYINT NOT NULL COMMENT '1单选，2判断',
    option_a VARCHAR(500) COMMENT 'A选项',
    option_b VARCHAR(500) COMMENT 'B选项',
    option_c VARCHAR(500) COMMENT 'C选项',
    option_d VARCHAR(500) COMMENT 'D选项',
    answer CHAR(1) COMMENT '正确答案 A/B/C/D',
    analysis TEXT COMMENT '题目解析',
    difficulty TINYINT DEFAULT 2 COMMENT '1简单 2中等 3困难',
    status TINYINT DEFAULT 1 COMMENT '0草稿，1已发布；草稿题目不能考试刷题',
    create_by BIGINT COMMENT '创建人user_id',
    create_time DATETIME DEFAULT NOW() COMMENT '创建时间',
    INDEX idx_cat(cat_id),
    INDEX idx_status(status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 模拟试卷表
DROP TABLE IF EXISTS exam_paper;
CREATE TABLE exam_paper (
    paper_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '试卷ID',
    paper_name VARCHAR(100) NOT NULL COMMENT '试卷名称',
    total_question INT DEFAULT 100 COMMENT '试卷总题目数量',
    pass_score INT DEFAULT 90 COMMENT '及格分数',
    time_limit INT DEFAULT 45 COMMENT '考试时长，单位分钟',
    status TINYINT DEFAULT 1 COMMENT '0禁用1启用',
    create_time DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 试卷和题目中间表：一张试卷包含多条题目
DROP TABLE IF EXISTS paper_question;
CREATE TABLE paper_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    paper_id BIGINT NOT NULL COMMENT '试卷ID',
    q_id BIGINT NOT NULL COMMENT '题目ID',
    sort_num INT DEFAULT 0 COMMENT '试卷内题目显示顺序',
    INDEX idx_paper(paper_id),
    INDEX idx_qid(q_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户考试总记录表：每一次模拟考试生成一条
DROP TABLE IF EXISTS user_exam_record;
CREATE TABLE user_exam_record (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '考试记录ID',
    user_id BIGINT NOT NULL COMMENT '考生user_id',
    paper_id BIGINT NOT NULL COMMENT '使用试卷id',
    start_time DATETIME NOT NULL COMMENT '考试开始时间',
    end_time DATETIME NULL COMMENT '交卷时间，交卷才赋值',
    total_score INT NULL COMMENT '考试得分',
    is_pass TINYINT NULL COMMENT '0未通过，1通过',
    status TINYINT DEFAULT 0 COMMENT '0未交卷，1已交卷',
    INDEX idx_user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户答题明细表：考试中每一道题作答记录
DROP TABLE IF EXISTS user_answer_detail;
CREATE TABLE user_answer_detail (
    detail_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    record_id BIGINT NOT NULL COMMENT '关联考试记录ID',
    q_id BIGINT NOT NULL COMMENT '作答题目ID',
    user_answer CHAR(1) COMMENT '用户选择答案A/B/C/D',
    is_right TINYINT COMMENT '0错误，1正确',
    INDEX idx_record(record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户错题本表，同一个用户同一道题仅一条记录
DROP TABLE IF EXISTS user_wrong_book;
CREATE TABLE user_wrong_book (
    wb_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '考生id',
    q_id BIGINT NOT NULL COMMENT '错题id',
    wrong_count INT DEFAULT 1 COMMENT '该题错误累计次数',
    add_time DATETIME DEFAULT NOW() COMMENT '加入错题本时间',
    UNIQUE uk_user_q(user_id,q_id),
    INDEX idx_user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户每题作答累计统计表：掌握每个用户对各题目的掌握情况。
-- 数据来源覆盖：模拟考试判分 / 刷题练习 / 错题本重做，统一在此累计作答与答对次数。
DROP TABLE IF EXISTS user_question_stat;
CREATE TABLE user_question_stat (
    stat_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '统计ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    q_id BIGINT NOT NULL COMMENT '题目ID',
    answer_count INT NOT NULL DEFAULT 0 COMMENT '累计作答次数',
    right_count INT NOT NULL DEFAULT 0 COMMENT '累计答对次数',
    last_answer TINYINT NULL COMMENT '最近一次对错：0错 1对',
    last_time DATETIME NULL COMMENT '最近作答时间',
    UNIQUE uk_user_q(user_id, q_id),
    INDEX idx_q(q_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 初始化基础角色数据
INSERT INTO sys_role(role_name,role_code,description) VALUES
('考生','STUDENT','刷题、模拟考试、查看个人成绩错题'),
('题库管理员','QUESTION_ADMIN','维护题库分类、题目增删改查导入导出，不能操作用户管理'),
('系统管理员','SYS_ADMIN','系统全部权限，用户角色题库统计');
