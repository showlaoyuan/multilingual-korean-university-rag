# Demo Examples from the Frozen Baseline

These examples are copied from the frozen 30-question baseline without editing the questions, system answers, citations, or human labels. They show two successful answers and one retrieval failure. The failure is included to make the current system boundary visible, not as a successful abstention case.

**Publication status:** passed local content, privacy, and third-party quotation review for the GitHub public allowlist. This file has not been staged or published.

## Q01-ZH — Chinese question

- **Language:** Chinese
- **Human label:** Correct
- **System support flag:** `true`

**Question (frozen)**

> 西江大学研究生外语考试什么时候可以参加？

**System answer (frozen)**

> 西江大学研究生外语考试每学期举行一次，分别在3月和9月进行。学生可以从各学位课程修读的第一个学期开始参加考试，但必须在学位论文审查之前通过考试。

**System citation (frozen)**

- Source: `sogang_02_exam_rules.pdf`
- Page: 3
- Chunk: `sogang_02_exam_rules_p3_c2`
- Evidence ID: `E5`

**Review note:** The answer includes both timing conditions required by the Gold answer. The additional March/September schedule is supported by the cited chunk.

## Q11-KO — Korean question

- **Language:** Korean
- **Human label:** Correct
- **System support flag:** `true`

**Question (frozen)**

> 이화여자대학교 대학원생은 졸업하려면 총 평균평점이 최소 얼마 이상이어야 하나요?

**System answer (frozen)**

> 梨花女子大学研究生院学生毕业时，总平均绩点必须至少为3.0以上。

**System citation (frozen)**

- Source: `ewha_01_grad_academic_guide.pdf`
- Page: 10
- Chunk: `ewha_01_grad_academic_guide_p10_c2`
- Evidence ID: `E3`

**Review note:** The answer correctly gives the minimum cumulative GPA as 3.0.

## Q05-KO — Refusal caused by retrieval failure

- **Language:** Korean
- **Human label:** Wrong
- **System support flag:** `false`

**Question (frozen)**

> 한국외국어대학교 외국인 유학생이 비자 연장을 신청할 때 어떤 서류가 필요한가요?

**System answer (frozen)**

> 无法从现有文档中确认。

**System citation (frozen)**

- None. The frozen record contains an empty `evidence_ids` list and no citations.

**Diagnostic reference, not a system citation**

- Target source: `hufs_03_visa_extension_guide.pdf`
- Page: 1
- Target chunk: `hufs_03_visa_extension_guide_p1_c1`
- School-filtered rank: 7, outside Top-K=5

**Review note:** This is a failed answer, not a successful safety example. The Korean query did not retrieve the visa-document chunk in the Top 5, so the system returned an insufficient-evidence response. The paired Chinese query retrieved the target and answered correctly, making this case useful for showing the cross-language retrieval gap.

## Privacy and Third-Party Content Check

- No names, student IDs, email addresses, phone numbers, API keys, or local user paths are included.
- No source-document passage is reproduced. The examples contain only frozen questions, generated answers, and source/page/chunk metadata.
- The cited university documents are third-party official materials and are not redistributed with this file.
- The examples remain subject to the same publication and attribution review as the other evaluation summaries.

