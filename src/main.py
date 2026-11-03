"""Entry point: python -m src.main <target-repo-path> [--limit N]"""
import argparse
from pathlib import Path

from src.models.gemini import GeminiClient
from src.scanner import scan_repo, save_findings_csv, RESULTS_DIR

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="path to the cloned target repo")
    ap.add_argument("--limit", type=int, help="only scan first N files")
    args = ap.parse_args()

    clients = [GeminiClient()]  # add Groq + Claude clients later
    findings = scan_repo(Path(args.repo), clients, limit=args.limit)
    names = "_".join(c.name for c in clients)
    save_findings_csv(findings, RESULTS_DIR / f"findings_{names}.csv")
    print(f"Saved {len(findings)} findings to results/findings.csv")


if __name__ == "__main__":
    main()