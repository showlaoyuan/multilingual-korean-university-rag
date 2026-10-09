from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "evaluation_results.jsonl"
)

SCORES_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "evaluation_scores.jsonl"
)

SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "evaluation_summary.json"
)


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            records.append(
                json.loads(line)
            )

    return records


def normalize_list(value) -> list:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def get_retrieved_sources(
    retrieval_results: list[dict],
) -> list[str]:

    return [
        item.get("source_file")
        for item in retrieval_results
        if item.get("source_file")
    ]


def get_retrieved_chunks(
    retrieval_results: list[dict],
) -> list[str]:

    return [
        item.get("chunk_id")
        for item in retrieval_results
        if item.get("chunk_id")
    ]


def get_citation_sources(
    citations: list[dict],
) -> list[str]:

    return [
        item.get("source_file")
        for item in citations
        if item.get("source_file")
    ]


def get_citation_chunks(
    citations: list[dict],
) -> list[str]:

    return [
        item.get("chunk_id")
        for item in citations
        if item.get("chunk_id")
    ]


def any_overlap(
    gold_values: list,
    actual_values: list,
) -> bool:

    if not gold_values:
        return False

    gold_set = set(gold_values)
    actual_set = set(actual_values)

    return bool(
        gold_set & actual_set
    )


def score_record(
    record: dict,
) -> dict:

    gold_sources = normalize_list(
        record.get("gold_sources")
    )

    gold_pages = normalize_list(
        record.get("gold_pages")
    )

    gold_chunk_ids = normalize_list(
        record.get("gold_chunk_ids")
    )

    retrieval_results = (
        record.get(
            "retrieval_results",
            [],
        )
    )

    citations = (
        record.get(
            "citations",
            [],
        )
    )

    retrieved_sources = (
        get_retrieved_sources(
            retrieval_results
        )
    )

    retrieved_chunks = (
        get_retrieved_chunks(
            retrieval_results
        )
    )

    citation_sources = (
        get_citation_sources(
            citations
        )
    )

    citation_chunks = (
        get_citation_chunks(
            citations
        )
    )

    # -------------------------
    # Retrieval
    # -------------------------

    retrieval_source_hit = (
        any_overlap(
            gold_sources,
            retrieved_sources,
        )
    )

    if gold_chunk_ids:
        retrieval_chunk_hit = (
            any_overlap(
                gold_chunk_ids,
                retrieved_chunks,
            )
        )

    else:
        retrieval_chunk_hit = None

    # -------------------------
    # Citation
    # -------------------------

    citation_source_hit = (
        any_overlap(
            gold_sources,
            citation_sources,
        )
    )

    if gold_chunk_ids:
        citation_chunk_hit = (
            any_overlap(
                gold_chunk_ids,
                citation_chunks,
            )
        )

    else:
        citation_chunk_hit = None

    return {
        "question_id": (
            record.get("question_id")
        ),
        "pair_id": (
            record.get("pair_id")
        ),
        "question_language": (
            record.get(
                "question_language"
            )
        ),
        "question": (
            record.get("question")
        ),

        "supported": (
            record.get(
                "supported",
                False,
            )
        ),

        "system_answer": (
            record.get(
                "system_answer"
            )
        ),

        "gold_answer": (
            record.get(
                "gold_answer"
            )
        ),

        "gold_sources": (
            gold_sources
        ),

        "gold_pages": (
            gold_pages
        ),

        "gold_chunk_ids": (
            gold_chunk_ids
        ),

        "retrieval_source_hit": (
            retrieval_source_hit
        ),

        "retrieval_chunk_hit": (
            retrieval_chunk_hit
        ),

        "citation_source_hit": (
            citation_source_hit
        ),

        "citation_chunk_hit": (
            citation_chunk_hit
        ),

        # 后面人工填写
        "answer_label": None,
    }


def percent(
    numerator: int,
    denominator: int,
) -> float | None:

    if denominator == 0:
        return None

    return round(
        numerator
        / denominator
        * 100,
        2,
    )


