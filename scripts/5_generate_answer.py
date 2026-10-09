from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from retrieve import retrieve


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TOP_K = 5

BASE_URL = (
    "https://dashscope.aliyuncs.com/"
    "compatible-mode/v1"
)

MODEL = "qwen3.7-plus"


SYSTEM_PROMPT = """
你是一个韩国高校行政文档问答助手。

你只能根据提供给你的参考证据回答问题。
不能使用参考证据之外的知识、常识、推测或模型记忆。

必须遵守以下规则：

1. 使用中文回答。
2. 必须准确保留原文中的条件、时间、数字、否定关系和限制条件。
3. 不允许编造学校规定。
4. 不允许自行编造来源、页码、文件名或 Chunk ID。
5. 每条参考证据都有 Evidence ID，例如 E1、E2。
6. evidence_ids 中只能填写真正支持最终回答内容的 Evidence ID。
7. 不要因为某条证据排名更高就优先使用它，应根据证据内容判断。
8. 可以同时使用多个 Evidence。
9. 如果现有证据不足以确认问题的答案，必须回答：
   “无法从现有文档中确认。”
10. 如果无法确认：
    supported 必须为 false；
    evidence_ids 必须为空数组。

你必须只返回一个合法 JSON 对象。

格式如下：

{
  "supported": true,
  "answer": "最终中文回答",
  "evidence_ids": ["E1", "E2"]
}

不要输出 Markdown。
不要输出 ```json。
不要在 JSON 前后添加解释。
"""


def build_context(
    results: list[dict],
) -> str:

    context_blocks = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        evidence_id = f"E{index}"

        block = (
            f"[{evidence_id}]\n"
            f"Source: {result['source_file']}\n"
            f"Page: {result['page_number']}\n"
            f"Chunk ID: {result['chunk_id']}\n"
            f"Text:\n"
            f"{result['text']}"
        )

        context_blocks.append(block)

    return "\n\n".join(context_blocks)


def clean_json_response(
    raw_answer: str,
) -> str:

    cleaned = raw_answer.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]

    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def generate_answer(
    question: str,
    context: str,
) -> dict:

    load_dotenv(
        PROJECT_ROOT / ".env"
    )

    api_key = os.getenv(
        "DASHSCOPE_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "DASHSCOPE_API_KEY was not found "
            "in the project .env file."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
    )

    user_prompt = (
        f"问题：\n"
        f"{question}\n\n"
        f"参考证据：\n"
        f"{context}"
    )

    response = (
        client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            max_tokens=800,
            extra_body={
                "enable_thinking": False
            },
        )
    )

    raw_answer = (
        response
        .choices[0]
        .message
        .content
    )

    if not raw_answer:
        raise ValueError(
            "The model returned an empty answer."
        )

    cleaned_answer = clean_json_response(
        raw_answer
    )

    try:
        answer_data = json.loads(
            cleaned_answer
        )

    except json.JSONDecodeError as error:
        print()
        print("Raw model output:")
        print(raw_answer)

        raise ValueError(
            "The model output is not valid JSON."
        ) from error

    return answer_data


def build_citations(
    answer_data: dict,
    results: list[dict],
) -> list[dict]:

    citations = []

    valid_evidence = {
        f"E{index}": result
        for index, result in enumerate(
            results,
            start=1,
        )
    }

    evidence_ids = answer_data.get(
        "evidence_ids",
        [],
    )

    for evidence_id in evidence_ids:

        if evidence_id not in valid_evidence:
            print(
                f"[Warning] Invalid evidence ID "
                f"returned by model: "
                f"{evidence_id}"
            )

            continue

        result = valid_evidence[
            evidence_id
        ]

        citation = {
            "evidence_id": evidence_id,
            "source_file": (
                result["source_file"]
            ),
            "page_number": (
                result["page_number"]
            ),
            "chunk_id": (
                result["chunk_id"]
            ),
        }

        citations.append(
            citation
        )

    return citations


def main() -> None:

    question = input(
        "Enter your question: "
    ).strip()

    if not question:
        print(
            "Question is empty."
        )
        return

    print()
    print(
        "Retrieving evidence..."
    )

    results = retrieve(
        query=question,
        top_k=TOP_K,
    )

    if not results:
        print()
        print(
            "无法从现有文档中确认。"
        )
        return

    context = build_context(
        results
    )

    print(
        f"Retrieved "
        f"{len(results)} evidence chunks."
    )

    print()
    print(
        f"Generating answer "
        f"with {MODEL}..."
    )

    try:
        answer_data = generate_answer(
            question=question,
            context=context,
        )

    except Exception as error:
        print()
        print(
            "Answer generation failed:"
        )
        print(
            f"{type(error).__name__}: "
            f"{error}"
        )
        return

    supported = answer_data.get(
        "supported",
        False,
    )

    answer = answer_data.get(
        "answer",
        "无法从现有文档中确认。",
    )

    evidence_ids = answer_data.get(
        "evidence_ids",
        [],
    )

    if not isinstance(
        supported,
        bool,
    ):
        print()
        print(
            "[Warning] Invalid supported field."
        )
        supported = False

    if not isinstance(
        evidence_ids,
        list,
    ):
        print()
        print(
            "[Warning] Invalid evidence_ids field."
        )
        evidence_ids = []

    print()
    print(
        "=" * 80
    )
    print(
        "Answer"
    )
    print(
        "=" * 80
    )
    print()
    print(
        answer
    )

    if not supported:
        print()
        print(
            "Evidence status: "
            "INSUFFICIENT"
        )
        return

    citations = build_citations(
        answer_data=answer_data,
        results=results,
    )

    if not citations:
        print()
        print(
            "[Warning] "
            "The answer was marked as supported, "
            "but no valid citation was returned."
        )
        return

    print()
    print(
        "=" * 80
    )
    print(
        "Citations"
    )
    print(
        "=" * 80
    )

    for citation in citations:
        print()

        print(
            f"[{citation['evidence_id']}]"
        )

        print(
            f"Source: "
            f"{citation['source_file']}"
        )

        print(
            f"Page: "
            f"{citation['page_number']}"
        )

        print(
            f"Chunk ID: "
            f"{citation['chunk_id']}"
        )


if __name__ == "__main__":
    main()