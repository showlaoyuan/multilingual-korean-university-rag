# token128_clause_v1 本地检索实验记录

本轮仅运行离线 Embedding 与 Retrieval，没有调用 LLM；以下不是回答正确率。旧生产代码、索引、Baseline、Gold、人工标签均保留。

## 实验口径

- 同一模型缓存快照、CPU、归一化向量、学校过滤、点积排序、Top-K=5。Before 须复现冻结 Top5，并逐题对照实际 retrieve.py。
- 切块目标112 tokens，硬上限128（含特殊符号和元数据）；元数据最多40 tokens。按条款边界，过长条款按句/行/分句拆分，再以token边界兜底；所有正文字符保留。
- 证据映射与程序/配置 SHA-256 在 After 前冻结，切块器不读QA。命中必须覆盖预登记原文区间的全部非空白字符；允许Top5多块联合覆盖，不用关键词或相似度代替事实支持。
- 目标事实 Hit@5以事实为分母；完整覆盖以全部目标事实为条件。排名为首个完整单块排名，同时保存最小联合覆盖前缀排名；两者不可混为一谈。
- Q03、Q04、Q10、Q15的中韩共8题缺乏已确认的研究生适用证据：保留原题并单列定位结果，有效命中为NA，不计入22题有效分母。Q14采用已审核的硕士24学分事实作诊断目标，原Gold不变。
- 适用范围匹配仅衡量文档层面的本科/研究生类别；不自动证明院系、入学年份、身份条件适用。证据中相应限制必须保留。

## Token与原文覆盖

|指标|Before|After|
|---|---:|---:|
|Chunk数|331|922|
|超128输入|253 (76.44%)|0 (0.00%)|
|最大输入tokens|312|128|
|中位数|198.0|90.0|

新Chunks对pages.jsonl的官方或不确定正文覆盖率为100%：116074字符；1988字符的明确归档说明另存archive_notes.jsonl。逐页区间、哈希和覆盖审计见chunking_audit.json及coverage_verification.json。该指标不证明原PDF提取完整，也不修复丢失的表格合并单元格结构。
共有103个原始文本单元因超过128上限被拆分，原文保留，跨页不猜测合并。特殊长条款可能需要多个检索位才能覆盖。

## 汇总

|范围|有效目标事实 Before→After|完整证据 Before→After|适用范围匹配Chunk Before→After|
|---|---|---|---|
|all|51/78 → 18/78|9/22 → 3/22|105/150 → 102/150|
|zh|31/39 → 10/39|6/11 → 2/11|52/75 → 50/75|
|ko|20/39 → 8/39|3/11 → 1/11|53/75 → 52/75|

学校匹配须全部通过。相似度仅写入逐事实明细作为辅助，不用于判断改善。

## 全30题 Before / After

事实列也显示范围待确认题的原文定位覆盖；这些题不算有效答案证据。

