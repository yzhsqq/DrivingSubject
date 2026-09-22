# 科目一题库系统 UML 图与 ER 图

本文档使用 Mermaid 绘图，可在支持 Mermaid 的 Markdown 编辑器、Typora、Obsidian 或 Mermaid Live Editor 中渲染，也可以截图放入答辩 PPT。

## 1. 系统用例图

```mermaid
flowchart LR
    U[用户]
    A[管理员]
    subgraph S[科目一题库系统]
      UC1((注册/登录))
      UC2((章节练习))
      UC3((模拟考试))
      UC4((提交试卷并查看成绩))
      UC5((查看错题本))
      UC6((使用 Dify 聊天助手))
      UC7((题目管理))
      UC8((用户管理))
      UC9((题目自动分类))
      UC10((重复题检测与审核))
    end
    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    A --> UC7
    A --> UC8
    A --> UC9
    A --> UC10
```

## 2. 提交试卷时序图

```mermaid
sequenceDiagram
    actor 用户
    participant 前端
    participant 考试接口
    participant 试卷服务
    participant 题目表
    participant 记录表

    用户->>前端: 选择试卷并提交答案
    前端->>考试接口: POST 答案和试卷编号
    考试接口->>试卷服务: 校验答案
    试卷服务->>题目表: 查询题目正确答案
    题目表-->>试卷服务: 返回标准答案
    试卷服务->>试卷服务: 计算得分和错题
    试卷服务->>记录表: 保存考试记录和答题明细
    记录表-->>试卷服务: 保存成功
    试卷服务-->>考试接口: 返回成绩、错题和解析
    考试接口-->>前端: 返回考试结果
    前端-->>用户: 展示成绩
```

## 3. 核心类图

```mermaid
classDiagram
    class User {
      +Long id
      +String username
      +login()
    }
    class Question {
      +Long id
      +String content
      +String answer
      +Long catId
    }
    class QuestionCategory {
      +Long id
      +String name
    }
    class ExamPaper {
      +Long id
      +String title
    }
    class UserExamRecord {
      +Long id
      +Long userId
      +Integer score
      +submit()
    }
    class UserAnswerDetail {
      +Long id
      +Long recordId
      +Long questionId
      +String userAnswer
      +Boolean correct
    }
    class UserWrongBook {
      +Long id
      +Long userId
      +Long questionId
    }
    class AiClassification {
      +Long questionId
      +String category
      +Double confidence
    }
    class QuestionSimilarity {
      +Long questionId
      +Long similarQuestionId
      +Double similarity
      +String matchType
    }

    QuestionCategory "1" --> "many" Question : 分类
    ExamPaper "many" --> "many" Question : 试卷题目
    User "1" --> "many" UserExamRecord : 参加考试
    UserExamRecord "1" --> "many" UserAnswerDetail : 包含答题
    Question "1" --> "many" UserAnswerDetail : 被作答
    User "1" --> "many" UserWrongBook : 维护错题
    Question "1" --> "many" UserWrongBook : 收录
    Question "1" --> "1" AiClassification : AI分类
    Question "1" --> "many" QuestionSimilarity : 相似题
```

## 4. 数据库 ER 图

```mermaid
erDiagram
    sys_user ||--o{ user_exam_record : "参加"
    user_exam_record ||--o{ user_answer_detail : "包含"
    exam_paper ||--o{ paper_question : "包含"
    question ||--o{ paper_question : "被收录"
    question_category ||--o{ question : "分类"
    question ||--o{ user_answer_detail : "被作答"
    sys_user ||--o{ user_wrong_book : "拥有"
    question ||--o{ user_wrong_book : "进入错题本"
    question ||--o| question_ai_classification : "AI分类结果"
    question ||--o{ question_similarity : "相似关系"

    sys_user {
      BIGINT id PK
      VARCHAR username
    }
    question_category {
      BIGINT id PK
      VARCHAR name
    }
    question {
      BIGINT id PK
      BIGINT cat_id FK
      TEXT content
      VARCHAR answer
    }
    exam_paper {
      BIGINT id PK
      VARCHAR title
    }
    paper_question {
      BIGINT paper_id FK
      BIGINT question_id FK
    }
    user_exam_record {
      BIGINT id PK
      BIGINT user_id FK
      INT score
    }
    user_answer_detail {
      BIGINT id PK
      BIGINT record_id FK
      BIGINT question_id FK
      VARCHAR user_answer
      BOOLEAN correct
    }
    user_wrong_book {
      BIGINT id PK
      BIGINT user_id FK
      BIGINT question_id FK
    }
    question_ai_classification {
      BIGINT id PK
      BIGINT question_id FK
      VARCHAR category
      DOUBLE confidence
    }
    question_similarity {
      BIGINT id PK
      BIGINT question_id FK
      BIGINT similar_question_id FK
      DOUBLE similarity
      VARCHAR match_type
    }
```

## 答辩说明

UML 图描述系统参与者、功能流程和程序对象；ER 图描述数据库实体、字段以及主键外键关系。`question_ai_classification` 保存 AI 分类结果，`question_similarity` 保存完全重复和语义相似题集合，这两张表属于题库智能分析模块。
