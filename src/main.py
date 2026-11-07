"""Entry point.

Usage:
    python -m src.main scan  <target-repo> --models gemini,claude,groq [--limit N]
    python -m src.main patch <target-repo> --models gemini --reviewed results/reviewed_gemini.csv
"""
import argparse
import importlib
from pathlib import Path

from src.patcher import patch_findings, save_patches_csv
from src.scanner import RESULTS_DIR, save_findings_csv, scan_repo

# model name -> (module, class), imported only when chosen
CLIENTS = {
    "gemini": ("src.models.gemini", "GeminiClient"),
    "claude": ("src.models.claude", "ClaudeClient"),
    "groq": ("src.models.groq_llama", "GroqClient"),
}


def build_clients(names: list[str]) -> list:
    """Create a client object for each requested model name."""
    clients = []
    for name in names:
        module_name, class_name = CLIENTS[name]
        module = importlib.import_module(module_name)
        clients.append(getattr(module, class_name)())
    return clients


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["scan", "patch"])
    ap.add_argument("repo", help="path to the cloned target repo")
    ap.add_argument("--models", default="gemini",
                    help="comma-separated: " + ",".join(CLIENTS))
    ap.add_argument("--limit", type=int, help="scan: only first N files")
    ap.add_argument("--reviewed", help="patch: reviewed CSV from the sheet")
    args = ap.parse_args()

    names = [n.strip() for n in args.models.split(",")]
    clients = build_clients(names)
    repo = Path(args.repo)

    if args.command == "scan":
        findings = scan_repo(repo, clients, limit=args.limit)
        out = RESULTS_DIR / f"findings_{'_'.join(names)}.csv"
        save_findings_csv(findings, out)
        print(f"Saved {len(findings)} findings to {out}")
    else:
        if not args.reviewed or len(clients) != 1:
            ap.error("patch needs exactly one model and --reviewed <csv>")
        patches = patch_findings(repo, clients[0], Path(args.reviewed))
        out = RESULTS_DIR / f"patches_{names[0]}.csv"
        save_patches_csv(patches, out)
        print(f"Saved {len(patches)} patches to {out}")


if __name__ == "__main__":
    main()