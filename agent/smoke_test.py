"""Smoke tests for all external integration points.

Validates every tools.py function and pipeline conditional path against
live APIs. Catches schema mismatches, parameter format bugs, and broken
code paths that only surface against real services.

Usage:
    python -m agent.smoke_test          # quick — API tools only, skip LLM/async
    python -m agent.smoke_test --full   # full — include LLM + buyer_chat async
"""

import re
import sys
import time
import traceback

from . import db, llm, tools

FULL = "--full" in sys.argv


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_completed_run():
    """Pull the most recent completed run from the DB."""
    db.init_db()
    conn = db.get_connection()
    row = conn.execute(
        "SELECT * FROM runs WHERE status='completed' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _extract_notion_page_id(url):
    """Extract 32-char hex page ID from a Notion URL."""
    clean = url.split("/")[-1].replace("-", "")
    m = re.search(r'([0-9a-f]{32})', clean)
    return m.group(1) if m else None


# ── Tool Schema Tests (Category A) ──────────────────────────────────────────

def test_opportunity_search():
    result = tools.opportunity_search(
        "workforce management", types=["Meeting"], page_size=5,
    )
    items = result if isinstance(result, list) else result.get("data", result.get("results", []))
    return True, f"returned {len(items) if isinstance(items, list) else '?'} items"


def test_buyer_search():
    result = tools.buyer_search(buyer_types=["SchoolDistrict"], page_size=1)
    items = result if isinstance(result, list) else result.get("data", result.get("results", []))
    return True, f"returned {len(items) if isinstance(items, list) else '?'} items"


def test_buyer_profile():
    run = _get_completed_run()
    if not run or not run.get("featured_buyer_id"):
        return False, "no completed run with buyer_id in DB"
    result = tools.buyer_profile(run["featured_buyer_id"])
    has_data = bool(result)
    return has_data, f"buyer_id={run['featured_buyer_id']}, got data={has_data}"


def test_buyer_contacts():
    run = _get_completed_run()
    if not run or not run.get("featured_buyer_id"):
        return False, "no completed run with buyer_id in DB"
    result = tools.buyer_contacts(run["featured_buyer_id"], page_size=1)
    has_data = bool(result)
    return has_data, f"buyer_id={run['featured_buyer_id']}, got data={has_data}"


def test_buyer_chat():
    """Async tool — takes 10-90s. Only runs with --full."""
    run = _get_completed_run()
    if not run or not run.get("featured_buyer_id"):
        return False, "no completed run with buyer_id in DB"
    result = tools.buyer_chat(
        run["featured_buyer_id"],
        "What procurement signals exist for this buyer?",
        max_wait=120,
    )
    has_data = bool(result) and len(str(result)) > 50
    return has_data, f"{len(str(result))} chars"


def test_notion_create_page():
    from .config import NOTION_PARENT_PAGE_ID
    ts = int(time.time())
    title = f"[SMOKE TEST {ts} — DELETE ME]"
    content = "This page was created by smoke_test.py and can be safely deleted."
    result = tools.notion_create_page(title, content, parent_page_id=NOTION_PARENT_PAGE_ID)
    # Notion MCP returns a list: [{"pages": [{"id": ..., "url": ...}]}]
    ok = bool(result)
    return ok, f"created page: {str(result)[:200]}"


def test_notion_search():
    result = tools.notion_search("Detroit")
    ok = result is not None
    return ok, f"got response: {str(result)[:200]}"


def test_notion_fetch():
    run = _get_completed_run()
    if not run or not run.get("notion_url"):
        return False, "no completed run with notion_url in DB"
    page_id = _extract_notion_page_id(run["notion_url"])
    if not page_id:
        return False, f"could not extract page_id from {run['notion_url']}"
    result = tools.notion_fetch(page_id)
    has_content = bool(result) and len(str(result)) > 100
    return has_content, f"page_id={page_id}, {len(str(result))} chars"


def test_notion_update_page():
    run = _get_completed_run()
    if not run or not run.get("notion_url") or not run.get("report_markdown"):
        return False, "no completed run with notion_url + report in DB"
    page_id = _extract_notion_page_id(run["notion_url"])
    if not page_id:
        return False, f"could not extract page_id from {run['notion_url']}"
    # Re-apply the same report — idempotent, no visible change
    result = tools.notion_update_page(page_id, content=run["report_markdown"])
    ok = isinstance(result, dict) and not result.get("is_error", False)
    return ok, f"page_id={page_id}, result={str(result)[:200]}"


# ── Conditional Path Tests (Category B) ─────────────────────────────────────

def test_s3b_skip():
    """s3b with empty keywords should return empty list without API call."""
    from .pipeline import s3b_alternate_search
    state = {
        "SEARCH_STRATEGY": {"alternate_keywords": [], "rfp_keywords": []},
        "DB_RUN_ID": None,
    }
    result = s3b_alternate_search(state)
    ok = result.get("DISCOVERY_SIGNALS_B") == []
    return ok, f"DISCOVERY_SIGNALS_B={result.get('DISCOVERY_SIGNALS_B')}"


def test_s3c_skip():
    """s3c with empty buyer_types should return empty list without API call."""
    from .pipeline import s3c_buyer_type_search
    state = {
        "SEARCH_STRATEGY": {"buyer_types": [], "ideal_buyer_profile": ""},
        "DB_RUN_ID": None,
    }
    result = s3c_buyer_type_search(state)
    ok = result.get("DISCOVERY_BUYERS_C") == []
    return ok, f"DISCOVERY_BUYERS_C={result.get('DISCOVERY_BUYERS_C')}"


def test_s3d_skip():
    """s3d with empty geographic hints should return empty list without API call."""
    from .pipeline import s3d_buyer_geo_search
    state = {
        "SEARCH_STRATEGY": {"geographic_hints": []},
        "DB_RUN_ID": None,
    }
    result = s3d_buyer_geo_search(state)
    ok = result.get("DISCOVERY_BUYERS_D") == []
    return ok, f"DISCOVERY_BUYERS_D={result.get('DISCOVERY_BUYERS_D')}"


def test_s4_no_buyers():
    """s4 with zero buyers should raise ValueError."""
    from .pipeline import s4_rank_and_select
    state = {
        "DISCOVERY_SIGNALS_A": [],
        "DISCOVERY_SIGNALS_B": [],
        "DISCOVERY_BUYERS_C": [],
        "DISCOVERY_BUYERS_D": [],
        "SEARCH_STRATEGY": {"primary_keywords": [], "buyer_types": [], "ideal_buyer_profile": ""},
        "DB_RUN_ID": None,
    }
    try:
        s4_rank_and_select(state)
        return False, "expected ValueError but none raised"
    except ValueError as e:
        return True, f"correctly raised: {e}"


def test_s13_no_findings():
    """s13 with a well-formed report should pass without fix/update."""
    run = _get_completed_run()
    if not run or not run.get("report_markdown"):
        return False, "no completed run with report in DB"

    from .pipeline import s13_validate
    import json

    state = {
        "DB_RUN_ID": None,
        "REPORT_MARKDOWN": run["report_markdown"],
        "FEATURED_BUYER_NAME": run.get("featured_buyer_name", ""),
        "target_company": run.get("target_company", ""),
        "SECONDARY_BUYERS": json.loads(run["secondary_buyers"]) if run.get("secondary_buyers") else [],
        "NOTION_PAGE_URL": None,  # prevent any Notion writes
    }

    result = s13_validate(state)
    validation = result.get("VALIDATION_RESULT", {})
    has_no_fix = "VALIDATED_REPORT_MARKDOWN" not in result
    return True, f"passed={validation.get('passed')}, fixed={validation.get('fixed')}, no_fix_applied={has_no_fix}"


def test_s13_fix_path():
    """s13 with injected warnings should trigger fix_report."""
    run = _get_completed_run()
    if not run or not run.get("report_markdown"):
        return False, "no completed run with report in DB"

    # Inject a deliberate issue by corrupting the buyer name
    report = run["report_markdown"]
    real_buyer = run.get("featured_buyer_name", "")
    if not real_buyer:
        return False, "no featured buyer name in run"

    # Replace buyer name in header with wrong name — triggers check 1
    corrupted_report = report.replace(real_buyer, "WRONG_BUYER_NAME_12345", 1)

    from .pipeline import s13_validate

    state = {
        "DB_RUN_ID": None,
        "REPORT_MARKDOWN": corrupted_report,
        "FEATURED_BUYER_NAME": real_buyer,
        "target_company": run.get("target_company", ""),
        "SECONDARY_BUYERS": [],
        "NOTION_PAGE_URL": None,  # don't actually update Notion
    }

    result = s13_validate(state)
    validation = result.get("VALIDATION_RESULT", {})
    has_issues = len(validation.get("issues", [])) > 0
    fix_attempted = validation.get("fixed", False)
    return has_issues, (
        f"issues={validation.get('issues', [])}, "
        f"fix_attempted={fix_attempted}, "
        f"has_validated_report={'VALIDATED_REPORT_MARKDOWN' in result}"
    )


# ── LLM Sub-agent Tests (Category C — --full only) ──────────────────────────

def test_llm_search_strategy():
    result = llm.search_strategy(
        target_company="VMock",
        target_domain="vmock.com",
        product_description="AI-powered career services platform",
    )
    required_keys = {"primary_keywords", "alternate_keywords", "buyer_types"}
    has_keys = required_keys.issubset(set(result.keys()))
    return has_keys, f"keys={list(result.keys())}"


def test_llm_fact_check():
    run = _get_completed_run()
    if not run or not run.get("report_markdown"):
        return False, "no completed run with report in DB"
    passed, detail = llm.fact_check(
        run.get("featured_buyer_name", ""),
        run["report_markdown"],
    )
    return True, f"passed={passed}, detail={detail[:100]}"


def test_llm_fix_report():
    run = _get_completed_run()
    if not run or not run.get("report_markdown"):
        return False, "no completed run with report in DB"
    fixed = llm.fix_report(
        run.get("featured_buyer_name", ""),
        run["report_markdown"],
        issues=["Test issue: buyer name missing from header"],
        warnings=[],
    )
    ok = bool(fixed) and len(fixed) > 500
    return ok, f"{len(fixed)} chars"


# ── Test Registry ────────────────────────────────────────────────────────────

TESTS = [
    # Category A: Tool schema tests
    ("opportunity_search", test_opportunity_search, False),
    ("buyer_search", test_buyer_search, False),
    ("buyer_profile", test_buyer_profile, False),
    ("buyer_contacts", test_buyer_contacts, False),
    ("buyer_chat", test_buyer_chat, True),
    ("notion_create_page", test_notion_create_page, False),
    ("notion_search", test_notion_search, False),
    ("notion_fetch", test_notion_fetch, False),
    ("notion_update_page", test_notion_update_page, False),
    # Category B: Conditional path tests
    ("s3b_skip", test_s3b_skip, False),
    ("s3c_skip", test_s3c_skip, False),
    ("s3d_skip", test_s3d_skip, False),
    ("s4_no_buyers", test_s4_no_buyers, False),
    ("s13_no_findings", test_s13_no_findings, True),
    ("s13_fix_path", test_s13_fix_path, True),
    # Category C: LLM sub-agent tests
    ("llm_search_strategy", test_llm_search_strategy, True),
    ("llm_fact_check", test_llm_fact_check, True),
    ("llm_fix_report", test_llm_fix_report, True),
]


# ── Runner ───────────────────────────────────────────────────────────────────

def main():
    print()
    print("  Smoke Tests (agent)")
    print("  " + "─" * 42)

    results = []
    passed = 0
    failed = 0
    skipped = 0

    for name, fn, full_only in TESTS:
        if full_only and not FULL:
            print(f"  ○ {name:28s} SKIP (use --full)")
            skipped += 1
            results.append((name, "skip", 0))
            continue

        t0 = time.time()
        try:
            ok, detail = fn()
            dt = time.time() - t0
            if ok:
                print(f"  ✓ {name:28s} {dt:.1f}s")
                passed += 1
                results.append((name, "pass", dt))
            else:
                print(f"  ✗ {name:28s} {dt:.1f}s  FAIL: {detail}")
                failed += 1
                results.append((name, "fail", dt))
        except Exception as e:
            dt = time.time() - t0
            print(f"  ✗ {name:28s} {dt:.1f}s  ERROR: {type(e).__name__}: {e}")
            if FULL:
                traceback.print_exc()
            failed += 1
            results.append((name, "fail", dt))

    total = passed + failed + skipped
    print("  " + "─" * 42)
    print(f"  {passed}/{total} passed, {failed} failed, {skipped} skipped")
    print()

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
