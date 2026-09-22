# 加分项实现说明

本发布包已实现以下三个可验证部分：

1. 题目自动分类：关键词弱标注、字符级 TF-IDF 和 Rocchio 类中心分类；结果写回 `question.cat_id`，并把置信度保存到 `question_ai_classification`。
2. 重复题检测：标准化精确匹配与中文句向量余弦相似检索；结果保存到 `question_similarity`，完整集合同时导出为 CSV。
3. 答案一致性校验：检查答案合法性、空选项、判断题答案范围，以及完全重复或高度相似题之间的答案冲突。

## 运行方法

在项目根目录执行：

```powershell
python tools\analyze_question_bank.py --apply
```

只生成报告、不修改数据库时，省略 `--apply`：

```powershell
python tools\analyze_question_bank.py
```

报告输出在 `reports` 目录：

- `question_bank_analysis.md`：方法、结果、评估方法和标准参考文献。
- `classification_results.csv`：2309 道题的分类、置信度和复核标记。
- `exact_duplicate_groups.csv`：标准化后完全重复的题目集合。
- `similar_question_pairs.csv`：语义相似题对、相似度、否定差异和答案冲突。
- `answer_audit_issues.csv`：需要核实的答案问题。
- `analysis_summary.json`：便于程序读取的汇总指标。

## 参数

- `--threshold 0.88`：语义相似阈值，默认 0.88。
- `--neighbors 8`：每道题检查的近邻数量，默认 8。
- `--host`、`--port`、`--user`、`--password`、`--database`：MySQL 连接配置。

## 限制

自动分类和语义检测用于缩小人工审核范围。算法不会自动删除题目，也不会自动覆盖答案。“答案正确”必须结合现行官方法规和人工审核；当前实现只能发现数据内部不一致。