def summarize(
    scored_records: list[dict],
) -> dict:

    total = len(scored_records)

    supported_count = sum(
        1
        for item in scored_records
        if item["supported"]
    )

    insufficient_count = (
        total - supported_count
    )

    retrieval_source_hits = sum(
        1
        for item in scored_records
        if item[
            "retrieval_source_hit"
        ]
    )

    retrieval_chunk_valid = [
        item
        for item in scored_records
        if item[
            "retrieval_chunk_hit"
        ] is not None
    ]

    retrieval_chunk_hits = sum(
        1
        for item in retrieval_chunk_valid
        if item[
            "retrieval_chunk_hit"
        ]
    )

    citation_source_hits = sum(
        1
        for item in scored_records
        if item[
            "citation_source_hit"
        ]
    )

    citation_chunk_valid = [
        item
        for item in scored_records
        if item[
            "citation_chunk_hit"
        ] is not None
    ]

    citation_chunk_hits = sum(
        1
        for item in citation_chunk_valid
        if item[
            "citation_chunk_hit"
        ]
    )

    language_stats = defaultdict(
        lambda: {
            "total": 0,
            "supported": 0,
            "retrieval_source_hit": 0,
            "citation_source_hit": 0,
        }
    )

    for item in scored_records:

        language = (
            item.get(
                "question_language"
            )
            or "unknown"
        )

        language_stats[
            language
        ]["total"] += 1

        if item["supported"]:
            language_stats[
                language
            ]["supported"] += 1

        if item[
            "retrieval_source_hit"
        ]:
            language_stats[
                language
            ][
                "retrieval_source_hit"
            ] += 1

        if item[
            "citation_source_hit"
        ]:
            language_stats[
                language
            ][
                "citation_source_hit"
            ] += 1

    formatted_language_stats = {}

    for language, stats in (
        language_stats.items()
    ):

        formatted_language_stats[
            language
        ] = {
            **stats,
            "supported_rate": percent(
                stats["supported"],
                stats["total"],
            ),
            "retrieval_source_hit_rate": (
                percent(
                    stats[
                        "retrieval_source_hit"
                    ],
                    stats["total"],
                )
            ),
            "citation_source_hit_rate": (
                percent(
                    stats[
                        "citation_source_hit"
                    ],
                    stats["total"],
                )
            ),
        }

    summary = {
        "total_questions": total,

        "supported_count": (
            supported_count
        ),

        "insufficient_count": (
            insufficient_count
        ),

        "supported_rate": (
            percent(
                supported_count,
                total,
            )
        ),

        "retrieval_source_hit_count": (
            retrieval_source_hits
        ),

        "retrieval_source_hit_at_5": (
            percent(
                retrieval_source_hits,
                total,
            )
        ),

        "retrieval_chunk_evaluable_count": (
            len(
                retrieval_chunk_valid
            )
        ),

        "retrieval_chunk_hit_count": (
            retrieval_chunk_hits
        ),

        "retrieval_chunk_hit_at_5": (
            percent(
                retrieval_chunk_hits,
                len(
                    retrieval_chunk_valid
                ),
            )
        ),

        "citation_source_hit_count": (
            citation_source_hits
        ),

        "citation_source_hit_rate": (
            percent(
                citation_source_hits,
                total,
            )
        ),

        "citation_chunk_evaluable_count": (
            len(
                citation_chunk_valid
            )
        ),

        "citation_chunk_hit_count": (
            citation_chunk_hits
        ),

        "citation_chunk_hit_rate": (
            percent(
                citation_chunk_hits,
                len(
                    citation_chunk_valid
                ),
            )
        ),

        "by_language": (
            formatted_language_stats
        ),
    }

    return summary


def main() -> None:

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation results not found: "
            f"{RESULTS_PATH}"
        )

    records = load_jsonl(
        RESULTS_PATH
    )

    print(
        f"Loaded {len(records)} "
        f"evaluation results."
    )

    scored_records = [
        score_record(record)
        for record in records
    ]

    with SCORES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        for record in scored_records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )

            file.write("\n")

    summary = summarize(
        scored_records
    )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 80)
    print("Evaluation Summary")
    print("=" * 80)

    print(
        f"Total questions: "
        f"{summary['total_questions']}"
    )

    print(
        f"Supported: "
        f"{summary['supported_count']}"
    )

    print(
        f"Insufficient: "
        f"{summary['insufficient_count']}"
    )

    print(
        f"Supported rate: "
        f"{summary['supported_rate']}%"
    )

    print()

    print(
        f"Retrieval Source Hit@5: "
        f"{summary['retrieval_source_hit_at_5']}%"
    )

    print(
        f"Retrieval Chunk Hit@5: "
        f"{summary['retrieval_chunk_hit_at_5']}%"
    )

    print()

    print(
        f"Citation Source Hit Rate: "
        f"{summary['citation_source_hit_rate']}%"
    )

    print(
        f"Citation Chunk Hit Rate: "
        f"{summary['citation_chunk_hit_rate']}%"
    )

    print()

    print("By language:")

    for language, stats in (
        summary[
            "by_language"
        ].items()
    ):

        print(
            f"  {language}: "
            f"total={stats['total']}, "
            f"supported="
            f"{stats['supported_rate']}%, "
            f"retrieval="
            f"{stats['retrieval_source_hit_rate']}%, "
            f"citation="
            f"{stats['citation_source_hit_rate']}%"
        )

    print()
    print(
        f"Scores saved to:\n"
        f"{SCORES_PATH}"
    )

    print()
    print(
        f"Summary saved to:\n"
        f"{SUMMARY_PATH}"
    )


if __name__ == "__main__":
    main()