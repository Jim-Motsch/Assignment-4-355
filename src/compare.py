"""Task 3: compare models using the team's verdicts and patch checks.

Usage: python -m src.compare
Reads results/reviewed_<model>.csv (verdict column) and
results/patches_<model>.csv (patch_verdict column) for each model,
prints the comparison table and writes results/comparison.csv.
Rows marked "out of scope" are left out of the counts.
"""
import csv
from pathlib import Path

RESULTS = Path("results")
MODELS = ["gemini", "claude", "groq"]
COLUMNS = ["model", "total_findings", "out_of_scope", "unreviewed",
           "true_vuln_true_patch", "true_vuln_false_patch",
           "true_vuln_unpatched", "hallucination", "precision"]


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm(value: str | None) -> str:
    return (value or "").strip().lower()


def summarize(model: str) -> dict | None:
    reviewed = read(RESULTS / f"reviewed_{model}.csv")
    if not reviewed:
        return None
    patches = read(RESULTS / f"patches_{model}.csv")
    verdicts = [norm(r.get("verdict")) for r in reviewed]
    real = verdicts.count("real")
    halluc = verdicts.count("hallucination")
    good = sum(norm(p.get("patch_verdict")).startswith("correct") for p in patches)
    bad = sum(norm(p.get("patch_verdict")).startswith("incorrect") for p in patches)
    judged = real + halluc
    return {
        "model": model,
        "total_findings": len(reviewed),
        "out_of_scope": verdicts.count("out of scope"),
        "unreviewed": verdicts.count(""),
        "true_vuln_true_patch": good,
        "true_vuln_false_patch": bad,
        "true_vuln_unpatched": real - good - bad,
        "hallucination": halluc,
        "precision": f"{real / judged:.0%}" if judged else "n/a",
    }


def main() -> None:
    rows = [s for m in MODELS if (s := summarize(m))]
    out = RESULTS / "comparison.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(" | ".join(COLUMNS))
    for r in rows:
        print(" | ".join(str(r[c]) for c in COLUMNS))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
