from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks.jsonl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "embeddings"
)

EMBEDDINGS_PATH = (
    OUTPUT_DIR
    / "chunk_embeddings.npy"
)

METADATA_PATH = (
    OUTPUT_DIR
    / "embedding_metadata.json"
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


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            records.append(json.loads(line))

    return records


def main() -> None:
    chunks = load_jsonl(INPUT_PATH)

    if not chunks:
        print("No chunks found.")
        return

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(
        MODEL_NAME,
        cache_folder=str(CACHE_DIR),
    )

    print(f"Encoding {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(
        EMBEDDINGS_PATH,
        embeddings,
    )

    metadata = {
        "model_name": MODEL_NAME,
        "chunk_count": len(chunks),
        "embedding_dimension": int(
            embeddings.shape[1]
        ),
        "normalized": True,
    }

    with METADATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Finished.")
    print(f"Chunks: {len(chunks)}")
    print(
        f"Embedding shape: "
        f"{embeddings.shape}"
    )
    print(
        f"Embeddings: "
        f"{EMBEDDINGS_PATH}"
    )
    print(
        f"Metadata: "
        f"{METADATA_PATH}"
    )
    print(
        f"Model cache: "
        f"{CACHE_DIR}"
    )


if __name__ == "__main__":
    main()