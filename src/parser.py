"""Turns a model's raw text reply into validated finding dicts."""
import json
import re

REQUIRED = ("line_start", "line_end", "cwe_id", "cwe_name", "explanation")


def parse_findings(raw: str, model: str, file_path: str) -> list[dict]:
    """Extract the JSON array from a reply; skip anything malformed."""
    text = raw.strip()
    # Some models wrap JSON in ```json fences despite instructions.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        print(f"  WARNING: {model} gave no JSON array for {file_path}")
        return []
    try:
        items = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        print(f"  WARNING: {model} gave invalid JSON for {file_path}: {e}")
        return []
    findings = []
    for item in items:
        if not isinstance(item, dict) or not all(k in item for k in REQUIRED):
            print(f"  WARNING: {model} malformed item in {file_path}: {item}")
            continue
        # We use our own file path, not the model's, so it's always exact.
        findings.append({"model": model, "file": file_path,
                         **{k: item[k] for k in REQUIRED}})
    return findings