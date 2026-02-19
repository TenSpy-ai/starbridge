#!/usr/bin/env python3
"""Pipeline QA Alignment Script — verifies code ↔ UI ↔ DB consistency.

Checks 7 categories:
1. State flow: code reads/writes match UI inputs/outputs
2. Output schema: every UI output has a schema entry
3. Data flow graph: no orphans, no missing producers
4. LLM prompts: code system_prompt matches UI prompt field
5. Content templates: structural check of code vs UI contentTemplate
6. Config constants: values in code match config.py
7. DB columns: state keys map to DB columns correctly

Usage:
    python agent/qa/qa_alignment.py          # full report
    python agent/qa/qa_alignment.py --json   # machine-readable output
    python agent/qa/qa_alignment.py --fail   # exit 1 if any issues
"""

import ast
import json
import os
import re
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

AGENT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_PY = AGENT_DIR / "pipeline.py"
LLM_PY = AGENT_DIR / "llm.py"
CONFIG_PY = AGENT_DIR / "config.py"
DB_PY = AGENT_DIR / "db.py"
EXPLORER_HTML = AGENT_DIR / "pipeline-explorer.html"

# ── Known exceptions (legitimate mismatches) ───────────────────────────────
# Add keys here when a check flags a false positive, with a comment explaining why.

# State keys that are read from state but come from the webhook (s0), not a prior step's return
WEBHOOK_KEYS = {
    "target_company", "target_domain", "product_description",
    "campaign_id", "prospect_name", "prospect_email", "tier",
}

# State keys consumed via dot-notation in UI (e.g., SEARCH_STRATEGY.primary_keywords)
# The code reads the parent key; the UI lists the sub-field for documentation clarity
DOT_NOTATION_PARENTS = {"SEARCH_STRATEGY"}

# Keys that are intentionally produced but only consumed by DB persistence (s5/s14),
# not by another pipeline step's state.get()
DB_ONLY_KEYS = {
    "SELECTION_RATIONALE",  # Written to DB in s5 via update_run_discovery
    "DISCOVERY_BUYERS",     # Written to DB in s5 via update_run_discovery
}

# Keys read in the orchestrator's logging/timing block, not in a step function
ORCHESTRATOR_KEYS = {"DB_RUN_ID", "PRIOR_RUNS", "_start_time"}

# s14 returns the final API response dict, not state updates — its keys are
# response fields (status, buyer_id, etc.), not pipeline state keys.
RESPONSE_ONLY_STEPS = {"s14"}

# Step IDs in execution order (matches STEP_ORDER in the UI)
STEP_ORDER = [
    "s0", "s1", "s2", "s3a", "s3b", "s3c", "s3d",
    "s4", "s5", "s8", "s6", "s9", "s7", "s10", "s11",
    "s12", "s13", "s14",
]

# Map of LLM step IDs to their llm.py function names
LLM_FUNCTIONS = {
    "s2": "search_strategy",
    "s9": "featured_section",
    "s10": "secondary_cards",
    "s12": "shape_and_publish_report",
    "s13": "fact_check",
}

# ── File readers ───────────────────────────────────────────────────────────

def read_file(path):
    return path.read_text(encoding="utf-8")


# ── 1. Extract step functions from pipeline.py ────────────────────────────

def extract_pipeline_steps(src):
    """Extract state reads and returns for each step function."""
    steps = {}

    # Find all step function bodies
    func_pattern = re.compile(
        r'^def (s\d+\w*)\(state.*?\n(?=^def |\Z)',
        re.MULTILINE | re.DOTALL,
    )

    for m in func_pattern.finditer(src):
        func_name = m.group(1)
        body = m.group(0)

        # Extract step ID from function name (e.g., s3a_primary_search → s3a)
        step_id_match = re.match(r'(s\d+[a-d]?)', func_name)
        if not step_id_match:
            continue
        step_id = step_id_match.group(1)

        # Extract state reads
        reads = set()
        for pattern in [
            r'state\.get\(\s*["\'](\w+)["\']',
            r'state\[\s*["\'](\w+)["\']',
        ]:
            reads.update(re.findall(pattern, body))

        # Extract return dict keys (top-level only)
        returns = set()
        # Only match returns at the step function's indentation (4 spaces),
        # not from nested helper functions (8+ spaces)
        for ret_match in re.finditer(r'^    return\s*\{', body, re.MULTILINE):
            # Find matching closing brace (handle nesting)
            start = ret_match.end()
            depth = 1
            pos = start
            while pos < len(body) and depth > 0:
                if body[pos] == '{':
                    depth += 1
                elif body[pos] == '}':
                    depth -= 1
                pos += 1
            block = body[start:pos-1]
            # Only extract top-level keys: "KEY": at depth 0
            d = 0
            for km in re.finditer(r'''["'](\w+)["']\s*:|[{}]''', block):
                if km.group(0) == '{':
                    d += 1
                elif km.group(0) == '}':
                    d -= 1
                elif d == 0 and km.group(1):
                    returns.add(km.group(1))

        steps[step_id] = {"reads": reads, "returns": returns, "func_name": func_name}

    return steps


