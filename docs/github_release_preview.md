# GitHub Release Boundary Preview

Status: the 42-file release candidate has passed local boundary review. No Git
repository has been created, and no files have been staged or published.

This document defines an explicit allowlist for the application-portfolio
version of the project. It does not claim that every file outside the
allowlist is unsafe. It prevents an accidental whole-directory upload and
records the locally reviewed publication boundary. Local approval does not
mean that these files have already been uploaded to GitHub.

## Publication principles

- Existing project files stay in their current locations.
- Local secrets, official source documents, reconstructable document text,
  embeddings, full retrieval rankings, and internal work notes remain local.
- Code may be public even when its runtime inputs are private, but the README
  must state those dependencies and side effects.
- Baseline, Gold data, embeddings, and experiment artifacts are preserved
  locally and are not rewritten for publication.
- Completed work, planned thesis work, and long-term research directions are
  labelled separately in the public README.

## Final reviewed public allowlist

The following 42 existing paths passed the local publication review. They form
the complete release candidate, but they have not been staged or published.

### Root and documentation

- `.gitignore`
- `README.md`
- `requirements.txt`
- `requirements-lock-py311.txt`
- `.env.example`
- `LICENSE`
- `NOTICE`
- `docs/github_release_preview.md`
- `docs/demo_examples.md`
- `docs/third_party_data_notice.md`
- `docs/THIRD_PARTY_NOTICES.md`

### Core implementation

- `scripts/1_extract_documents.py`
- `scripts/2_chunk_documents.py`
- `scripts/3_build_embeddings.py`
- `scripts/retrieve.py`
- `scripts/5_single_retrieve.py`
- `scripts/5_batch_retrieve.py`
- `scripts/5_generate_answer.py`
- `scripts/6_evaluate_qa.py`
- `scripts/7_score_evaluation.py`

### Token128 negative-experiment implementation

- `scripts/token128_common.py`
- `scripts/prepare_token128_experiment.py`
- `scripts/chunk_documents_token128.py`
- `scripts/build_embeddings_versioned.py`
- `scripts/evaluate_retrieval_versions.py`
- `configs/chunking/token128_clause_v1.json`
- `tests/test_token128_chunking.py`

### Reviewed evaluation summaries

- `data/evaluation/baseline_summary.md`
- `data/evaluation/evaluation_summary.json`
- `data/evaluation/evaluation_summary.xlsx`
- `data/evaluation/gold_issues_and_adjudication.md`
- `data/evaluation/error_analysis/error_analysis_report.md`
- `data/experiments/token128_clause_v1/evaluation/correct_regression_13.csv`
- `data/experiments/token128_clause_v1/evaluation/coverage_verification.json`
- `data/experiments/token128_clause_v1/evaluation/fact_comparison.csv`
- `data/experiments/token128_clause_v1/evaluation/final_report.md`
- `data/experiments/token128_clause_v1/evaluation/pair_comparison_15.csv`
- `data/experiments/token128_clause_v1/evaluation/posthoc_review_audit.json`
- `data/experiments/token128_clause_v1/evaluation/retrieval_comparison_30.csv`
- `data/experiments/token128_clause_v1/evaluation/retrieval_report.md`
- `data/experiments/token128_clause_v1/evaluation/retrieval_summary.json`
- `data/experiments/token128_clause_v1/evaluation/token_statistics.json`

## Files excluded from the current public allowlist

These files remain local and are not part of the 42-file release candidate.

- `configs/chunking/token128_evidence_targets_v1.json`: contains short
  verbatim source passages used to freeze evidence locations.
- `data/evaluation/qa_eval_set.jsonl`, `questions.jsonl`, and
  `manual_review_30.csv`: contain full row-level QA and review records outside
  the reviewed public-summary boundary.
- `data/evaluation/error_analysis/error_analysis_30.csv`: contains full
  answers, evidence descriptions, and diagnostic details that are not needed
  for the public error-analysis summary.
- `data/evaluation/error_analysis/diagnose_readonly.py`: despite its name,
  it creates audit JSON, copies prior reports, and renders PDF pages.
- `data/evaluation/error_analysis/diagnose_truncation.py`: writes diagnostic
  output and requires the private corpus, production embeddings, and local
  model cache.
- `data/experiments/token128_clause_v1/finalize_readonly_review.py`: writes
  post-run reports and integrity records inside the experiment directory.
