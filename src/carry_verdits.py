"""Copy verdicts from one reviewed CSV onto matching rows of another.

Usage: python -m src.carry_verdicts results/reviewed_gemini.csv results/findings_claude.csv
Writes results/prefilled_<model>.csv. Only rows with the same file, an
overlapping line range (+-1) and the same CWE are copied; review the rest.
"""
import csv
import sys
from pathlib import Path

COPY = ["verdict", "correct_line", "notes"]


def overlaps(a: dict, b: dict) -> bool:
    return (a["file"] == b["file"]
            and int(a["line_start"]) - 1 <= int(b["line_end"])
            and int(b["line_start"]) - 1 <= int(a["line_end"]))


def main() -> None:
    reviewed = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    rows = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
    copied = 0
    for row in rows:
        for col in COPY + ["reviewer"]:
            row.setdefault(col, "")
        match = next((r for r in reviewed if r.get("verdict")
                      and overlaps(r, row) and r["cwe_id"] == row["cwe_id"]), None)
        if match:
            for col in COPY:
                row[col] = match.get(col, "")
            row["reviewer"] = "copied from " + match["model"]
            copied += 1
    model = rows[0]["model"] if rows else "unknown"
    out = Path("results") / f"prefilled_{model}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Copied {copied} of {len(rows)} verdicts -> {out}")


if __name__ == "__main__":
    main()