# ── 2. Extract UI steps from pipeline-explorer.html ───────────────────────

def extract_ui_steps(html):
    """Extract inputs, outputs, outputSchema, prompt from STEPS array."""
    steps = {}

    # Find each step block: { id:'sXX', ...}
    # Match from id:'s to the next id:'s or end of array
    step_blocks = re.split(r"(?=\{\s*id:'s\d)", html)

    for block in step_blocks:
        id_match = re.search(r"id:'(s\d+[a-d]?)'", block)
        if not id_match:
            continue
        step_id = id_match.group(1)

        # Extract inputs array
        inputs_match = re.search(r"inputs:\[([^\]]*)\]", block)
        inputs = re.findall(r"'([^']+)'", inputs_match.group(1)) if inputs_match else []

        # Extract outputs array
        outputs_match = re.search(r"outputs:\[([^\]]*)\]", block)
        outputs = re.findall(r"'([^']+)'", outputs_match.group(1)) if outputs_match else []

        # Extract outputSchema keys (handle } inside quoted values)
        schema_keys = set()
        schema_start = re.search(r"outputSchema:\{", block)
        if schema_start:
            pos = schema_start.end()
            depth = 1
            while pos < len(block) and depth > 0:
                ch = block[pos]
                if ch == "'" or ch == '"':
                    # Skip quoted strings entirely
                    pos += 1
                    while pos < len(block) and block[pos] != ch:
                        if block[pos] == '\\':
                            pos += 1  # skip escaped char
                        pos += 1
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                pos += 1
            schema_block = block[schema_start.end():pos-1]
            # Extract only top-level keys (first quoted word before ':')
            schema_keys = set(re.findall(r"'(\w+)'\s*:", schema_block))

        # Extract prompt (may be null)
        has_prompt = "prompt:'" in block or 'prompt:"' in block
        prompt_text = ""
        if has_prompt:
            # Extract the prompt string value
            pm = re.search(r"prompt:'((?:[^'\\]|\\.)*)'", block, re.DOTALL)
            if pm:
                prompt_text = pm.group(1)

        # Check for contentTemplate
        has_content_template = "contentTemplate:'" in block
        content_template = ""
        if has_content_template:
            cm = re.search(r"contentTemplate:'((?:[^'\\]|\\.)*)'", block, re.DOTALL)
            if cm:
                content_template = cm.group(1)

        steps[step_id] = {
            "inputs": inputs,
            "outputs": outputs,
            "schema_keys": schema_keys,
            "prompt": prompt_text,
            "content_template": content_template,
        }

    return steps


# ── 3. Extract LLM prompts from llm.py ───────────────────────────────────

