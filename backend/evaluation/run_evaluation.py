"""RAG retrieval evaluation — Hard optional task ("Implement an evaluation of
your RAG system, using RAGAs or otherwise").

For each question in questions.json, runs the actual retrieval used in
production (rag_core.get_vectorstore().similarity_search) and checks whether
the expected source document appears in the Top-1 / Top-3 results. This
evaluates retrieval quality directly — the part of a RAG system most likely
to silently break (wrong chunking, bad embeddings, stale index) without
anyone noticing, since the LLM can often still produce a plausible-sounding
answer even from irrelevant context.

Usage:
    python -m evaluation.run_evaluation
"""

import json
import os
import time

from rag.rag_core import get_vectorstore

QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "questions.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")
TOP_K = 3


def _matches(source_path: str, expected_filename: str) -> bool:
    """Match by filename only — robust to Windows vs. POSIX path separators
    and to which subfolder (metrics/, frameworks/, sql/...) the doc lives in.
    """
    normalized = source_path.replace("\\", "/").rsplit("/", 1)[-1]
    return normalized.lower() == expected_filename.lower()


def run_evaluation(lang: str = "en") -> dict:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    db = get_vectorstore()
    rows = []
    top1_hits = 0
    top3_hits = 0
    latencies = []

    for item in questions:
        question = item["question"]
        expected = item["expected_document"]

        start = time.perf_counter()
        docs = db.similarity_search(question, k=TOP_K, filter={"lang": lang})
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

        retrieved = [d.metadata.get("source", "") for d in docs]
        retrieved_filenames = [r.replace("\\", "/").rsplit("/", 1)[-1] for r in retrieved]

        top1 = bool(retrieved) and _matches(retrieved[0], expected)
        top3 = any(_matches(r, expected) for r in retrieved)

        top1_hits += int(top1)
        top3_hits += int(top3)

        rows.append({
            "question": question,
            "expected_document": expected,
            "retrieved_top_k": retrieved_filenames,
            "top1_success": top1,
            "top3_success": top3,
            "latency_ms": round(latency_ms, 1),
        })

    n = len(questions)
    summary = {
        "total_questions": n,
        "top1_accuracy_pct": round(top1_hits / n * 100, 1) if n else 0,
        "top3_accuracy_pct": round(top3_hits / n * 100, 1) if n else 0,
        "avg_retrieval_ms": round(sum(latencies) / n, 1) if n else 0,
        "lang": lang,
    }

    result = {"summary": summary, "rows": rows}

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def print_report(result: dict) -> None:
    s = result["summary"]
    print(f"\nRAG Retrieval Evaluation — lang={s['lang']}")
    print(f"Questions:          {s['total_questions']}")
    print(f"Top-1 Accuracy:     {s['top1_accuracy_pct']}%")
    print(f"Top-3 Accuracy:     {s['top3_accuracy_pct']}%")
    print(f"Avg Retrieval Time: {s['avg_retrieval_ms']} ms\n")

    print(f"{'Question':<55} {'Expected':<25} {'Top-1':<6} {'Top-3':<6}")
    print("-" * 95)
    for row in result["rows"]:
        q = (row["question"][:52] + "...") if len(row["question"]) > 52 else row["question"]
        print(
            f"{q:<55} {row['expected_document']:<25} "
            f"{'✅' if row['top1_success'] else '❌':<6} {'✅' if row['top3_success'] else '❌':<6}"
        )


if __name__ == "__main__":
    result = run_evaluation()
    print_report(result)
