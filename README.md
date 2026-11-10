# Multi-LLM Vulnerability Analysis and Defensive Patching

IT 355 Assignment 4. A Python pipeline that scans a vulnerable Django app
([verademo-python](https://github.com/veracode-demo-labs/verademo-python)) with three LLMs,
asks each model to patch the findings the team confirmed as real, and compares the models.

## How it works

Every model sits behind one interface, `LLMClient` (`src/models/base.py`), with a single
`send(system_prompt, user_prompt)` method. The scanner, patcher and comparison code only talk
to that interface, so adding a model is one new file.

| Model | Client | Provider |
|---|---|---|
| Gemini | `src/models/gemini.py` | Google Gemini API |
| Claude | `src/models/claude.py` | Anthropic API |
| Groq | `src/models/groq_llama.py` | Groq API (files split into 250-line chunks for the free tier) |

Pipeline:

1. **Scan** (`src/scanner.py`): finds every `.py` file, numbers the lines, sends it with
   `prompts/scan_system.txt`, and retries on rate limits. `src/parser.py` turns the JSON reply
   into rows: file, line_start, line_end, cwe_id, cwe_name, explanation.
2. **Review** (manual): the team marks each finding `real`, `hallucination` or `out of scope`.
3. **Patch** (`src/patcher.py`): for each `real` finding, sends the vulnerable snippet
   (plus 5 lines of context) with `prompts/patch_system.txt` and saves the rewrite.
4. **Verify** (manual): the team marks each patch `correct` or `incorrect` with a summary.
5. **Compare** (`src/compare.py`): counts true vuln + true patch, true vuln + false patch,
   and hallucinations per model.

`src/carry_verdicts.py` copies verdicts from one model's reviewed CSV onto matching findings
(same file and CWE, lines within 1) from another model, so shared findings are only judged once.

## Setup

```
py -m pip install -r requirements.txt
```

Create a `.env` file in the repo root with `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`.
`.env` is gitignored. Clone the target next to this repo as `../verademo-python`.

## Usage

```
py -m src.main scan ../verademo-python --models gemini,claude,groq
py -m src.main patch ../verademo-python --models claude --reviewed results/reviewed_claude.csv
py -m src.carry_verdicts results/reviewed_gemini.csv results/findings_claude.csv
py -m src.compare
```

Add `--limit N` to `scan` to test on the first N files.

## Results

| File | Contents |
|---|---|
| `results/findings_<model>.csv` | raw scan findings |
| `results/reviewed_<model>.csv` | findings with team verdicts |
| `results/patches_<model>.csv` | generated patches with verification |
| `results/comparison.csv` | Task 3 table |
| `results/raw/`, `results/patches/` | raw model responses |