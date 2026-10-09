# Static RAG Baseline：30 QA 人工评分统计

**状态：2026-10-09 人工评分已覆盖30条；Q04/Q15研究生适用性仍待原始官方资料核实。**

## 1. 统计表（基于当前30条评分标签）

| 分组 | 样本数 | Correct | Partial | Wrong | Strict Accuracy (Correct/N) | Partial率 | Wrong率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 全体 | 30 | 13 | 7 | 10 | 43.33% | 23.33% | 33.33% |
| 中文问句 ZH | 15 | 9 | 2 | 4 | 60.00% | 13.33% | 26.67% |
| 韩文问句 KO | 15 | 4 | 5 | 6 | 26.67% | 33.33% | 40.00% |

**口径：** Strict Accuracy = Correct / 该组样本数；Partial 不计为 Correct。此处的人工答案准确率不同于原脚本 `supported=true` 的 Supported Rate，也不同于检索/引用命中率。

## 2. 逐题标签（按测试顺序）

| ID | 标签 | ID | 标签 |
|---|---|---|---|
| Q01-ZH | Correct | Q01-KO | Partial |
| Q02-ZH | Correct | Q02-KO | Partial |
| Q03-ZH | Wrong | Q03-KO | Wrong |
| Q04-ZH | Partial | Q04-KO | Correct |
| Q05-ZH | Correct | Q05-KO | Wrong |
| Q06-ZH | Correct | Q06-KO | Correct |
| Q07-ZH | Correct | Q07-KO | Wrong |
| Q08-ZH | Wrong | Q08-KO | Wrong |
| Q09-ZH | Correct | Q09-KO | Correct |
| Q10-ZH | Correct | Q10-KO | Partial |
| Q11-ZH | Correct | Q11-KO | Correct |
| Q12-ZH | Partial | Q12-KO | Partial |
| Q13-ZH | Correct | Q13-KO | Partial |
| Q14-ZH | Wrong | Q14-KO | Wrong |
| Q15-ZH | Wrong | Q15-KO | Wrong |

## 3. 现有自动指标（来自此前手工提供的运行汇总，**不从此次jsonl重新计算**）

| 指标 | 旧运行汇总值 |
|---|---:|
| Supported Rate | 76.67% |
| Retrieval Source Hit@5 | 86.67% |
| Retrieval Chunk Hit@5 | 76.92% |
| Citation Source Hit Rate | 73.33% |
| Citation Chunk Hit Rate | 73.08% |
| ZH Retrieval Source Hit@5 | 93.33% |
| KO Retrieval Source Hit@5 | 80.00% |
| ZH Citation Source Hit Rate | 80.00% |
| KO Citation Source Hit Rate | 66.67% |

**注意：** 自动指标与人工准确率不应互相替代；正式论文引用自动数值前需用对应脚本的原始输出再核对。

## 4. 质量与限制

- Q14-ZH / Q14-KO：原始表格证明此前 Gold 错置了硕士和博士学分。原始预测与Gold均保持冻结；修订答案单列在 `gold_issues_and_adjudication.md`。
- Q04-ZH / Q04-KO / Q15-ZH / Q15-KO：用于评分的汉阳复学指南注明本科范围，研究生仅提示咨询行政团队，需确认研究生适用性。当前人工标签属**临时基线标签**，正式发布可做经裁决的敏感性分析。
- Q08-ZH：韩文原文 `2월 중/8월 중` 是“2月期间/8月期间”，非特指“中旬”。
- 上述评分是单人辅助人工判断而非独立多评审一致性评分；正式论文应描述人工复核程序。