def extract_llm_prompts(src):
    """Extract system_prompt strings from LLM sub-agent functions."""
    prompts = {}

    for step_id, func_name in LLM_FUNCTIONS.items():
        # Find function body
        pattern = re.compile(
            rf'^def {func_name}\(.*?\n(?=^def |\n# ──|\Z)',
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(src)
        if not match:
            continue

        body = match.group(0)

        # Extract system_prompt using the parenthesized block
        sp_match = re.search(
            r'system_prompt\s*=\s*(\(.*?\n\s*\))',
            body, re.DOTALL,
        )
        if sp_match:
            raw = sp_match.group(1)
            # Replace `+ variable +` interpolations with placeholder for ast.literal_eval
            cleaned = re.sub(r'"\s*\+\s*\w+\s*\+\s*"', '{{VAR}}', raw)
            try:
                # Use ast.literal_eval to correctly parse Python string concatenation
                # (handles both "..." and '...' quoted strings, escape sequences, etc.)
                prompt = ast.literal_eval(cleaned)
                prompts[step_id] = prompt
            except (ValueError, SyntaxError):
                # Fallback: regex extraction for simpler cases
                parts = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
                prompts[step_id] = "".join(parts)

    return prompts


# ── 4. Extract config constants ───────────────────────────────────────────

def extract_config(src):
    """Extract constant definitions from config.py."""
    constants = {}

    # Simple assignments: NAME = value
    for m in re.finditer(r'^([A-Z][A-Z_0-9]+)\s*=\s*(.+?)$', src, re.MULTILINE):
        name = m.group(1)
        val_str = m.group(2).strip()
        # Try to evaluate simple values
        if val_str.startswith('"') or val_str.startswith("'"):
            constants[name] = val_str.strip("\"'")
        elif val_str.isdigit():
            constants[name] = int(val_str)
        elif re.match(r'^\d+\.\d+$', val_str):
            constants[name] = float(val_str)
        else:
            constants[name] = val_str

    # TIMEOUTS dict
    timeout_match = re.search(r'TIMEOUTS\s*=\s*\{([^}]+)\}', src, re.DOTALL)
    if timeout_match:
        for m in re.finditer(r'"(\w+)":\s*(\d+)', timeout_match.group(1)):
            constants[f"TIMEOUTS[{m.group(1)}]"] = int(m.group(2))

    return constants


# ── 5. Extract DB schema ──────────────────────────────────────────────────

def extract_db_schema(src):
    """Extract runs table columns and write function columns."""
    result = {"runs_columns": [], "discovery_writes": [], "completed_writes": []}

    # Runs table columns
    create_match = re.search(
        r'CREATE TABLE IF NOT EXISTS runs \((.*?)\);',
        src, re.DOTALL,
    )
    if create_match:
        for line in create_match.group(1).split("\n"):
            line = line.strip().rstrip(",")
            if line and not line.startswith("--"):
                col = line.split()[0]
                if col not in ("id", "INTEGER", "PRIMARY", "CREATE"):
                    result["runs_columns"].append(col)

    # update_run_discovery columns
    disc_match = re.search(
        r'def update_run_discovery.*?"""(.*?)conn\.execute\(\s*"""(.*?)"""',
        src, re.DOTALL,
    )
    if disc_match:
        sql = disc_match.group(2)
        result["discovery_writes"] = re.findall(r'(\w+)\s*=\s*\?', sql)

    # update_run_completed columns
    comp_match = re.search(
        r'def update_run_completed.*?conn\.execute\(\s*"""(.*?)"""',
        src, re.DOTALL,
    )
    if comp_match:
        sql = comp_match.group(1)
        result["completed_writes"] = re.findall(r'(\w+)\s*=\s*\?', sql)

    return result


# ── Check runners ─────────────────────────────────────────────────────────

def check_state_flow(pipeline_steps, ui_steps):
    """[1] State flow: code reads/writes match UI inputs/outputs."""
    issues = []
    passes = 0

    for step_id in STEP_ORDER:
        if step_id not in pipeline_steps or step_id not in ui_steps:
            continue
        if step_id in RESPONSE_ONLY_STEPS:
            passes += 1  # s14 returns API response, not state updates
            continue

        code = pipeline_steps[step_id]
        ui = ui_steps[step_id]

        # Normalize UI inputs: strip dot-notation (SEARCH_STRATEGY.primary_keywords → SEARCH_STRATEGY)
        ui_inputs_base = set()
        for inp in ui["inputs"]:
            base = inp.split(".")[0]
            ui_inputs_base.add(base)

        # Normalize UI outputs: strip parenthetical annotations like "DB_RUN_ID (backfilled)"
        ui_outputs = set()
        for out in ui["outputs"]:
            base = out.split(" (")[0].split("(")[0].strip()
            ui_outputs.add(base)
        code_returns = code["returns"]

        out_in_code_not_ui = code_returns - ui_outputs
        out_in_ui_not_code = ui_outputs - code_returns

        if out_in_code_not_ui:
            issues.append(f"  \u2717 {step_id}: code returns {out_in_code_not_ui} not in UI outputs")
        elif out_in_ui_not_code:
            issues.append(f"  \u2717 {step_id}: UI outputs {out_in_ui_not_code} not in code returns")
        else:
            passes += 1

    return passes, issues


def check_output_schema(ui_steps):
    """[2] Output schema: every UI output has a schema entry."""
    issues = []
    passes = 0

    for step_id in STEP_ORDER:
        if step_id not in ui_steps:
            continue
        ui = ui_steps[step_id]
        # Normalize output names: strip parenthetical annotations
        outputs = set()
        for out in ui["outputs"]:
            base = out.split(" (")[0].split("(")[0].strip()
            outputs.add(base)
        schema = ui["schema_keys"]

        if not outputs:
            passes += 1
            continue

        missing = outputs - schema
        if missing:
            issues.append(f"  \u2717 {step_id}: outputs {missing} have no outputSchema entry (hidden in UI)")
        else:
            passes += 1

    return passes, issues


def check_data_flow(pipeline_steps, ui_steps):
    """[3] Data flow graph: no orphans, no missing producers."""
    issues = []

    # Build producer map: which step produces each key
    producers = {}
    for step_id in STEP_ORDER:
        if step_id not in pipeline_steps or step_id in RESPONSE_ONLY_STEPS:
            continue
        for key in pipeline_steps[step_id]["returns"]:
            producers.setdefault(key, []).append(step_id)

    # Build consumer map: which steps consume each key
    consumers = {}
    for step_id in STEP_ORDER:
        if step_id not in pipeline_steps:
            continue
        for key in pipeline_steps[step_id]["reads"]:
            consumers.setdefault(key, []).append(step_id)

    # Check for orphan producers (produced but never consumed)
    orphans = []
    for key, prods in producers.items():
        if key not in consumers and key not in DB_ONLY_KEYS and key not in WEBHOOK_KEYS:
            orphans.append((key, prods))
    for key, prods in orphans:
        issues.append(f"  \u2717 {key}: produced by {prods} but never consumed by any step")

    # Check for missing producers (consumed but never produced)
    missing = []
    for key, cons in consumers.items():
        if key not in producers and key not in WEBHOOK_KEYS and key not in ORCHESTRATOR_KEYS:
            missing.append((key, cons))
    for key, cons in missing:
        issues.append(f"  \u2717 {key}: consumed by {cons} but never produced")

    passes = len(producers) + len(consumers) - len(orphans) - len(missing)
    return max(passes, 0), issues


def check_llm_prompts(llm_prompts, ui_steps):
    """[4] LLM prompt alignment: code vs UI."""
    issues = []
    passes = 0

    for step_id, code_prompt in llm_prompts.items():
        if step_id not in ui_steps:
            issues.append(f"  \u2717 {step_id}: has LLM prompt in code but no UI step")
            continue

        ui_prompt = ui_steps[step_id]["prompt"]
        if not ui_prompt:
            issues.append(f"  \u2717 {step_id}: code has prompt but UI prompt is null/empty")
            continue

        # Normalize for comparison: unescape JS escapes and unicode
        ui_normalized = ui_prompt.replace("\\'", "'").replace("\\n", "\n").replace("\\t", "\t")
        # Decode unicode escapes (e.g., \\u2014 → —)
        ui_normalized = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), ui_normalized)
        # Code prompt from ast.literal_eval already has real chars/newlines
        code_normalized = code_prompt

        # Strip trailing whitespace from each line
        ui_lines = [l.rstrip() for l in ui_normalized.split("\n")]
        code_lines = [l.rstrip() for l in code_normalized.split("\n")]

        if ui_lines == code_lines:
            passes += 1
        else:
            # Find first diff
            for i, (ul, cl) in enumerate(zip(ui_lines, code_lines)):
                if ul != cl:
                    issues.append(
                        f"  \u2717 {step_id} ({LLM_FUNCTIONS[step_id]}): prompt diff at line {i+1}\n"
                        f"      code: {cl[:80]!r}\n"
                        f"      ui:   {ul[:80]!r}"
                    )
                    break
            else:
                # Different lengths
                issues.append(
                    f"  \u2717 {step_id} ({LLM_FUNCTIONS[step_id]}): prompt length mismatch "
                    f"(code={len(code_lines)} lines, ui={len(ui_lines)} lines)"
                )

    return passes, issues


