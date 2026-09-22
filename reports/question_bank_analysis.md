# 科目一题库智能分析报告

生成时间：2026-09-10T23:55:31<br>
题目总数：2309<br>
数据库写入：已完成

## 1. 自动分类结果

采用“关键词弱标注 + 字符级 TF-IDF + Rocchio 类中心余弦相似度”的可解释分类流程。关键词先产生高置信伪标签，再以伪标签样本的 TF-IDF 均值构造类别中心，最终结合类别中心相似度和关键词得分确定类别。置信度低于 0.58 的题目进入人工复核集合。

| 分类 | 题数 |
|---|---:|
| 道路通行规则 | 633 |
| 交通信号与标志标线 | 434 |
| 驾驶证与机动车管理 | 382 |
| 道路交通安全法律法规 | 243 |
| 车辆结构与驾驶操作 | 216 |
| 紧急情况与事故处理 | 203 |
| 安全文明驾驶常识 | 169 |
| 其他与综合知识 | 29 |

需要人工复核：**717** 道。逐题结果见 `classification_results.csv`。

## 2. 重复及语义相似检测

第一层对 Unicode、大小写、空白和标点进行归一化后比较“题干+全部选项”，识别完全重复。第二层使用本地 `text2vec-base-chinese` 模型生成 768 维句向量，用余弦相似度进行近邻搜索；仅比较相同题型，阈值为命令行配置值。报告同时保留字面相似度、否定词差异和答案冲突，供管理员复核。

- 完全重复组：**42** 组
- 达到阈值的语义相似题对：**838** 对
- 高相似但答案内容冲突：**8** 对

详细集合见 `exact_duplicate_groups.csv` 和 `similar_question_pairs.csv`。

## 3. 答案一致性校验

已实现答案字母合法性、答案对应选项非空、判断题答案范围、完全重复题答案冲突、以及高相似题正确选项内容冲突检查，共发现 **8** 条待核验记录，见 `answer_audit_issues.csv`。

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