- All files under `学校材料整理/`, `data/raw_docs/`,
  `data/processed/`, `出现问题/`, and `LLM모델선定이유/`.

## Script dependency and side-effect audit

No reviewed script contains a hard-coded user home path, Windows drive path,
API key, private name, or copied official document body. Paths are resolved
from the project root. This does not make every script safe to run against the
preserved local project.

| Script | Private or ignored runtime dependency | Side effect or external call |
| --- | --- | --- |
| `1_extract_documents.py` | `data/raw_docs/*.pdf` | Rewrites `data/processed/pages.jsonl` |
| `2_chunk_documents.py` | `data/processed/pages.jsonl` | Rewrites `data/processed/chunks.jsonl` |
| `3_build_embeddings.py` | Processed chunks and model cache/network | Rewrites production embedding and metadata files |
| `retrieve.py` | Processed chunks, production embedding, model cache/network | Read-only retrieval |
| `5_single_retrieve.py` | Same production data and model requirements | Read-only retrieval |
| `5_batch_retrieve.py` | Questions, chunks, embeddings, model cache/network | Rewrites `retrieval_results.jsonl` |
| `5_generate_answer.py` | Production retrieval data and local `.env` | Sends question and retrieved evidence to DashScope; paid API possible |
| `6_evaluate_qa.py` | QA set, production retrieval data, local `.env` | Sends evidence to DashScope and rewrites `evaluation_results.jsonl` |
| `7_score_evaluation.py` | Existing evaluation result JSONL | Rewrites score and summary outputs |
| `token128_common.py` | Exact ignored local model snapshot | Provides exclusive-create writers; no overwrite by design |
| `prepare_token128_experiment.py` | Processed pages, QA/analysis files, and ignored source catalog | Creates a new version directory and refuses overwrite |
| `chunk_documents_token128.py` | Processed pages, ignored source catalog, local tokenizer snapshot | Creates versioned chunks/audits and refuses overwrite |
| `build_embeddings_versioned.py` | Versioned chunks and local model snapshot | Creates versioned embeddings and refuses overwrite |
| `evaluate_retrieval_versions.py` | Private Baseline, labels, pages, old/new chunks and embeddings | Creates versioned comparison files and refuses overwrite |
| `test_token128_chunking.py` | Token128 config and exact local tokenizer snapshot | Uses temporary test files; no production write |

Important publication notes:

- The public repository will demonstrate the implementation but will not be
  self-contained until a lawful data-acquisition or sample-data procedure is
  documented.
- Scripts `1_extract_documents.py`, `2_chunk_documents.py`,
  `3_build_embeddings.py`, `5_batch_retrieve.py`,
  `6_evaluate_qa.py`, and `7_score_evaluation.py` use normal write mode and
  can replace preserved outputs if run locally.
- Answer generation and batch evaluation are not offline operations. They
  require a user-supplied `DASHSCOPE_API_KEY` and can incur API charges.
- The Token128 scripts are frozen evidence for a failed experiment. Their
  publication does not mean the generated index was adopted.

## Explicitly excluded from publication

The updated `.gitignore` excludes:

- real environment files and common private-key/credential files;
- Python environments, IDE state, model caches, and bytecode;
- official source PDFs/HTML/HWPX and the local source archive;
- extracted pages, chunks, production embeddings, and raw evaluation JSONL;
- Token128 embeddings, chunks, evidence targets, full rankings, logs, and
  internal integrity backups;
- internal Office documents, screenshots, temporary files, and the local
  environment tree.

## Local pre-publication gate

The current 42-file preview has been checked for the following conditions:

1. Every allowlisted path exists and is not ignored.
2. Representative nested experiment vectors, chunks, logs, and full rankings
   are ignored.
3. The exact release candidate has been scanned for secrets, personal paths,
   long third-party source passages, and unsuitable Office metadata.
4. `.env.example` contains a safe placeholder and is explicitly unignored;
   real environment variants remain ignored.
5. `LICENSE`, `NOTICE`, the third-party software notice, and the third-party
   data notice state the current licensing and publication boundaries.
6. Public QA material is limited to reviewed summaries, generated answers,
   short fact labels, and provenance metadata; source documents and
   reconstructable full text remain excluded.

These checks should be repeated immediately before any future staging action
because new or modified local files can change the release boundary.

No Git command that creates a repository, stages files, commits, or pushes is
authorized by this document.
