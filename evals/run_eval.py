"""Runs extraction over the synthetic dataset with two models (Claude Sonnet 5 and
Claude Haiku 4.5), computing per-field accuracy, valid-JSON-on-first-try rate, and
average cost/latency per document. Writes evals/results.json and evals/results.md."""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anthropic import Anthropic
from dotenv import load_dotenv

from doc_extraction.extraction import extract_document
from doc_extraction.schemas import DocumentType

load_dotenv()

DATASET_DIR = Path(__file__).parent / "dataset"

MODELS = {
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}


def _load_index() -> list[dict]:
    index_path = DATASET_DIR / "index.jsonl"
    return [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines()]


def _field_accuracy(expected: dict, actual: dict) -> tuple[int, int]:
    """Returns (correct_fields, total_fields), comparing each field with a small
    tolerance for floats and exact match otherwise."""
    correct = 0
    total = 0
    for key, exp_val in expected.items():
        total += 1
        act_val = actual.get(key) if actual else None
        if isinstance(exp_val, float) and isinstance(act_val, (int, float)):
            if abs(exp_val - act_val) <= 0.05:
                correct += 1
        elif exp_val == act_val:
            correct += 1
    return correct, total


def run(per_model_limit: int | None = None) -> dict:
    client = Anthropic()
    entries = _load_index()
    if per_model_limit:
        entries = entries[:per_model_limit]

    results_by_model: dict[str, list[dict]] = {m: [] for m in MODELS}

    for model_name, prices in MODELS.items():
        for entry in entries:
            doc_type = DocumentType(entry["document_type"])
            image_path = DATASET_DIR / entry["image_path"]
            label = json.loads((DATASET_DIR / entry["label_path"]).read_text(encoding="utf-8"))

            result = extract_document(image_path, doc_type, client=client, model=model_name)

            actual = result.validated.model_dump() if result.validated else result.raw_output
            correct, total = _field_accuracy(label, actual or {})
            cost = (
                result.input_tokens / 1_000_000 * prices["input"]
                + result.output_tokens / 1_000_000 * prices["output"]
            )

            results_by_model[model_name].append(
                {
                    "id": entry["id"],
                    "document_type": entry["document_type"],
                    "field_correct": correct,
                    "field_total": total,
                    "valid_on_first_try": result.valid_on_first_try,
                    "valid_final": result.validated is not None,
                    "latency_seconds": result.latency_seconds,
                    "cost_usd": cost,
                    "error": result.error,
                }
            )
            print(
                f"[{model_name}] {entry['id']}: "
                f"{correct}/{total} fields, "
                f"valid_first_try={result.valid_on_first_try}, "
                f"${cost:.4f}, {result.latency_seconds:.2f}s"
            )

    return results_by_model


def summarize(results_by_model: dict) -> dict:
    summary = {}
    for model_name, rows in results_by_model.items():
        field_acc = sum(r["field_correct"] for r in rows) / max(
            sum(r["field_total"] for r in rows), 1
        )
        valid_first = sum(r["valid_on_first_try"] for r in rows) / len(rows)
        valid_final = sum(r["valid_final"] for r in rows) / len(rows)
        avg_cost = statistics.mean(r["cost_usd"] for r in rows)
        avg_latency = statistics.mean(r["latency_seconds"] for r in rows)

        by_type: dict[str, list[dict]] = {}
        for r in rows:
            by_type.setdefault(r["document_type"], []).append(r)
        per_type_accuracy = {
            doc_type: sum(r["field_correct"] for r in type_rows)
            / max(sum(r["field_total"] for r in type_rows), 1)
            for doc_type, type_rows in by_type.items()
        }

        summary[model_name] = {
            "field_accuracy": field_acc,
            "valid_json_first_try_rate": valid_first,
            "valid_json_final_rate": valid_final,
            "avg_cost_usd": avg_cost,
            "avg_latency_seconds": avg_latency,
            "n_documents": len(rows),
            "per_type_field_accuracy": per_type_accuracy,
        }
    return summary


def write_report(summary: dict, output_dir: Path) -> None:
    lines = ["# Evaluation Results", ""]
    lines.append(
        "| Model | Field accuracy | Valid JSON (1st try) | Valid JSON (final) | "
        "Avg cost/doc | Avg latency/doc |"
    )
    lines.append("|---|---|---|---|---|---|")
    for model_name, s in summary.items():
        lines.append(
            f"| {model_name} | {s['field_accuracy']:.1%} | "
            f"{s['valid_json_first_try_rate']:.1%} | {s['valid_json_final_rate']:.1%} | "
            f"${s['avg_cost_usd']:.4f} | {s['avg_latency_seconds']:.2f}s |"
        )
    lines.append("")
    lines.append("## Field accuracy by document type")
    lines.append("")
    doc_types = sorted({dt for s in summary.values() for dt in s["per_type_field_accuracy"]})
    header = "| Model | " + " | ".join(doc_types) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(doc_types) + 1))
    for model_name, s in summary.items():
        row = [f"{s['per_type_field_accuracy'].get(dt, 0):.1%}" for dt in doc_types]
        lines.append(f"| {model_name} | " + " | ".join(row) + " |")

    (output_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raw_results = run()
    result_summary = summarize(raw_results)

    output_dir = Path(__file__).parent
    (output_dir / "results.json").write_text(
        json.dumps({"raw": raw_results, "summary": result_summary}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_report(result_summary, output_dir)

    print("\n=== Summary ===")
    print(json.dumps(result_summary, indent=2, ensure_ascii=False))
