"""Task 1: scan a target repo's source files with each LLM."""
import csv
import time
from pathlib import Path

from src.models.base import LLMClient
from src.parser import parse_findings

PROMPT_PATH = Path("prompts/scan_system.txt")
RESULTS_DIR = Path("results")
SKIP_DIRS = {".git", "venv", ".venv", "__pycache__", "node_modules", "migrations"}
FIELDS = ["model", "file", "line_start", "line_end",
          "cwe_id", "cwe_name", "explanation"]


def find_source_files(repo_root: Path, exts=(".py",)) -> list[Path]:
    """All source files under repo_root, skipping tooling folders."""
    return sorted(p for p in repo_root.rglob("*")
                  if p.suffix in exts and not SKIP_DIRS & set(p.parts))


def number_lines(code: str) -> str:
    """Prefix each line with its number so models report exact lines."""
    return "\n".join(f"{i}: {line}"
                     for i, line in enumerate(code.splitlines(), 1))


def send_with_retry(client: LLMClient, system: str, user: str,
                    attempts: int = 4) -> str:
    """Retry with growing waits when the API is busy (e.g. 503)."""
    for attempt in range(attempts):
        try:
            return client.send(system, user)
        except Exception as e:
            if attempt == attempts - 1:
                raise
            wait = 5 * 2 ** attempt
            print(f"  {client.name}: {type(e).__name__}, retrying in {wait}s")
            time.sleep(wait)


def scan_repo(repo_root: Path, clients: list[LLMClient],
              limit: int | None = None) -> list[dict]:
    """Send every source file to every model; save raw replies."""
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    files = find_source_files(repo_root)[:limit]
    findings = []
    for client in clients:
        raw_dir = RESULTS_DIR / "raw" / client.name
        raw_dir.mkdir(parents=True, exist_ok=True)
        for path in files:
            rel = path.relative_to(repo_root).as_posix()
            code = path.read_text(encoding="utf-8", errors="replace")
            print(f"[{client.name}] scanning {rel}")
            raw = send_with_retry(client, system_prompt,
                                  f"File: {rel}\n\n{number_lines(code)}")
            (raw_dir / (rel.replace("/", "__") + ".txt")).write_text(
                raw, encoding="utf-8")
            findings.extend(parse_findings(raw, client.name, rel))
    return findings


def save_findings_csv(findings: list[dict],
                      out: Path = RESULTS_DIR / "findings.csv") -> None:
    """Write all findings to one CSV for the team's review sheet."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(findings)