import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"


def load_jsonl(filename):
    path = DATASET_DIR / filename
    items = []

    if not path.exists():
        return items

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    return items


def load_chunks():
    return load_jsonl("chunks.jsonl")


def load_rules():
    return load_jsonl("rules.jsonl")


def load_facts():
    return load_jsonl("facts.jsonl")


def load_qa():
    return load_jsonl("qa.jsonl")