|题号|原评分|目标事实 Before→After|完整覆盖 Before→After|适用性|丢失事实|
|---|---|---|---|---|---|
|Q01-ZH|Correct|2/2 → 2/2|是 → 是|已映射范围|无|
|Q01-KO|Partial|2/2 → 2/2|是 → 是|已映射范围|无|
|Q02-ZH|Correct|1/4 → 1/4|否 → 否|已映射范围|无|
|Q02-KO|Partial|1/4 → 1/4|否 → 否|已映射范围|无|
|Q03-ZH|Wrong|0/1 → 0/1|否 → 否|待确认，NA|无|
|Q03-KO|Wrong|0/1 → 0/1|否 → 否|待确认，NA|无|
|Q04-ZH|Partial|1/1 → 1/1|是 → 是|待确认，NA|无|
|Q04-KO|Correct|0/1 → 1/1|否 → 是|待确认，NA|无|
|Q05-ZH|Correct|8/8 → 0/8|是 → 否|已映射范围|application,passport,registration,tb,enrollment,transcript,residence,fee|
|Q05-KO|Wrong|0/8 → 0/8|否 → 否|已映射范围|无|
|Q06-ZH|Correct|4/5 → 1/5|否 → 否|已映射范围|foreign_exception,masters,kflt|
|Q06-KO|Correct|4/5 → 1/5|否 → 否|已映射范围|foreign_exception,masters,kflt|
|Q07-ZH|Correct|1/1 → 1/1|是 → 是|已映射范围|无|
|Q07-KO|Wrong|0/1 → 0/1|否 → 否|已映射范围|无|
|Q08-ZH|Wrong|0/1 → 0/1|否 → 否|已映射范围|无|
|Q08-KO|Wrong|0/1 → 0/1|否 → 否|已映射范围|无|
|Q09-ZH|Correct|4/4 → 3/4|是 → 否|已映射范围|ethics|
|Q09-KO|Correct|4/4 → 3/4|是 → 否|已映射范围|ethics|
|Q10-ZH|Correct|1/1 → 1/1|是 → 是|待确认，NA|无|
|Q10-KO|Partial|1/1 → 0/1|是 → 否|待确认，NA|single_duration|
|Q11-ZH|Correct|1/1 → 0/1|是 → 否|已映射范围|gpa|
|Q11-KO|Correct|1/1 → 0/1|是 → 否|已映射范围|gpa|
|Q12-ZH|Partial|6/8 → 1/8|否 → 否|已映射范围|semesters,gpa,guidance,time,department,submission|
|Q12-KO|Partial|5/8 → 1/8|否 → 否|已映射范围|gpa,guidance,time,department,submission|
|Q13-ZH|Correct|4/4 → 1/4|是 → 否|已映射范围|global,entrance,alumni|
|Q13-KO|Partial|3/4 → 0/4|否 → 否|已映射范围|global,entrance,alumni|
|Q14-ZH|Wrong|0/1 → 0/1|否 → 否|已映射范围|无|
|Q14-KO|Wrong|0/1 → 0/1|否 → 否|已映射范围|无|
|Q15-ZH|Wrong|3/3 → 1/3|是 → 否|待确认，NA|discharged,upload|
|Q15-KO|Wrong|1/3 → 2/3|否 → 否|待确认，NA|无|

## Q03、Q05、Q08专项

Q03即使命中本科1门/1学分条款，也不能视为研究生问题修复。Q05按8项材料及预登记条件检查，避免只命中部分清单便判正确。Q08仅使用本科文件月份，不借研究生文件充当替代；2월 중/8월 중意为该月期间，不能自动解释为中旬。

### Q03-ZH

Top5事实覆盖 0/1 → 0/1；完整证据 否 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|本科原条款至少1门/1学分，仅作定位|7|72|否 → 否|

### Q03-KO

Top5事实覆盖 0/1 → 0/1；完整证据 否 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|本科原条款至少1门/1学分，仅作定位|13|72|否 → 否|

### Q05-ZH

Top5事实覆盖 8/8 → 0/8；完整证据 是 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|综合申请书|1|70|是 → 否|
|护照复印件|1|35|是 → 否|
|外国人登录证|1|145|是 → 否|
|结核证明及适用/重检条件|1|145|是 → 否|
|在学或结业证明|1|77|是 → 否|
|成绩证明|1|21|是 → 否|
|居住地证明或合同|1|249|是 → 否|
|手续费|1|14|是 → 否|

### Q05-KO

Top5事实覆盖 0/8 → 0/8；完整证据 否 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|综合申请书|7|40|否 → 否|
|护照复印件|7|29|否 → 否|
|外国人登录证|7|181|否 → 否|
|结核证明及适用/重检条件|7|181|否 → 否|
|在学或结业证明|7|67|否 → 否|
|成绩证明|7|21|否 → 否|
|居住地证明或合同|7|273|否 → 否|
|手续费|7|56|否 → 否|

### Q08-ZH

Top5事实覆盖 0/1 → 0/1；完整证据 否 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|本科选课2月/8月期间|54|164|否 → 否|

### Q08-KO

