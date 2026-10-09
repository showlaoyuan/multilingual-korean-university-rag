from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "pages.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            records.append(json.loads(line))

    return records


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def main() -> None:
    pages = load_jsonl(INPUT_PATH)

    all_chunks = []

    for page in pages:
        chunks = split_text(page["text"])

        for chunk_index, chunk_text in enumerate(chunks, start=1):
            record = {
                "chunk_id": (
                    f"{page['doc_id']}"
                    f"_p{page['page_number']}"
                    f"_c{chunk_index}"
                ),
                "doc_id": page["doc_id"],
                "source_file": page["source_file"],
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": chunk_text,
            }

            all_chunks.append(record)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        for record in all_chunks:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("Finished.")
    print(f"Input pages: {len(pages)}")
    print(f"Output chunks: {len(all_chunks)}")
    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Chunk overlap: {CHUNK_OVERLAP}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()