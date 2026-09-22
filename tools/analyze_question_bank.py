#!/usr/bin/env python3
"""Classify questions, detect duplicates, and audit answer consistency.

The implementation uses only the local MySQL database and a locally cached
Chinese sentence-embedding model. Run with --apply to persist category and
similarity results; omit --apply for a report-only dry run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pymysql
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize


MODEL_NAME = "shibing624/text2vec-base-chinese"
NEGATIONS = ("不", "不得", "不能", "禁止", "错误", "无需", "无须", "未", "否")

# Category definitions double as transparent weak labels. Each prototype is
# deliberately broader than its keywords so the TF-IDF centroid can generalize.
CATEGORIES = (
    {
        "name": "道路交通安全法律法规",
        "keywords": ("法律", "法规", "违法", "处罚", "罚款", "拘留", "记分", "扣分", "吊销", "刑事责任", "民事责任", "违法行为", "构成犯罪", "依法追究", "危险驾驶", "饮酒", "醉酒", "拼装", "报废", "扣留车辆"),
        "prototype": "道路交通安全法律法规 违法行为 处罚罚款 记分扣分 法律责任 刑事责任",
    },
    {
        "name": "驾驶证与机动车管理",
        "keywords": ("驾驶证", "行驶证", "准驾", "换证", "审验", "登记", "号牌", "实习期", "有效期", "车管所", "驾驶许可", "检验合格标志", "保险标志", "机动车检验"),
        "prototype": "驾驶证申领换证审验 准驾车型 实习期 机动车登记号牌 行驶证 车辆管理",
    },
    {
        "name": "道路通行规则",
        "keywords": ("车道", "超车", "会车", "让行", "路口", "高速公路", "限速", "掉头", "倒车", "变更车道", "跟车", "停车", "人行横道", "交叉路口"),
        "prototype": "道路通行规则 车道行驶 路口让行 超车会车 跟车限速 停车掉头 高速公路",
    },
    {
        "name": "交通信号与标志标线",
        "keywords": ("交通信号", "信号灯", "交通标志", "标线", "警告标志", "禁令标志", "指示标志", "路面标记", "交通警察手势", "图中标志", "这种标志"),
        "prototype": "交通信号灯 交通标志 标线 路面标记 交警手势 禁令警告指示标志",
    },
    {
        "name": "安全文明驾驶常识",
        "keywords": ("文明", "礼让", "行人", "儿童", "学校", "夜间", "雨天", "雾天", "冰雪", "疲劳", "安全距离", "恶劣天气", "眩目"),
        "prototype": "安全文明驾驶 礼让行人儿童 夜间雨雾冰雪天气 安全距离 疲劳驾驶",
    },
    {
        "name": "车辆结构与驾驶操作",
        "keywords": ("仪表", "指示灯", "发动机", "轮胎", "安全带", "安全气囊", "ABS", "制动器", "离合器", "方向盘", "踏板", "灯光", "点火开关", "操纵杆"),
        "prototype": "机动车结构仪表 指示灯 发动机轮胎 安全带气囊 制动离合 方向盘灯光驾驶操作",
    },
    {
        "name": "紧急情况与事故处理",
        "keywords": ("交通事故", "事故", "故障", "爆胎", "侧滑", "失控", "伤员", "急救", "报警", "逃逸", "碰撞", "起火", "自燃", "抢救"),
        "prototype": "交通事故处理 报警逃逸 车辆故障 爆胎侧滑碰撞起火 伤员急救抢救",
    },
    {
        "name": "其他与综合知识",
        "keywords": ("常识", "环保", "节能", "职业道德", "运输", "货物", "乘客"),
        "prototype": "驾驶综合知识 节能环保 职业道德 运输乘客货物 其他常识",
    },
)


@dataclass
class Question:
    q_id: int
    cat_id: int | None
    title: str
    image: str
    q_type: int
    options: tuple[str, str, str, str]
    answer: str

    @property
    def full_text(self) -> str:
        return "；".join((self.title, *[x for x in self.options if x]))

    @property
    def correct_option(self) -> str:
        index = ord(self.answer.upper()) - ord("A") if self.answer else -1
        return self.options[index] if 0 <= index < 4 else ""


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    return "".join(ch for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def signature(question: Question) -> str:
    # The image is part of the meaning. Two questions with identical wording
    # but different traffic-scene images are not exact duplicates.
    return "|".join(normalize_text(x) for x in (question.title, question.image, *question.options))


def keyword_scores(text: str) -> np.ndarray:
    normalized = normalize_text(text)
    scores = []
    for category in CATEGORIES:
        score = 0.0
        for keyword in category["keywords"]:
            if normalize_text(keyword) in normalized:
                score += 1.0 + min(len(keyword), 6) * 0.08
        scores.append(score)
    return np.asarray(scores, dtype=np.float32)


def classify(questions: list[Question]):
    titles = [q.title for q in questions]
    prototypes = [c["prototype"] for c in CATEGORIES]
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        min_df=2,
        max_features=45000,
        sublinear_tf=True,
        norm="l2",
    )
    combined = titles + prototypes
    matrix = vectorizer.fit_transform(combined)
    title_matrix = matrix[: len(titles)]
    prototype_matrix = matrix[len(titles) :]
    rules = np.vstack([keyword_scores(text) for text in titles])

    # High-margin keyword matches become pseudo-labelled examples. Their mean
    # TF-IDF vector forms a Rocchio-style class centroid; the written prototype
    # is always included so every category remains defined.
    centroids = []
    for category_index in range(len(CATEGORIES)):
        seed_indices = []
        for row_index, row in enumerate(rules):
            ordered = np.sort(row)
            margin = row[category_index] - ordered[-2] if len(ordered) > 1 else row[category_index]
            if row[category_index] >= 1.1 and row[category_index] == row.max() and margin >= 0.15:
                seed_indices.append(row_index)
        vectors = [prototype_matrix[category_index].toarray()[0]]
        if seed_indices:
            vectors.append(np.asarray(title_matrix[seed_indices].mean(axis=0))[0])
        centroid = normalize(np.asarray(vectors).sum(axis=0).reshape(1, -1)).astype(np.float32)
        centroids.append(centroid)

    centroid_matrix = np.vstack([c[0] for c in centroids]).T
    cosine_scores = np.asarray(title_matrix @ centroid_matrix)
    final_scores = cosine_scores + np.minimum(rules, 5.0) * 0.22
    chosen = final_scores.argmax(axis=1)

    results = []
    for index, category_index in enumerate(chosen):
        ordered = np.sort(final_scores[index])
        best = float(ordered[-1])
        second = float(ordered[-2])
        margin = best - second
        confidence = max(0.0, min(1.0, 0.48 + margin * 1.8 + min(best, 0.7) * 0.25))
        results.append(
            {
                "q_id": questions[index].q_id,
                "category": CATEGORIES[int(category_index)]["name"],
                "confidence": round(confidence, 4),
                "margin": round(margin, 4),
                "needs_review": confidence < 0.58,
            }
        )
    return results


def lexical_similarity(left: str, right: str) -> float:
    a, b = normalize_text(left), normalize_text(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def polarity(text: str) -> frozenset[str]:
    normalized = normalize_text(text)
    return frozenset(token for token in NEGATIONS if token in normalized)


def detect_duplicates(questions: list[Question], threshold: float, neighbors: int):
    exact_map: dict[str, list[Question]] = defaultdict(list)
    for question in questions:
        exact_map[signature(question)].append(question)
    exact_groups = [group for group in exact_map.values() if len(group) > 1]

    model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    texts = [q.full_text for q in questions]
    embeddings = model.encode(
        texts,
        batch_size=48,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype(np.float32)
    nearest = NearestNeighbors(
        n_neighbors=min(neighbors + 1, len(questions)),
        metric="cosine",
        algorithm="brute",
        n_jobs=-1,
    ).fit(embeddings)
    distances, indices = nearest.kneighbors(embeddings)

    seen: set[tuple[int, int]] = set()
    pairs = []
    for left_index, (row_distances, row_indices) in enumerate(zip(distances, indices)):
        for distance, right_index in zip(row_distances, row_indices):
            if int(right_index) == left_index:
                continue
            a, b = sorted((left_index, int(right_index)))
            if (a, b) in seen:
                continue
            seen.add((a, b))
            left, right = questions[a], questions[b]
            score = 1.0 - float(distance)
            if score < threshold or left.q_type != right.q_type:
                continue
            # Image-dependent questions are comparable only when the bound
            # image is the same. Otherwise identical text can ask about two
            # different road scenes and legitimately have different answers.
            if (left.image or right.image) and normalize_text(left.image) != normalize_text(right.image):
                continue
            lexical = lexical_similarity(left.full_text, right.full_text)
            exact = signature(left) == signature(right)
            polarity_difference = polarity(left.title) != polarity(right.title)
            same_options = all(
                normalize_text(a_option) == normalize_text(b_option)
                for a_option, b_option in zip(left.options, right.options)
            )
            answer_conflict = (
                bool(left.correct_option and right.correct_option)
                and normalize_text(left.correct_option) != normalize_text(right.correct_option)
                and score >= 0.97
                and lexical >= 0.90
                and same_options
            )
            if exact:
                level = "完全重复"
            elif score >= 0.96 or (score >= 0.93 and lexical >= 0.72):
                level = "高度疑似重复"
            else:
                level = "语义相似待复核"
            pairs.append(
                {
                    "q_id_a": left.q_id,
                    "q_id_b": right.q_id,
                    "semantic_similarity": round(score, 4),
                    "lexical_similarity": round(lexical, 4),
                    "level": level,
                    "polarity_difference": polarity_difference,
                    "answer_conflict": answer_conflict,
                    "title_a": left.title,
                    "title_b": right.title,
                    "answer_a": left.answer,
                    "answer_b": right.answer,
                    "correct_option_a": left.correct_option,
                    "correct_option_b": right.correct_option,
                }
            )
    pairs.sort(key=lambda row: row["semantic_similarity"], reverse=True)
    return exact_groups, pairs


def audit_answers(questions: list[Question], exact_groups, similar_pairs):
    issues = []
    for q in questions:
        answer = (q.answer or "").upper()
        if answer not in "ABCD":
            issues.append((q.q_id, "答案字母无效", q.title, answer, ""))
            continue
        option_index = ord(answer) - ord("A")
        if not q.options[option_index].strip():
            issues.append((q.q_id, "正确答案指向空选项", q.title, answer, ""))
        if q.q_type == 2 and answer not in "AB":
            issues.append((q.q_id, "判断题答案不是A/B", q.title, answer, ""))

    for group in exact_groups:
        answers = {normalize_text(q.correct_option) for q in group if q.correct_option}
        if len(answers) > 1:
            ids = ",".join(str(q.q_id) for q in group)
            for q in group:
                issues.append((q.q_id, "完全重复题答案冲突", q.title, q.answer, ids))

    for pair in similar_pairs:
        if pair["answer_conflict"]:
            issues.append(
                (
                    pair["q_id_a"],
                    "高度相似题答案内容冲突",
                    pair["title_a"],
                    pair["answer_a"],
                    str(pair["q_id_b"]),
                )
            )
    return issues


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fetch_questions(connection) -> list[Question]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT q_id, cat_id, title, q_type,
                   COALESCE(image,''),
                   COALESCE(option_a,''), COALESCE(option_b,''),
                   COALESCE(option_c,''), COALESCE(option_d,''),
                   COALESCE(answer,'')
            FROM question ORDER BY q_id
            """
        )
        return [
            Question(
                q_id=int(row[0]),
                cat_id=row[1],
                title=row[2] or "",
                q_type=int(row[3]),
                image=row[4] or "",
                options=(row[5], row[6], row[7], row[8]),
                answer=row[9] or "",
            )
            for row in cursor.fetchall()
        ]