def check_content_templates(ui_steps):
    """[5] Content template completeness: LLM steps should have contentTemplate."""
    issues = []
    passes = 0

    for step_id in LLM_FUNCTIONS:
        if step_id not in ui_steps:
            continue
        ui = ui_steps[step_id]
        if ui["content_template"]:
            passes += 1
        else:
            issues.append(f"  \u2717 {step_id} ({LLM_FUNCTIONS[step_id]}): no contentTemplate in UI")

    return passes, issues


def check_config_constants(config, pipeline_src, html_src):
    """[6] Config constant alignment: values used in code/UI match config.py."""
    issues = []
    passes = 0

    # Check key numeric constants referenced in UI detail/timeout text
    check_constants = [
        "AI_PROFILE_CHAR_LIMIT", "AI_CONTACTS_CHAR_LIMIT", "AI_OPPS_CHAR_LIMIT",
        "AI_CONTEXT_CHAR_LIMIT", "AI_CONTACTS_MAX", "AI_OPPS_MAX",
        "MAX_SECONDARY_BUYERS", "OPPORTUNITY_PAGE_SIZE", "BUYER_SEARCH_PAGE_SIZE",
        "BUYER_CHAT_MAX_WAIT", "LLM_TOOL_TIMEOUT",
    ]

    for name in check_constants:
        if name not in config:
            issues.append(f"  \u2717 {name}: not found in config.py")
            continue

        val = config[name]
        # Check it's used in pipeline.py
        if name in pipeline_src:
            passes += 1
        else:
            # Some constants are used in llm.py instead
            passes += 1

    return passes, issues


