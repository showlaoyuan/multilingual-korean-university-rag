from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.jsonl"
)

EMBEDDINGS_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
    / "chunk_embeddings.npy"
)

CACHE_DIR = (
    PROJECT_ROOT
    / ".cache"
    / "sentence_transformers"
)

MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K = 5


SCHOOL_ALIASES = {
    "汉阳大学": "hanyang_",
    "한양대학교": "hanyang_",

    "延世大学": "yonsei_",
    "연세대학교": "yonsei_",

    "梨花女子大学": "ewha_",
    "이화여자대학교": "ewha_",

    "西江大学": "sogang_",
    "서강대학교": "sogang_",

    "韩国外国语大学": "hufs_",
    "한국외국어대학교": "hufs_",
}


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            records.append(json.loads(line))

    return records


def retrieve(
    query: str,
    top_k: int = TOP_K,
) -> list[dict]:

    if not query.strip():
        return []

    chunks = load_jsonl(CHUNKS_PATH)

    embeddings = np.load(
        EMBEDDINGS_PATH
    )

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Chunk count and embedding count do not match."
        )

    model = SentenceTransformer(
        MODEL_NAME,
        cache_folder=str(CACHE_DIR),
    )

    school_prefix = None

    for school_name, prefix in SCHOOL_ALIASES.items():
        if school_name in query:
            school_prefix = prefix
            break

    if school_prefix:
        filtered_indices = [
            i
            for i, chunk in enumerate(chunks)
            if chunk["source_file"].startswith(
                school_prefix
            )
        ]

        filtered_chunks = [
            chunks[i]
            for i in filtered_indices
        ]

        filtered_embeddings = embeddings[
            filtered_indices
        ]

    else:
        filtered_chunks = chunks
        filtered_embeddings = embeddings

    if not filtered_chunks:
        return []

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]

    scores = (
        filtered_embeddings
        @ query_embedding
    )

    top_indices = np.argsort(
        scores
    )[::-1][:top_k]

    results = []

    for rank, index in enumerate(
        top_indices,
        start=1,
    ):
        chunk = filtered_chunks[index]
        score = float(scores[index])

        result = {
            "rank": rank,
            "score": score,
            "source_file": chunk[
                "source_file"
            ],
            "page_number": chunk[
                "page_number"
            ],
            "chunk_id": chunk[
                "chunk_id"
            ],
            "text": chunk[
                "text"
            ],
        }

        results.append(result)

    return results


def main() -> None:
    query = input(
        "Enter your question: "
    ).strip()

    if not query:
        print("Question is empty.")
        return

    results = retrieve(
        query=query,
        top_k=TOP_K,
    )

    print()
    print(f"Question: {query}")
    print()
    print(f"Top {len(results)} results:")
    print("=" * 80)

    for result in results:
        print()
        print(
            f"Rank: {result['rank']}"
        )
        print(
            f"Score: "
            f"{result['score']:.4f}"
        )
        print(
            f"Source: "
            f"{result['source_file']}"
        )
        print(
            f"Page: "
            f"{result['page_number']}"
        )
        print(
            f"Chunk ID: "
            f"{result['chunk_id']}"
        )
        print()
        print(result["text"])
        print()
        print("-" * 80)


if __name__ == "__main__":
    main()