Top5事实覆盖 0/1 → 0/1；完整证据 否 → 否。

|事实|Before排名|After排名|Hit@5 Before→After|
|---|---|---|---|
|本科选课2月/8月期间|71|82|否 → 否|

## 原13条Correct回归检查

任何原已覆盖事实丢失即标记回归；即使同时增加其他事实，也不抵消。原Correct是历史人工回答评分，不保证其Gold或适用范围正确。

|题号|事实 Before→After|丢失事实|判定|
|---|---|---|---|
|Q01-ZH|2/2 → 2/2|无|未发现已映射事实丢失|
|Q02-ZH|1/4 → 1/4|无|未发现已映射事实丢失|
|Q04-KO|0/1 → 1/1|无|未发现已映射事实丢失|
|Q05-ZH|8/8 → 0/8|application,passport,registration,tb,enrollment,transcript,residence,fee|证据回归|
|Q06-ZH|4/5 → 1/5|foreign_exception,masters,kflt|证据回归|
|Q06-KO|4/5 → 1/5|foreign_exception,masters,kflt|证据回归|
|Q07-ZH|1/1 → 1/1|无|未发现已映射事实丢失|
|Q09-ZH|4/4 → 3/4|ethics|证据回归|
|Q09-KO|4/4 → 3/4|ethics|证据回归|
|Q10-ZH|1/1 → 1/1|无|未发现已映射事实丢失|
|Q11-ZH|1/1 → 0/1|gpa|证据回归|
|Q11-KO|1/1 → 0/1|gpa|证据回归|
|Q13-ZH|4/4 → 1/4|global,entrance,alumni|证据回归|

## 结论与限制

128-token静默截断已在新索引消除，正文覆盖审计通过。原Correct证据回归8题：Q05-ZH、Q06-ZH、Q06-KO、Q09-ZH、Q09-KO、Q11-ZH、Q11-KO、Q13-ZH。
本轮可证明工程上的长度约束是否满足；检索结论以以上事实覆盖和范围指标为准。缩短Chunk使长清单/跨段条件分散，元数据重复也可能影响排序；这些是本方案的取舍。仅有一组对照实验，不能把所有排序变化分别归因于某一项规则。
有回归或完整证据未改善时，不建议替换生产索引。即使指标改善，也需要后续人工证据复核，不能推断LLM回答和引用已经修复。
证据映射采用已冻结的明确原文位置，尚未登记的等价证据可能造成保守低估；After后不据此调整映射或规则。表格语义、Gold修订、研究生适用性和生成问题均不在本轮修复范围。
实验完成即停止，保留全部产物，等待审核；不切换生产代码/索引，不开展第二轮修复。

## 产物与运行命令

目录：`data/experiments/token128_clause_v1/`

evaluation/retrieval_comparison_30.csv：全30题；fact_comparison.csv：逐事实排名/相似度/命中；correct_regression_13.csv：13条回归；pair_comparison_15.csv：中韩差异；before_retrieval_30.jsonl与after_retrieval_30.jsonl：完整排序和原文；token_statistics.json：逐块长度；retrieval_summary.json：汇总。logs保存各阶段时间、参数与校验。

~~~powershell
.\.venv\Scripts\python.exe -B -X utf8 -m unittest discover -s tests -p test_token128_chunking.py -v
.\.venv\Scripts\python.exe -B -X utf8 scripts/prepare_token128_experiment.py --config configs/chunking/token128_clause_v1.json
.\.venv\Scripts\python.exe -B -X utf8 scripts/chunk_documents_token128.py --config configs/chunking/token128_clause_v1.json
.\.venv\Scripts\python.exe -B -X utf8 scripts/build_embeddings_versioned.py --version-dir data/experiments/token128_clause_v1
.\.venv\Scripts\python.exe -B -X utf8 scripts/evaluate_retrieval_versions.py --version-dir data/experiments/token128_clause_v1
~~~

上述命令记录本次流程。输出采用独占创建，已完成目录不可覆盖重跑；复现实验应另设版本目录并重新冻结配置。