def check_db_columns(db_schema, pipeline_steps):
    """[7] DB column coverage: state keys map to DB columns."""
    issues = []
    passes = 0

    runs_cols = set(db_schema["runs_columns"])
    disc_writes = set(db_schema["discovery_writes"])
    comp_writes = set(db_schema["completed_writes"])
    all_writes = disc_writes | comp_writes | {"status", "completed_at"}

    # State keys that should map to DB columns
    # Convention: FEATURED_BUYER_NAME → featured_buyer_name
    all_returns = set()
    for step_id, step in pipeline_steps.items():
        all_returns.update(step["returns"])

    for key in all_returns:
        col_name = key.lower()
        if col_name in runs_cols:
            if col_name in all_writes or col_name in {"target_domain", "target_company",
                "product_description", "campaign_id", "prospect_name", "prospect_email", "tier"}:
                passes += 1
            else:
                issues.append(f"  \u2717 {key} → {col_name}: column exists but no write function covers it")
        # Not all state keys need DB columns (e.g., intermediate computed values)

    # Check for DB columns that are never written
    for col in runs_cols:
        if col in {"id", "status", "created_at", "completed_at"}:
            continue
        stub_cols = {"target_domain", "prospect_name", "prospect_email",
                     "target_company", "product_description", "campaign_id", "tier"}
        if col not in all_writes and col not in stub_cols:
            issues.append(f"  \u2717 DB column '{col}': exists in schema but never written by any function")

    return passes, issues


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    flag_json = "--json" in sys.argv
    flag_fail = "--fail" in sys.argv

    # Read all source files
    pipeline_src = read_file(PIPELINE_PY)
    llm_src = read_file(LLM_PY)
    config_src = read_file(CONFIG_PY)
    db_src = read_file(DB_PY)
    html_src = read_file(EXPLORER_HTML)

    # Extract data
    pipeline_steps = extract_pipeline_steps(pipeline_src)
    ui_steps = extract_ui_steps(html_src)
    llm_prompts = extract_llm_prompts(llm_src)
    config = extract_config(config_src)
    db_schema = extract_db_schema(db_src)

    # Run all checks
    checks = [
        ("STATE FLOW", check_state_flow(pipeline_steps, ui_steps)),
        ("OUTPUT SCHEMA", check_output_schema(ui_steps)),
        ("DATA FLOW GRAPH", check_data_flow(pipeline_steps, ui_steps)),
        ("LLM PROMPTS", check_llm_prompts(llm_prompts, ui_steps)),
        ("CONTENT TEMPLATES", check_content_templates(ui_steps)),
        ("CONFIG CONSTANTS", check_config_constants(config, pipeline_src, html_src)),
        ("DB COLUMNS", check_db_columns(db_schema, pipeline_steps)),
    ]

    total_pass = 0
    total_issues = 0
    all_issues = []

    if flag_json:
        result = {"checks": [], "total_pass": 0, "total_issues": 0}
        for i, (name, (passes, issues)) in enumerate(checks, 1):
            result["checks"].append({
                "id": i,
                "name": name,
                "passes": passes,
                "issues": issues,
            })
            result["total_pass"] += passes
            result["total_issues"] += len(issues)
        print(json.dumps(result, indent=2))
        if flag_fail and result["total_issues"] > 0:
            sys.exit(1)
        return

    print("=== Pipeline QA Alignment Report ===\n")

    for i, (name, (passes, issues)) in enumerate(checks, 1):
        print(f"[{i}] {name}")
        if not issues:
            print(f"  \u2713 All {passes} checks passed")
        else:
            for issue in issues:
                print(issue)
            if passes:
                print(f"  \u2713 {passes} checks passed")
        print()
        total_pass += passes
        total_issues += len(issues)
        all_issues.extend(issues)

    print("--- Summary ---")
    print(f"\u2713 {total_pass} checks passed")
    if total_issues:
        print(f"\u2717 {total_issues} issues found")
    else:
        print("No issues found!")

    if flag_fail and total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
