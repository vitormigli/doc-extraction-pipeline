"""Builds a synthetic dataset: renders N documents per type, saves images and
ground-truth JSON, and writes an index.jsonl describing the whole dataset."""

import json
from pathlib import Path

from doc_extraction.generator.documents import generate_document
from doc_extraction.schemas import DocumentType


def build_dataset(output_dir: Path, per_type: int = 15) -> list[dict]:
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    index: list[dict] = []
    seed = 1000

    for doc_type in DocumentType:
        for i in range(per_type):
            seed += 1
            data, img = generate_document(doc_type, seed)

            doc_id = f"{doc_type.value}_{i:03d}"
            image_path = images_dir / f"{doc_id}.png"
            label_path = labels_dir / f"{doc_id}.json"

            img.save(image_path)
            label_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            index.append(
                {
                    "id": doc_id,
                    "document_type": doc_type.value,
                    "image_path": str(image_path.relative_to(output_dir)),
                    "label_path": str(label_path.relative_to(output_dir)),
                }
            )

    index_path = output_dir / "index.jsonl"
    with index_path.open("w", encoding="utf-8") as f:
        for entry in index:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return index


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate the synthetic document dataset")
    parser.add_argument("--output", default="evals/dataset", type=Path)
    parser.add_argument("--per-type", default=15, type=int)
    args = parser.parse_args()

    entries = build_dataset(args.output, per_type=args.per_type)
    print(f"Generated {len(entries)} documents into {args.output}")
