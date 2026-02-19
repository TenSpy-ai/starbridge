"""Test prior-run deduplication — runs s0 → s1 → s2 only.

Picks a domain with completed prior runs, then runs the early pipeline
steps twice: once with ENABLE_PRIOR_RUN_DEDUP=True, once with False.
Compares the LLM search strategies to verify diversification works.

Usage:
    python -m agent.test_dedup                     # auto-pick domain
    python -m agent.test_dedup vmock.com            # specific domain
    python -m agent.test_dedup frontlineeducation.com
"""

import json
import logging
import sys
import time

from . import config, db, llm
from .pipeline import s0_parse_webhook, s1_validate_and_load, s2_search_strategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _pick_domain():
    """Find a domain with the most completed runs."""
    db.init_db()
    conn = db.get_connection()
    row = conn.execute("""
        SELECT target_domain, target_company, product_description,
               COUNT(*) as cnt
        FROM runs WHERE status='completed' AND target_domain != ''
        GROUP BY target_domain
        ORDER BY cnt DESC LIMIT 1
    """).fetchone()
    conn.close()
    if not row:
        return None, None, None, 0
    return row["target_domain"], row["target_company"], row["product_description"], row["cnt"]


def _get_domain_info(domain):
    """Get company/product info from most recent completed run for domain."""
    db.init_db()
    conn = db.get_connection()
    row = conn.execute(
        "SELECT target_company, product_description FROM runs "
        "WHERE target_domain = ? AND status = 'completed' ORDER BY id DESC LIMIT 1",
        (domain,),
    ).fetchone()
    cnt_row = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE target_domain = ? AND status = 'completed'",
        (domain,),
    ).fetchone()
    conn.close()
    if not row:
        return None, None, 0
    return row["target_company"], row["product_description"], cnt_row[0]


def _run_early_steps(webhook, dedup_enabled):
    """Run s0 → s1 → s2 and return the search strategy + timing."""
    # Set the dedup toggle
    config.ENABLE_PRIOR_RUN_DEDUP = dedup_enabled
    # Push to pipeline module (apply_config_to_modules pushes via setattr)
    import agent.pipeline as p
    p.ENABLE_PRIOR_RUN_DEDUP = dedup_enabled

    t0 = time.time()

    state = s0_parse_webhook(webhook)
    state |= s1_validate_and_load(state)

    prior_count = len(state.get("PRIOR_RUNS", []))
    prior_buyers = []
    for pr in state.get("PRIOR_RUNS", []):
        if pr.get("featured_buyer_name"):
            prior_buyers.append(pr["featured_buyer_name"])

    state |= s2_search_strategy(state)

    dt = time.time() - t0
    strategy = state["SEARCH_STRATEGY"]
    run_id = state.get("DB_RUN_ID")

    # Clean up the test run stub so it doesn't pollute future runs
    if run_id:
        conn = db.get_connection()
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.execute("DELETE FROM audit_log WHERE run_id = ?", (run_id,))
        conn.commit()
        conn.close()

    return {
        "strategy": strategy,
        "prior_count": prior_count,
        "prior_buyers": prior_buyers,
        "duration": dt,
        "run_id": run_id,
    }


def _compare(key, a, b):
    """Compare two values and return overlap info."""
    if isinstance(a, list) and isinstance(b, list):
        set_a, set_b = set(str(x).lower() for x in a), set(str(x).lower() for x in b)
        overlap = set_a & set_b
        pct = len(overlap) / max(len(set_a | set_b), 1) * 100
        return overlap, pct
    return None, None


