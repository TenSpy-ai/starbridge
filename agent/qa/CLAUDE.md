# QA Scripts

## qa_alignment.py — Pipeline Code <> UI Alignment Checker

Verifies that pipeline-explorer.html step definitions stay in sync with the actual Python code.

### When to run
- After any change to pipeline.py, llm.py, config.py, db.py, or pipeline-explorer.html
- Before committing changes that touch both code and UI
- When adding/removing state keys, DB columns, or LLM prompts

### How to run

```bash
python agent/qa/qa_alignment.py          # full report
python agent/qa/qa_alignment.py --json   # machine-readable output
python agent/qa/qa_alignment.py --fail   # exit 1 if any issues (for CI)
```

### What it checks

1. **State flow** — code reads/writes match UI inputs/outputs
2. **Output schema** — every output has a schema entry
3. **Data flow graph** — no orphan keys, no missing producers
4. **LLM prompts** — code system_prompt matches UI prompt field
5. **Content templates** — code content block matches UI contentTemplate
6. **Config constants** — values in code match config.py match UI mentions
7. **DB columns** — state keys map to DB columns, write functions cover them

### Maintaining this script

- If a check flags a **false positive** (the code is correct but the regex misparses it), add the key to the appropriate `KNOWN_EXCEPTIONS` set at the top of the script with a comment explaining why
- If you add a **new step** to the pipeline, the script auto-discovers it — no changes needed
- If you add a **new LLM sub-agent**, add its function name to the `LLM_FUNCTIONS` mapping
- If you add a **new config constant**, it's auto-discovered from config.py
- If checks start failing after a legitimate change, fix the source of truth (code or UI), don't suppress the check