def apply_results(connection, questions, classifications, similar_pairs):
    with connection.cursor() as cursor:
        for order, category in enumerate(CATEGORIES, start=1):
            cursor.execute(
                "INSERT INTO question_category(cat_name,sort) "
                "SELECT %s,%s WHERE NOT EXISTS "
                "(SELECT 1 FROM question_category WHERE cat_name=%s)",
                (category["name"], order * 10, category["name"]),
            )
        cursor.execute("SELECT cat_id,cat_name FROM question_category")
        category_ids = {name: cat_id for cat_id, name in cursor.fetchall()}

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_ai_classification (
                q_id BIGINT PRIMARY KEY,
                suggested_cat_id INT NOT NULL,
                confidence DECIMAL(6,4) NOT NULL,
                needs_review TINYINT NOT NULL DEFAULT 0,
                algorithm VARCHAR(100) NOT NULL,
                update_time DATETIME NOT NULL,
                INDEX idx_ai_cat(suggested_cat_id),
                INDEX idx_ai_review(needs_review)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_similarity (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                q_id_a BIGINT NOT NULL,
                q_id_b BIGINT NOT NULL,
                semantic_similarity DECIMAL(6,4) NOT NULL,
                lexical_similarity DECIMAL(6,4) NOT NULL,
                similarity_level VARCHAR(30) NOT NULL,
                polarity_difference TINYINT NOT NULL DEFAULT 0,
                answer_conflict TINYINT NOT NULL DEFAULT 0,
                update_time DATETIME NOT NULL,
                UNIQUE KEY uk_similarity_pair(q_id_a,q_id_b),
                INDEX idx_similarity_score(semantic_similarity),
                INDEX idx_similarity_conflict(answer_conflict)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

        now = datetime.now()
        classification_rows = []
        for result in classifications:
            cat_id = category_ids[result["category"]]
            classification_rows.append(
                (result["q_id"], cat_id, result["confidence"], int(result["needs_review"]), "TF-IDF+Rocchio弱监督分类", now)
            )
        cursor.executemany(
            """
            INSERT INTO question_ai_classification
                (q_id,suggested_cat_id,confidence,needs_review,algorithm,update_time)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                suggested_cat_id=VALUES(suggested_cat_id),
                confidence=VALUES(confidence), needs_review=VALUES(needs_review),
                algorithm=VALUES(algorithm), update_time=VALUES(update_time)
            """,
            classification_rows,
        )
        cursor.executemany(
            "UPDATE question SET cat_id=%s WHERE q_id=%s",
            [(category_ids[row["category"]], row["q_id"]) for row in classifications],
        )

        cursor.execute("DELETE FROM question_similarity")
        if similar_pairs:
            cursor.executemany(
                """
                INSERT INTO question_similarity
                    (q_id_a,q_id_b,semantic_similarity,lexical_similarity,
                     similarity_level,polarity_difference,answer_conflict,update_time)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    (
                        row["q_id_a"], row["q_id_b"], row["semantic_similarity"],
                        row["lexical_similarity"], row["level"],
                        int(row["polarity_difference"]), int(row["answer_conflict"]), now,
                    )
                    for row in similar_pairs
                ],
            )
    connection.commit()


def build_report(report_dir, questions, classifications, exact_groups, similar_pairs, answer_issues, applied):
    report_dir.mkdir(parents=True, exist_ok=True)
    question_by_id = {q.q_id: q for q in questions}
    classification_rows = [
        {
            **row,
            "title": question_by_id[row["q_id"]].title,
            "old_cat_id": question_by_id[row["q_id"]].cat_id,
        }
        for row in classifications
    ]
    write_csv(
        report_dir / "classification_results.csv",
        classification_rows,
        ("q_id", "title", "category", "confidence", "margin", "needs_review", "old_cat_id"),
    )
    write_csv(
        report_dir / "similar_question_pairs.csv",
        similar_pairs,
        (
            "q_id_a", "q_id_b", "semantic_similarity", "lexical_similarity", "level",
            "polarity_difference", "answer_conflict", "title_a", "title_b", "answer_a",
            "answer_b", "correct_option_a", "correct_option_b",
        ),
    )
    exact_rows = []
    for group_number, group in enumerate(exact_groups, start=1):
        for q in group:
            exact_rows.append(
                {"group": group_number, "q_id": q.q_id, "title": q.title, "image": q.image, "answer": q.answer, "correct_option": q.correct_option}
            )
    write_csv(report_dir / "exact_duplicate_groups.csv", exact_rows, ("group", "q_id", "title", "image", "answer", "correct_option"))
    issue_rows = [
        {"q_id": row[0], "issue": row[1], "title": row[2], "answer": row[3], "related_q_id": row[4]}
        for row in answer_issues
    ]
    write_csv(report_dir / "answer_audit_issues.csv", issue_rows, ("q_id", "issue", "title", "answer", "related_q_id"))

    distribution = Counter(row["category"] for row in classifications)
    level_counts = Counter(row["level"] for row in similar_pairs)
    review_count = sum(bool(row["needs_review"]) for row in classifications)
    conflict_count = sum(bool(row["answer_conflict"]) for row in similar_pairs)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "applied_to_database": applied,
        "question_count": len(questions),
        "category_distribution": dict(distribution),
        "classification_review_count": review_count,
        "exact_duplicate_group_count": len(exact_groups),
        "semantic_pair_count": len(similar_pairs),
        "similarity_level_counts": dict(level_counts),
        "answer_issue_count": len(answer_issues),
        "high_similarity_answer_conflicts": conflict_count,
        "model": MODEL_NAME,
    }
    (report_dir / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    category_lines = "\n".join(f"| {name} | {count} |" for name, count in distribution.most_common())
    report = f"""# 科目一题库智能分析报告

生成时间：{summary['generated_at']}<br>
题目总数：{len(questions)}<br>
数据库写入：{'已完成' if applied else '未执行（仅分析）'}

## 1. 自动分类结果

采用“关键词弱标注 + 字符级 TF-IDF + Rocchio 类中心余弦相似度”的可解释分类流程。关键词先产生高置信伪标签，再以伪标签样本的 TF-IDF 均值构造类别中心，最终结合类别中心相似度和关键词得分确定类别。置信度低于 0.58 的题目进入人工复核集合。

| 分类 | 题数 |
|---|---:|
{category_lines}

需要人工复核：**{review_count}** 道。逐题结果见 `classification_results.csv`。

## 2. 重复及语义相似检测

第一层对 Unicode、大小写、空白和标点进行归一化后比较“题干+全部选项”，识别完全重复。第二层使用本地 `text2vec-base-chinese` 模型生成 768 维句向量，用余弦相似度进行近邻搜索；仅比较相同题型，阈值为命令行配置值。报告同时保留字面相似度、否定词差异和答案冲突，供管理员复核。

- 完全重复组：**{len(exact_groups)}** 组
- 达到阈值的语义相似题对：**{len(similar_pairs)}** 对
- 高相似但答案内容冲突：**{conflict_count}** 对

详细集合见 `exact_duplicate_groups.csv` 和 `similar_question_pairs.csv`。

## 3. 答案一致性校验

已实现答案字母合法性、答案对应选项非空、判断题答案范围、完全重复题答案冲突、以及高相似题正确选项内容冲突检查，共发现 **{len(answer_issues)}** 条待核验记录，见 `answer_audit_issues.csv`。

该算法验证的是数据内部一致性，不能单独证明答案在法律意义上绝对正确。要形成可审计的正确答案，还需保存法规名称、条款、施行日期、来源链接和人工审核记录，并以现行官方法规为最终依据。

## 4. 评估与复核方式

1. 从每个分类随机抽取不少于 30 道题进行人工标注，计算准确率、宏平均 Precision、Recall 和 F1。
2. 对“高度疑似重复”全部复核，对“语义相似待复核”随机抽样，统计查准率。
3. 对答案冲突记录逐条查阅权威来源；确认前不自动删除题目或覆盖答案。
4. 人工修订后的类别可作为下一轮真实训练标签，替代弱标注并重复评估。

## 5. 参考文献（GB/T 7714）

[1] ROCCHIO J J. Relevance feedback in information retrieval[C]//SALTON G. The SMART Retrieval System: Experiments in Automatic Document Processing. Englewood Cliffs: Prentice-Hall, 1971: 313-323.

[2] MANNING C D, RAGHAVAN P, SCHÜTZE H. Introduction to Information Retrieval[M]. Cambridge: Cambridge University Press, 2008.

[3] DEVLIN J, CHANG M W, LEE K, et al. BERT: Pre-training of deep bidirectional transformers for language understanding[C]//Proceedings of NAACL-HLT. Minneapolis: Association for Computational Linguistics, 2019: 4171-4186. DOI:10.18653/v1/N19-1423.

[4] REIMERS N, GUREVYCH I. Sentence-BERT: Sentence embeddings using Siamese BERT-networks[C]//Proceedings of EMNLP-IJCNLP. Hong Kong: Association for Computational Linguistics, 2019: 3982-3992. DOI:10.18653/v1/D19-1410.

[5] GAO T, YAO X, CHEN D. SimCSE: Simple contrastive learning of sentence embeddings[C]//Proceedings of EMNLP. Association for Computational Linguistics, 2021: 6894-6910. DOI:10.18653/v1/2021.emnlp-main.552.

## 6. 实现对应关系

- 文献[1][2]：用于 TF-IDF 文本表示、类别中心构造和余弦相似分类。
- 文献[3]：作为预训练语言模型编码文本的理论基础。
- 文献[4][5]：用于句向量、对比学习和余弦语义相似检索方法设计；本实现采用兼容 SentenceTransformer 的中文 text2vec 模型落地。
"""
    (report_dir / "question_bank_analysis.md").write_text(report, encoding="utf-8")
    return summary


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=3306, type=int)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="123456")
    parser.add_argument("--database", default="driving_subject1")
    parser.add_argument("--threshold", default=0.88, type=float)
    parser.add_argument("--neighbors", default=8, type=int)
    parser.add_argument("--apply", action="store_true", help="write classifications and similarity pairs to MySQL")
    parser.add_argument("--report-dir", default=str(Path(__file__).resolve().parents[1] / "reports"))
    return parser.parse_args()


def main():
    args = parse_args()
    connection = pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        questions = fetch_questions(connection)
        if not questions:
            raise RuntimeError("No questions were found in the database.")
        print(f"Loaded {len(questions)} questions.")
        classifications = classify(questions)
        print("Classification complete; encoding semantic vectors...")
        exact_groups, similar_pairs = detect_duplicates(questions, args.threshold, args.neighbors)
        answer_issues = audit_answers(questions, exact_groups, similar_pairs)
        if args.apply:
            apply_results(connection, questions, classifications, similar_pairs)
            print("Database results committed.")
        summary = build_report(
            Path(args.report_dir), questions, classifications, exact_groups,
            similar_pairs, answer_issues, args.apply,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
