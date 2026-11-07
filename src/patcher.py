"""Task 2: send verified findings back to the same model for a fix."""
import csv
from pathlib import Path

from src.models.base import LLMClient
from src.scanner import RESULTS_DIR, send_with_retry

PATCH_PROMPT = Path("prompts/patch_system.txt")
CONTEXT = 5  # extra lines shown above and below the flagged lines
FIELDS = ["model", "file", "line_start", "line_end", "cwe_id", "cwe_name",
          "original_code", "patched_code",
          "patch_verdict", "verification_summary"]


def read_real_findings(reviewed_csv: Path) -> list[dict]:
    """Rows from the team's review sheet marked verdict = real."""
    with reviewed_csv.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)
                if r.get("verdict", "").strip().lower() == "real"]


def extract_snippet(repo_root: Path, rel: str, start: int, end: int):
    """Return (first_line, last_line, code) around the flagged lines."""
    lines = (repo_root / rel).read_text(
        encoding="utf-8", errors="replace").splitlines()
    lo, hi = max(start - CONTEXT, 1), min(end + CONTEXT, len(lines))
    return lo, hi, "\n".join(lines[lo - 1:hi])


def strip_fences(text: str) -> str:
    """Remove ``` fences if a model adds them anyway."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
    if t.endswith("```"):
        t = t[:-3]
    return t.rstrip()


def patch_findings(repo_root: Path, client: LLMClient,
                   reviewed_csv: Path) -> list[dict]:
    """Ask the model that found each real issue to fix it."""
    system_prompt = PATCH_PROMPT.read_text(encoding="utf-8")
    rows = read_real_findings(reviewed_csv)
    raw_dir = RESULTS_DIR / "patches" / client.name
    raw_dir.mkdir(parents=True, exist_ok=True)
    patches = []
    for n, row in enumerate(rows, 1):
        # Use the reviewer's corrected line when one was recorded.
        fixed = row.get("correct_line", "").strip()
        start = int(fixed or row["line_start"])
        end = start if fixed else int(row["line_end"])
        lo, hi, snippet = extract_snippet(repo_root, row["file"], start, end)
        user_prompt = (
            f"File: {row['file']}\n"
            f"Vulnerability: {row['cwe_id']} {row['cwe_name']} "
            f"at lines {start}-{end}\n"
            f"Finding: {row['explanation']}\n\n"
            f"Code (lines {lo}-{hi}):\n{snippet}")
        print(f"[{client.name}] patching {row['file']}:{start} "
              f"{row['cwe_id']} ({n}/{len(rows)})")
        try:
            raw = send_with_retry(client, system_prompt, user_prompt)
        except Exception as e:
            print(f"  ERROR: {client.name} failed: {e}")
            continue
        name = f"{n:03d}_{row['file'].replace('/', '__')}_{start}.txt"
        (raw_dir / name).write_text(raw, encoding="utf-8")
        patches.append({
            "model": client.name, "file": row["file"],
            "line_start": start, "line_end": end,
            "cwe_id": row["cwe_id"], "cwe_name": row["cwe_name"],
            "original_code": snippet, "patched_code": strip_fences(raw),
            "patch_verdict": "", "verification_summary": ""})
    return patches


def save_patches_csv(patches: list[dict], out: Path) -> None:
    """Write patches with empty columns for the team's manual review."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(patches)