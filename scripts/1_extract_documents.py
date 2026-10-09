from __future__ import annotations

import json
from pathlib import Path

import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DOCS_DIR = PROJECT_ROOT / "data" / "raw_docs"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "pages.jsonl"


def clean_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def extract_pdf(pdf_path: Path) -> list[dict]:
    records = []

    with pymupdf.open(pdf_path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text", sort=True)
            text = clean_text(text)

            if not text:
                continue

            record = {
                "doc_id": pdf_path.stem,
                "source_file": pdf_path.name,
                "page_number": page_index + 1,
                "text": text,
            }

            records.append(record)

    return records


def main() -> None:
    pdf_files = sorted(RAW_DOCS_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {RAW_DOCS_DIR}")
        return

    all_records = []

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        records = extract_pdf(pdf_path)
        all_records.extend(records)

        print(f"  extracted pages: {len(records)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        for record in all_records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("Finished.")
    print(f"PDF files: {len(pdf_files)}")
    print(f"Extracted pages: {len(all_records)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()