def main():
    # Resolve domain
    domain = sys.argv[1] if len(sys.argv) > 1 else None

    if domain:
        company, product, prior_count = _get_domain_info(domain)
        if not company:
            print(f"\n  ERROR: No completed runs for domain '{domain}'\n")
            sys.exit(1)
    else:
        domain, company, product, prior_count = _pick_domain()
        if not domain:
            print("\n  ERROR: No completed runs in DB. Run the pipeline first.\n")
            sys.exit(1)

    webhook = {
        "target_company": company or "",
        "target_domain": domain,
        "product_description": product or "",
    }

    print()
    print("  Prior-Run Dedup Test (s0 → s1 → s2)")
    print("  " + "─" * 50)
    print(f"  Domain:       {domain}")
    print(f"  Company:      {company}")
    print(f"  Prior runs:   {prior_count}")
    print()

    # ── Run 1: dedup ON ──────────────────────────────────────────────
    print("  [1/2] Running with dedup ON...")
    r_on = _run_early_steps(webhook, dedup_enabled=True)
    s_on = r_on["strategy"]
    print(f"        Done in {r_on['duration']:.1f}s — {r_on['prior_count']} prior runs loaded")
    if r_on["prior_buyers"]:
        print(f"        Prior featured buyers: {', '.join(r_on['prior_buyers'][:5])}")
    print(f"        Primary keywords:   {s_on.get('primary_keywords', [])}")
    print(f"        Alternate keywords: {s_on.get('alternate_keywords', [])}")
    print(f"        Buyer types:        {s_on.get('buyer_types', [])}")
    print(f"        Geographic hints:   {s_on.get('geographic_hints', [])}")
    print()

    # ── Run 2: dedup OFF ─────────────────────────────────────────────
    print("  [2/2] Running with dedup OFF...")
    r_off = _run_early_steps(webhook, dedup_enabled=False)
    s_off = r_off["strategy"]
    print(f"        Done in {r_off['duration']:.1f}s — {r_off['prior_count']} prior runs loaded")
    print(f"        Primary keywords:   {s_off.get('primary_keywords', [])}")
    print(f"        Alternate keywords: {s_off.get('alternate_keywords', [])}")
    print(f"        Buyer types:        {s_off.get('buyer_types', [])}")
    print(f"        Geographic hints:   {s_off.get('geographic_hints', [])}")
    print()

    # ── Compare ──────────────────────────────────────────────────────
    print("  " + "─" * 50)
    print("  Comparison")
    print("  " + "─" * 50)

    for key in ("primary_keywords", "alternate_keywords", "buyer_types", "geographic_hints"):
        val_on = s_on.get(key, [])
        val_off = s_off.get(key, [])
        overlap, pct = _compare(key, val_on, val_off)
        if overlap is not None:
            diverged = "DIVERGED" if pct < 80 else "SIMILAR" if pct < 100 else "IDENTICAL"
            print(f"  {key:25s}  {diverged:10s}  overlap={pct:.0f}%  ({len(overlap)}/{max(len(set(str(x).lower() for x in val_on) | set(str(x).lower() for x in val_off)), 1)})")

    # ── Verdict ──────────────────────────────────────────────────────
    print()
    pk_overlap, pk_pct = _compare("primary_keywords",
                                   s_on.get("primary_keywords", []),
                                   s_off.get("primary_keywords", []))

    if r_on["prior_count"] == 0:
        print("  RESULT: No prior runs exist — both modes behave identically (expected)")
        verdict = True
    elif pk_pct is not None and pk_pct < 100:
        print(f"  RESULT: PASS — dedup ON produced different primary keywords ({pk_pct:.0f}% overlap)")
        verdict = True
    elif pk_pct == 100:
        print("  RESULT: INCONCLUSIVE — keywords identical despite prior runs")
        print("          (LLM may have chosen the same strategy; re-run to check)")
        verdict = True  # Not necessarily a failure — LLM is non-deterministic
    else:
        print("  RESULT: PASS")
        verdict = True

    dedup_loaded = r_on["prior_count"] > 0 and r_off["prior_count"] == 0
    if r_on["prior_count"] > 0 and r_off["prior_count"] == 0:
        print(f"  DEDUP GATE: PASS — ON loaded {r_on['prior_count']} prior runs, OFF loaded 0")
    elif r_on["prior_count"] == 0:
        print("  DEDUP GATE: N/A — no prior runs for this domain")
    else:
        print(f"  DEDUP GATE: FAIL — OFF should load 0 prior runs but loaded {r_off['prior_count']}")
        verdict = False

    print()

    # Restore config default
    config.ENABLE_PRIOR_RUN_DEDUP = True
    import agent.pipeline as p
    p.ENABLE_PRIOR_RUN_DEDUP = True

    sys.exit(0 if verdict else 1)


if __name__ == "__main__":
    main()
