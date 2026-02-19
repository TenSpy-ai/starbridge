"""Intel brief pipeline — 18 steps from webhook to published Notion report.

LLM calls (s2, s9, s10, s12, s13) go through agent.llm sub-agents.
s12 uses MCP tool access to shape the report AND publish to Notion in one session.
Starbridge tool calls (s3a, s3b, s3c, s6=profile+contacts+chat, s7×N) go through agent.tools.
"""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from . import llm, tools
from .config import (
    AI_CONTACTS_CHAR_LIMIT,
    AI_CONTACTS_MAX,
    AI_CONTEXT_CHAR_LIMIT,
    AI_OPPS_CHAR_LIMIT,
    AI_OPPS_MAX,
    AI_PROFILE_CHAR_LIMIT,
    AI_REPORT_SECTION_CHAR_LIMIT,
    BUYER_SEARCH_PAGE_SIZE,
    BUYER_TYPE_LABEL,
    CTA_BUYERS_COUNT,
    CTA_RECORDS_COUNT,
    ENABLE_PRIOR_RUN_DEDUP,
    FEATURED_CONTACT_PAGE_SIZE,
    MAX_SECONDARY_BUYERS,
    MAX_WORKERS_DISCOVERY,
    MAX_WORKERS_ENRICHMENT,
    MAX_WORKERS_FEATURED,
    MAX_WORKERS_SECONDARY,
    NOTION_PARENT_PAGE_ID,
    OPPORTUNITY_PAGE_SIZE,
    SECONDARY_CONTACT_PAGE_SIZE,
    STATE_CODES,
    TIMEOUTS,
)
from .db import (
    StepTimer,
    init_db,
    insert_contacts,
    insert_discoveries,
    insert_run,
    insert_run_stub,
    load_prior_runs,
    log_step,
    update_run_cancelled,
    update_run_completed,
    update_run_discovery,
    update_run_failed,
)

logger = logging.getLogger("pipeline")

# Short stop words filtered out when extracting keywords from ideal_buyer_profile
_STOP_WORDS = frozenset({
    "with", "that", "this", "from", "their", "which", "have", "been",
    "will", "would", "could", "should", "about", "into", "over", "under",
    "between", "through", "after", "before", "during", "without", "within",
    "along", "across", "against", "toward", "upon", "need", "needing",
    "seeking", "looking", "using", "based", "large", "small",
})


class PipelineCancelled(Exception):
    """Raised when the pipeline is killed by the user."""
    pass


def _summarize_output(data, max_str=10000, max_items=10):
    """Summarize a step output dict for audit_log metadata.

    Preserves full content for UI display. Only truncates extremely large
    strings (>10K chars) and caps list samples at 10 items.
    """
    if not isinstance(data, dict):
        return data
    out = {}
    for k, v in data.items():
        if isinstance(v, str):
            out[k] = v[:max_str] + f"... ({len(v)} chars)" if len(v) > max_str else v
        elif isinstance(v, list):
            sample = v[:max_items]
            cleaned = []
            for item in sample:
                if isinstance(item, dict):
                    cleaned.append({ik: (iv[:500] + "..." if isinstance(iv, str) and len(iv) > 500 else iv) for ik, iv in list(item.items())[:15]})
                else:
                    cleaned.append(item)
            out[k] = {"_count": len(v), "_sample": cleaned}
        elif isinstance(v, dict):
            out[k] = {ik: (iv[:500] + "..." if isinstance(iv, str) and len(iv) > 500 else iv) for ik, iv in list(v.items())[:20]}
        else:
            out[k] = v
    return out


# ── Helpers ─────────────────────────────────────────────────────────────────

def _opps_list(raw):
    """Normalize opportunity search results to a list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("opportunities") or raw.get("results") or raw.get("data") or []
    return []


def _buyers_list(raw):
    """Normalize buyer search results to a list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("buyers") or raw.get("results") or raw.get("data") or []
    return []


def _contacts_list(raw):
    """Normalize contacts response to a list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("contacts") or raw.get("results") or raw.get("data") or []
    return []


# ── Phase I: SOURCE ─────────────────────────────────────────────────────────

def s0_parse_webhook(webhook: dict) -> dict:
    """s0 — Extract & validate 7 webhook fields."""
    logger.info("[s0] Parsing webhook")

    if not webhook.get("target_domain") and not webhook.get("target_company"):
        raise ValueError("Webhook must have target_domain or target_company")

    state = {
        "target_company": webhook.get("target_company", ""),
        "target_domain": webhook.get("target_domain", ""),
        "product_description": webhook.get("product_description", ""),
        "campaign_id": webhook.get("campaign_id", ""),
        "prospect_name": webhook.get("prospect_name", ""),
        "prospect_email": webhook.get("prospect_email", ""),
        "tier": webhook.get("tier", ""),
        "_start_time": time.time(),
    }
    logger.info(f"  target: {state['target_company']} ({state['target_domain']})")
    return state


# ── Phase II: INPUT ─────────────────────────────────────────────────────────

def s1_validate_and_load(state: dict) -> dict:
    """s1 — Validate field formats, init DB, create run stub, load cache."""
    logger.info("[s1] Validating inputs + loading cache")

    domain = state["target_domain"]
    if domain and not re.match(r'^[\w.-]+\.\w{2,}$', domain):
        logger.warning(f"  domain format suspect: {domain}")

    init_db()

    # Create a run stub immediately so all subsequent steps have a run_id
    # for audit logging. Discovery data is backfilled in s5.
    # If DB_RUN_ID is pre-assigned (batch mode), skip stub creation.
    if state.get("DB_RUN_ID"):
        run_id = state["DB_RUN_ID"]
        logger.info(f"  run_id={run_id} (pre-assigned)")
    else:
        run_id = insert_run_stub(state)
        logger.info(f"  run_id={run_id} (stub created)")

    if ENABLE_PRIOR_RUN_DEDUP and domain:
        prior_runs = load_prior_runs(domain)
    else:
        prior_runs = []

    logger.info(f"  prior runs: {len(prior_runs)} (dedup={'on' if ENABLE_PRIOR_RUN_DEDUP else 'off'})")
    # Duration is added retroactively by the orchestrator
    return {"PRIOR_RUNS": prior_runs, "DB_RUN_ID": run_id}


# ── Phase III: ANALYZE ──────────────────────────────────────────────────────

def s2_search_strategy(state: dict) -> dict:
    """s2 — LLM sub-agent: analyze target → SLED segments + search keywords + opp types."""
    logger.info("[s2] Generating search strategy via LLM")

    run_id = state.get("DB_RUN_ID")

    with StepTimer(run_id, "s2_search_strategy") as t:
        strategy = llm.search_strategy(
            target_company=state["target_company"],
            target_domain=state["target_domain"],
            product_description=state["product_description"],
            prior_runs=state.get("PRIOR_RUNS", []),
        )
        t.message = f"kw={strategy['primary_keywords']}, types={strategy.get('opportunity_types', [])}"
        t.metadata = _summarize_output({"SEARCH_STRATEGY": strategy})

    logger.info(f"  primary kw: {strategy['primary_keywords']}")
    logger.info(f"  alternate kw: {strategy['alternate_keywords']}")
    logger.info(f"  buyer types: {strategy['buyer_types']}")
    logger.info(f"  opportunity types: {strategy.get('opportunity_types', [])}")

    return {"SEARCH_STRATEGY": strategy}


# ── Phase IV: DISCOVER ──────────────────────────────────────────────────────

def s3a_primary_search(state: dict) -> dict:
    """s3a — opportunity_search with primary keywords."""
    primary = state["SEARCH_STRATEGY"].get("primary_keywords", [])
    meeting = state["SEARCH_STRATEGY"].get("meeting_keywords", [])
    kw = " ".join(primary + meeting)
    opp_types = state["SEARCH_STRATEGY"].get("opportunity_types", [])
    logger.info(f"[s3a] Opportunity search (primary+meeting): '{kw}' types={opp_types}")

    run_id = state.get("DB_RUN_ID")

    with StepTimer(run_id, "s3a_primary_search") as t:
        raw = tools.opportunity_search(
            search_query=kw,
            types=opp_types,
            page_size=OPPORTUNITY_PAGE_SIZE,
        )
        opps = _opps_list(raw)
        t.message = f"{len(opps)} results"
        t.metadata = _summarize_output({"DISCOVERY_SIGNALS_A": opps})
        logger.info(f"  → {len(opps)} results")

    return {"DISCOVERY_SIGNALS_A": opps}


def s3b_alternate_search(state: dict) -> dict:
    """s3b — opportunity_search with alternate keywords."""
    alternate = state["SEARCH_STRATEGY"].get("alternate_keywords", [])
    rfp = state["SEARCH_STRATEGY"].get("rfp_keywords", [])
    kw = " ".join(alternate + rfp)
    if not kw.strip():
        logger.info("[s3b] No alternate/rfp keywords, skipping")
        log_step(state.get("DB_RUN_ID"), "s3b_alternate_search", "skipped",
                 "No alternate/rfp keywords", duration=0)
        return {"DISCOVERY_SIGNALS_B": []}

    opp_types = state["SEARCH_STRATEGY"].get("opportunity_types", [])
    logger.info(f"[s3b] Opportunity search (alternate+rfp): '{kw}' types={opp_types}")

    run_id = state.get("DB_RUN_ID")

    with StepTimer(run_id, "s3b_alternate_search") as t:
        raw = tools.opportunity_search(
            search_query=kw,
            types=opp_types,
            page_size=OPPORTUNITY_PAGE_SIZE,
        )
        opps = _opps_list(raw)
        t.message = f"{len(opps)} results"
        t.metadata = _summarize_output({"DISCOVERY_SIGNALS_B": opps})
        logger.info(f"  → {len(opps)} results")

    return {"DISCOVERY_SIGNALS_B": opps}


def s3c_buyer_type_search(state: dict) -> dict:
    """s3c — buyer_search by buyer_types filter only.

    Searches for buyers matching the LLM-selected buyer types (e.g.
    SchoolDistrict, City). Runs in parallel with s3d (geographic search).
    """
    strategy = state["SEARCH_STRATEGY"]
    buyer_types = strategy.get("buyer_types", [])

    if not buyer_types:
        logger.info("[s3c] No buyer types — skipping")
        log_step(state.get("DB_RUN_ID"), "s3c_buyer_type_search", "skipped",
                 "No buyer types in strategy", duration=0)
        return {"DISCOVERY_BUYERS_C": []}

    # Extract first significant keyword from ideal_buyer_profile for name-contains filter
    profile = strategy.get("ideal_buyer_profile", "")
    profile_words = [w for w in profile.split() if len(w) > 3 and w.lower() not in _STOP_WORDS]
    query = profile_words[0] if profile_words else None

    logger.info(f"[s3c] Buyer type search: types={buyer_types} query={query}")
    run_id = state.get("DB_RUN_ID")

    with StepTimer(run_id, "s3c_buyer_type_search") as t:
        raw = tools.buyer_search(
            query=query,
            buyer_types=buyer_types,
            page_size=BUYER_SEARCH_PAGE_SIZE,
        )
        buyers = _buyers_list(raw)
        t.message = f"{len(buyers)} buyers"
        t.metadata = _summarize_output({"DISCOVERY_BUYERS_C": buyers})
        logger.info(f"  → {len(buyers)} buyers")

    return {"DISCOVERY_BUYERS_C": buyers}


def s3d_buyer_geo_search(state: dict) -> dict:
    """s3d — buyer_search by geographic hints (state codes) only.

    Searches for buyers in the LLM-identified geographic regions.
    Runs in parallel with s3c (buyer type search).
    """
    strategy = state["SEARCH_STRATEGY"]
    geo = strategy.get("geographic_hints", [])

    state_codes = []
    for hint in geo[:3]:
        h = hint.strip()
        if len(h) == 2 and h.upper().isalpha():
            state_codes.append(h.upper())
        else:
            code = STATE_CODES.get(h.lower())
            if code:
                state_codes.append(code)

    if not state_codes:
        logger.info("[s3d] No geographic hints — skipping")
        log_step(state.get("DB_RUN_ID"), "s3d_buyer_geo_search", "skipped",
                 "No geographic hints in strategy", duration=0)
        return {"DISCOVERY_BUYERS_D": []}

    logger.info(f"[s3d] Buyer geo search: states={state_codes}")
    run_id = state.get("DB_RUN_ID")

    with StepTimer(run_id, "s3d_buyer_geo_search") as t:
        raw = tools.buyer_search(
            states=state_codes,
            page_size=BUYER_SEARCH_PAGE_SIZE,
        )
        buyers = _buyers_list(raw)
        t.message = f"{len(buyers)} buyers"
        t.metadata = _summarize_output({"DISCOVERY_BUYERS_D": buyers})
        logger.info(f"  → {len(buyers)} buyers")

    return {"DISCOVERY_BUYERS_D": buyers}


# ── Phase V: SELECT ─────────────────────────────────────────────────────────

def s4_rank_and_select(state: dict) -> dict:
    """s4 — Fully deterministic: merge, dedupe, score, select featured + secondary."""
    logger.info("[s4] Ranking buyers (deterministic)")
    _s4_start = time.time()

    opps_a = state.get("DISCOVERY_SIGNALS_A") or []
    opps_b = state.get("DISCOVERY_SIGNALS_B") or []
    buyers_c = state.get("DISCOVERY_BUYERS_C") or []
    buyers_d = state.get("DISCOVERY_BUYERS_D") or []
    direct_buyers = buyers_c + buyers_d
    all_opps = opps_a + opps_b

    # ── Build buyer → signals map from opportunity results ──
    buyer_signals = {}
    for opp in all_opps:
        bid = opp.get("buyerId") or opp.get("buyer_id") or opp.get("id")
        bname = opp.get("buyerName") or opp.get("buyer_name") or opp.get("name", "Unknown")
        btype = opp.get("buyerType") or opp.get("buyer_type") or ""
        if not bid:
            continue
        if bid not in buyer_signals:
            buyer_signals[bid] = {"name": bname, "type": btype, "signals": []}
        buyer_signals[bid]["signals"].append(opp)

    # ── Add direct buyers from s3c + s3d (may have zero signals) ──
    for b in direct_buyers:
        bid = b.get("id") or b.get("buyerId")
        if bid and bid not in buyer_signals:
            buyer_signals[bid] = {
                "name": b.get("name") or b.get("buyerName", "Unknown"),
                "type": b.get("type") or b.get("buyerType", ""),
                "signals": [],
            }

    if not buyer_signals:
        raise ValueError("No buyers found across all searches — cannot generate report")

    # ── Score each buyer ──
    primary_kw = state.get("SEARCH_STRATEGY", {}).get("primary_keywords", [])
    profile = state.get("SEARCH_STRATEGY", {}).get("ideal_buyer_profile", "")
    profile_words = [w for w in profile.split() if len(w) > 3 and w.lower() not in _STOP_WORDS]
    kw_set = set(w.lower() for kw in primary_kw for w in kw.split())
    kw_set.update(w.lower() for w in profile_words)
    target_types = set(t.lower() for t in state.get("SEARCH_STRATEGY", {}).get("buyer_types", []))

    scored = []
    for bid, info in buyer_signals.items():
        signals = info["signals"]
        sig_count = len(signals)

        recency = 0.0
        for s in signals:
            date_str = s.get("date") or s.get("createdAt") or s.get("created_at") or ""
            if date_str:
                try:
                    dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                    age_days = (datetime.now(dt.tzinfo) - dt).days if dt.tzinfo else (datetime.now() - dt).days
                    recency = max(recency, max(0, 365 - age_days) / 365)
                except (ValueError, TypeError):
                    pass

        urgency = 0.0
        for s in signals:
            stype = (s.get("type") or s.get("opportunityType") or "").lower()
            if stype in ("rfp", "contract", "contract expiration"):
                urgency = 1.0
                break
            title = (s.get("title") or s.get("summary") or "").lower()
            if any(w in title for w in ["deadline", "expir", "due date", "rfp"]):
                urgency = 1.0
                break

        max_dollar = 0.0
        for s in signals:
            amt = s.get("amount") or s.get("value") or s.get("contractAmount") or 0
            if isinstance(amt, (int, float)):
                max_dollar = max(max_dollar, float(amt))
            elif isinstance(amt, str):
                for n in re.findall(r'[\d]+(?:\.[\d]+)?', amt.replace(",", "")):
                    try:
                        max_dollar = max(max_dollar, float(n))
                    except ValueError:
                        pass

        kw_hits = 0
        for s in signals:
            text = f"{s.get('title', '')} {s.get('summary', '')}".lower()
            kw_hits += sum(1 for w in kw_set if w in text)

        buyer_type_raw = (info["type"] or "").lower()
        buyer_type_tokens = [t.strip().lower() for t in buyer_type_raw.split(",")]
        type_match = 1.0 if any(t in target_types for t in buyer_type_tokens) else 0.0

        scored.append({
            "buyerId": bid,
            "buyerName": info["name"],
            "buyerType": info["type"],
            "signalCount": sig_count,
            "topSignalType": signals[0].get("type", "") if signals else "",
            "topSignalSummary": (signals[0].get("title") or signals[0].get("summary", ""))[:200] if signals else "",
            "score": 0.0,
            "_sig": sig_count,
            "_rec": recency,
            "_urg": urgency,
            "_dol": max_dollar,
            "_kw": kw_hits,
            "_type": type_match,
        })

    # Normalize and compute final scores
    max_sig = max((s["_sig"] for s in scored), default=1) or 1
    max_dol = max((s["_dol"] for s in scored), default=1) or 1
    max_kw = max((s["_kw"] for s in scored), default=1) or 1

    for s in scored:
        s["score"] = round(
            0.25 * s["_type"]
            + 0.20 * (s["_sig"] / max_sig)
            + 0.20 * s["_rec"]
            + 0.15 * s["_urg"]
            + 0.10 * (s["_dol"] / max_dol)
            + 0.10 * (s["_kw"] / max_kw),
            4,
        )
        for k in ("_sig", "_rec", "_urg", "_dol", "_kw", "_type"):
            del s[k]

    scored.sort(key=lambda x: x["score"], reverse=True)

    featured = scored[0]
    secondary = scored[1:MAX_SECONDARY_BUYERS + 1]

    rationale = (
        f"Selected {featured['buyerName']} (score: {featured['score']:.3f}) "
        f"with {featured['signalCount']} signals. "
        f"Top signal: {featured['topSignalType']} — {featured['topSignalSummary'][:100]}"
    )

    logger.info(f"  Featured: {featured['buyerName']} (score={featured['score']:.3f}, signals={featured['signalCount']})")
    logger.info(f"  Secondary: {[s['buyerName'] for s in secondary]}")

    log_step(state.get("DB_RUN_ID"), "s4_rank_and_select", "success",
             f"Featured={featured['buyerName']}, {len(scored)} total buyers",
             duration=time.time() - _s4_start,
             metadata=_summarize_output({
                 "FEATURED": {"name": featured["buyerName"], "id": featured["buyerId"], "score": featured["score"], "signals": featured["signalCount"]},
                 "SECONDARY_BUYERS": [{"name": s["buyerName"], "score": s["score"]} for s in secondary],
                 "TOTAL_SCORED": len(scored),
             }))

    return {
        "FEATURED_BUYER_ID": featured["buyerId"],
        "FEATURED_BUYER_NAME": featured["buyerName"],
        "FEATURED_BUYER_TYPE": featured.get("buyerType", ""),
        "SECONDARY_BUYERS": secondary,
        "SELECTION_RATIONALE": rationale,
        "ALL_SCORED_BUYERS": scored,
        "DISCOVERY_BUYERS": list({(b.get("id") or b.get("buyerId")): b for b in direct_buyers}.values()),
    }


def s5_persist_discovery(state: dict) -> dict:
    """s5 — Backfill discovery data into the run stub + insert discoveries."""
    logger.info("[s5] Persisting discovery to SQLite")
    _s5_start = time.time()

    run_id = state.get("DB_RUN_ID")

    if run_id:
        update_run_discovery(run_id, state)
    else:
        run_id = insert_run(state)

    all_scored = state.get("ALL_SCORED_BUYERS", [])
    insert_discoveries(run_id, state["target_domain"], all_scored)
    logger.info(f"  run_id={run_id}, {len(all_scored)} discoveries saved")
    log_step(run_id, "s5_persist_discovery", "success",
             f"run_id={run_id}, {len(all_scored)} discoveries",
             duration=time.time() - _s5_start,
             metadata={"discoveries": len(all_scored), "run_id": run_id})
    return {"DB_RUN_ID": run_id}


# ── Phase VI: ENRICH & GENERATE ────────────────────────────────────────────

def s6_featured_intel(state: dict) -> dict:
    """s6 — Parallel fetch: buyer_profile + buyer_contacts + buyer_chat for featured buyer.

    Replaces full_intel (which was just a combo of these) to avoid SSE timeout.
    Opportunities are reused from s3a/s3b discovery results — no need to re-fetch.
    """
    buyer_id = state["FEATURED_BUYER_ID"]
    buyer_name = state["FEATURED_BUYER_NAME"]
    logger.info(f"[s6] Enriching featured buyer: {buyer_name} ({buyer_id[:8]}...)")

    run_id = state.get("DB_RUN_ID")

    ai_question = (
        f"What are {buyer_name}'s key strategic priorities, recent technology initiatives, "
        f"major procurement activity, and any leadership changes in the past 12 months? "
        f"Include specific initiative names, dollar amounts, and dates where available."
    )

    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS_FEATURED)
    f_profile = pool.submit(tools.buyer_profile, buyer_id)
    f_contacts = pool.submit(tools.buyer_contacts, buyer_id, FEATURED_CONTACT_PAGE_SIZE)
    f_ai_chat = pool.submit(tools.buyer_chat, buyer_id, ai_question)

    profile = None
    contacts = []

    _t0 = time.time()
    try:
        raw_prof = f_profile.result(timeout=TIMEOUTS.get("s7", 20))
        if isinstance(raw_prof, dict):
            profile = raw_prof.get("profile") or raw_prof
        else:
            profile = raw_prof
        logger.info("  buyer_profile ✓")
        log_step(run_id, "s6_buyer_profile", "success", duration=time.time() - _t0,
                 metadata=_summarize_output({"FEAT_PROFILE": profile}))
    except Exception as e:
        log_step(run_id, "s6_buyer_profile", "failure", f"{type(e).__name__}: {e}", duration=time.time() - _t0)
        pool.shutdown(wait=False, cancel_futures=True)
        raise

    _t0 = time.time()
    try:
        raw_con = f_contacts.result(timeout=TIMEOUTS.get("s7", 20))
        contacts = _contacts_list(raw_con)
        logger.info(f"  buyer_contacts ✓ ({len(contacts)})")
        log_step(run_id, "s6_buyer_contacts", "success", f"{len(contacts)} contacts", duration=time.time() - _t0,
                 metadata=_summarize_output({"FEAT_CONTACTS": contacts}))
    except Exception as e:
        log_step(run_id, "s6_buyer_contacts", "failure", f"{type(e).__name__}: {e}", duration=time.time() - _t0)
        pool.shutdown(wait=False, cancel_futures=True)
        raise

    _t0 = time.time()
    try:
        raw_chat = f_ai_chat.result(timeout=TIMEOUTS.get("s6", 330))
        if isinstance(raw_chat, dict):
            ai_ctx = raw_chat.get("ai_response") or raw_chat.get("response") or raw_chat.get("answer")
            if not ai_ctx:
                ai_ctx = json.dumps(raw_chat)
        elif raw_chat:
            ai_ctx = str(raw_chat)
        else:
            raise RuntimeError(f"buyer_chat returned empty response for {buyer_name}")
        logger.info(f"  buyer_chat ✓ ({len(ai_ctx or '')} chars)")
        log_step(run_id, "s6_buyer_chat", "success", f"{len(ai_ctx or '')} chars", duration=time.time() - _t0,
                 metadata=_summarize_output({"FEAT_AI_CONTEXT": ai_ctx or ""}))
    except Exception as e:
        log_step(run_id, "s6_buyer_chat", "failure", f"{type(e).__name__}: {e}", duration=time.time() - _t0)
        pool.shutdown(wait=False, cancel_futures=True)
        raise

    pool.shutdown(wait=False, cancel_futures=True)

    # Reuse opportunities from discovery phase
    all_opps = (state.get("DISCOVERY_SIGNALS_A") or []) + (state.get("DISCOVERY_SIGNALS_B") or [])
    opps = [o for o in all_opps if (o.get("buyerId") or o.get("buyer_id")) == buyer_id]

    logger.info(f"  profile: {'yes' if profile else 'no'}, contacts: {len(contacts)}, "
                f"opportunities: {len(opps)}, AI: {'yes' if ai_ctx else 'no'}")

    return {
        "FEAT_PROFILE": profile,
        "FEAT_CONTACTS": contacts,
        "FEAT_OPPORTUNITIES": opps,
        "FEAT_AI_CONTEXT": ai_ctx,
    }


def s7_secondary_intel(state: dict) -> dict:
    """s7 — buyer_profile + buyer_contacts per secondary buyer (parallel)."""
    secondaries = state.get("SECONDARY_BUYERS") or []
    if not secondaries:
        logger.info("[s7] No secondary buyers, skipping")
        return {"SEC_PROFILES": [], "SEC_CONTACTS": []}

    logger.info(f"[s7] Fetching intel for {len(secondaries)} secondary buyers")
    _s7_start = time.time()

    run_id = state.get("DB_RUN_ID")

    def _fetch_one(buyer):
        bid = buyer["buyerId"]
        bname = buyer["buyerName"]
        prof = tools.buyer_profile(bid)
        cons = _contacts_list(tools.buyer_contacts(bid, page_size=SECONDARY_CONTACT_PAGE_SIZE))
        return {"profile": prof, "contacts": cons, "buyerId": bid, "buyerName": bname}

    profiles = []
    contacts_out = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS_SECONDARY) as pool:
        futures = {pool.submit(_fetch_one, b): b["buyerName"] for b in secondaries[:MAX_SECONDARY_BUYERS]}
        for f in as_completed(futures, timeout=TIMEOUTS.get("s7", 20)):
            r = f.result()
            profiles.append(r["profile"])
            contacts_out.append({
                "buyerId": r["buyerId"],
                "buyerName": r["buyerName"],
                "contacts": r["contacts"],
            })

    logger.info(f"  fetched {len(profiles)} profiles, {len(contacts_out)} contact sets")
    log_step(run_id, "s7_secondary_intel", "success",
             f"{len(profiles)} profiles, {len(contacts_out)} contact sets",
             duration=time.time() - _s7_start,
             metadata=_summarize_output({"SEC_PROFILES": profiles, "SEC_CONTACTS": contacts_out}))
    return {"SEC_PROFILES": profiles, "SEC_CONTACTS": contacts_out}


def s8_exec_summary(state: dict) -> dict:
    """s8 — Template: executive summary (no LLM)."""
    logger.info("[s8] Exec summary (template)")
    _s8_start = time.time()

    opps_a = state.get("DISCOVERY_SIGNALS_A") or []
    opps_b = state.get("DISCOVERY_SIGNALS_B") or []
    all_buyers = state.get("ALL_SCORED_BUYERS") or []
    featured = state.get("FEATURED_BUYER_NAME", "Unknown")
    featured_type = state.get("FEATURED_BUYER_TYPE", "")
    segments = state.get("SEARCH_STRATEGY", {}).get("sled_segments", [])
    product = state.get("target_company", "")

    signal_count = len(opps_a) + len(opps_b)
    buyer_count = len(all_buyers)
    seg_str = " and ".join(BUYER_TYPE_LABEL.get(s, s) for s in segments[:3]) if segments else "SLED"
    type_label = BUYER_TYPE_LABEL.get(featured_type, featured_type)

    summary = (
        f"We scanned **{signal_count} procurement signals** across **{buyer_count} SLED buyers** "
        f"in the {seg_str} space for **{product}**. "
        f"Leading match: **{featured}**"
    )
    if type_label:
        summary += f" ({type_label})"
    summary += ", with the strongest combination of signal recency, urgency, and relevance."

    run_id = state.get("DB_RUN_ID")
    if run_id:
        log_step(run_id, "s8_exec_summary", "success",
                 f"{signal_count} signals, {buyer_count} buyers, featured={featured}",
                 duration=time.time() - _s8_start,
                 metadata=_summarize_output({"SECTION_EXEC_SUMMARY": summary}))

    return {"SECTION_EXEC_SUMMARY": summary}


def s9_featured_section(state: dict) -> dict:
    """s9 — LLM sub-agent: featured buyer deep-dive."""
    logger.info("[s9] Featured buyer section via LLM")

    run_id = state.get("DB_RUN_ID")
    profile = state.get("FEAT_PROFILE")
    contacts = state.get("FEAT_CONTACTS") or []
    opps = state.get("FEAT_OPPORTUNITIES") or []
    ai_ctx = state.get("FEAT_AI_CONTEXT") or ""
    buyer_name = state.get("FEATURED_BUYER_NAME", "Unknown")
    buyer_type = state.get("FEATURED_BUYER_TYPE", "")
    product = state.get("target_company", "")
    product_desc = state.get("product_description", "")

    with StepTimer(run_id, "s9_featured_section") as t:
        section = llm.featured_section(
            buyer_name=buyer_name,
            buyer_type=buyer_type,
            product=product,
            product_desc=product_desc,
            profile_json=json.dumps(profile, indent=2, default=str)[:AI_PROFILE_CHAR_LIMIT],
            contacts_json=json.dumps(contacts[:AI_CONTACTS_MAX], indent=2, default=str)[:AI_CONTACTS_CHAR_LIMIT],
            opps_json=json.dumps(opps[:AI_OPPS_MAX], indent=2, default=str)[:AI_OPPS_CHAR_LIMIT],
            ai_context=str(ai_ctx)[:AI_CONTEXT_CHAR_LIMIT] if ai_ctx else None,
        )
        t.message = f"{len(section)} chars"
        t.metadata = _summarize_output({"SECTION_FEATURED": section})

    return {"SECTION_FEATURED": section}


def s10_secondary_cards(state: dict) -> dict:
    """s10 — LLM sub-agent: compact cards for each secondary buyer."""
    secondaries = state.get("SECONDARY_BUYERS") or []
    if not secondaries:
        logger.info("[s10] No secondary buyers, skipping")
        return {"SECTION_SECONDARY": ""}

    sec_profiles = state.get("SEC_PROFILES") or []
    sec_contacts = state.get("SEC_CONTACTS") or []

    logger.info(f"[s10] Generating {len(secondaries)} secondary cards via LLM")

    run_id = state.get("DB_RUN_ID")
    product = state.get("target_company", "")
    product_desc = state.get("product_description", "")

    buyers_content = ""
    for i, buyer in enumerate(secondaries[:MAX_SECONDARY_BUYERS]):
        buyers_content += f"--- BUYER {i+1} ---\n"
        buyers_content += f"Name: {buyer['buyerName']} | Type: {buyer.get('buyerType', 'Unknown')}\n"
        buyers_content += f"Score: {buyer.get('score', 0):.3f} | Signals: {buyer.get('signalCount', 0)}\n"
        buyers_content += f"Top Signal: {buyer.get('topSignalType', '')} — {buyer.get('topSignalSummary', '')}\n"

        if i < len(sec_profiles) and sec_profiles[i]:
            buyers_content += f"Profile: {json.dumps(sec_profiles[i], default=str)[:800]}\n"

        matching = [sc for sc in sec_contacts if sc.get("buyerId") == buyer["buyerId"]]
        if matching and matching[0].get("contacts"):
            buyers_content += f"Contacts: {json.dumps(matching[0]['contacts'][:5], default=str)[:800]}\n"

        buyers_content += "\n"

    with StepTimer(run_id, "s10_secondary_cards") as t:
        section = llm.secondary_cards(product, product_desc, buyers_content)
        t.message = f"{len(section)} chars, {len(secondaries)} buyers"
        t.metadata = _summarize_output({"SECTION_SECONDARY": section})

    return {"SECTION_SECONDARY": section}


def s11_cta(state: dict) -> dict:
    """s11 — Template: Starbridge CTA section (no LLM)."""
    logger.info("[s11] CTA (template)")
    _s11_start = time.time()

    product = state.get("target_company", "")
    segments = state.get("SEARCH_STRATEGY", {}).get("sled_segments", [])
    all_buyers = state.get("ALL_SCORED_BUYERS") or []
    total_signals = (
        len(state.get("DISCOVERY_SIGNALS_A") or [])
        + len(state.get("DISCOVERY_SIGNALS_B") or [])
    )

    seg_str = ", ".join(BUYER_TYPE_LABEL.get(s, s) for s in segments[:3]) if segments else "SLED"

    cta = (
        f"## What Starbridge Can Do\n\n"
        f"Starbridge monitors **{CTA_BUYERS_COUNT} government and education buyers** across all 50 states, "
        f"with **{CTA_RECORDS_COUNT} indexed board meetings and procurement records**. "
        f"For {product} targeting {seg_str} buyers, we surface:\n\n"
        f"- **Active procurement signals** — RFPs, contract expirations, board discussions, and budget allocations\n"
        f"- **Verified decision-maker contacts** — directors, VPs, superintendents, and budget authorities\n"
        f"- **AI-powered buyer analysis** — strategic context synthesized from public records and FOIA data\n\n"
        f"This scan surfaced **{total_signals} signals** across **{len(all_buyers)} buyers** "
        f"in the {seg_str} space."
    )

    run_id = state.get("DB_RUN_ID")
    if run_id:
        log_step(run_id, "s11_cta", "success",
                 f"{total_signals} signals, {len(all_buyers)} buyers",
                 duration=time.time() - _s11_start,
                 metadata=_summarize_output({"SECTION_CTA": cta}))

    return {"SECTION_CTA": cta}


# ── Phase VII: ASSEMBLE & VALIDATE ──────────────────────────────────────────


def _extract_notion_url(result):
    """Extract Notion page URL from the Datagen MCP / SDK response.

    Handles multiple response formats:
    - MCP CallToolResult: {content: [{type: "text", text: "...json..."}]}
    - SDK list format: [{pages: [{id, url, ...}]}]
    - SDK dict format: {pages: [{id, url, ...}]}
    - Plain URL string
    """
    # Unwrap MCP CallToolResult format
    if isinstance(result, dict) and "content" in result and isinstance(result.get("content"), list):
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                try:
                    result = json.loads(item["text"])
                    break
                except (json.JSONDecodeError, TypeError):
                    pass

    page = None
    if isinstance(result, list) and result:
        inner = result[0]
        if isinstance(inner, dict) and "pages" in inner:
            pages = inner["pages"]
            page = pages[0] if pages else None
        elif isinstance(inner, dict):
            page = inner
    elif isinstance(result, dict):
        if "pages" in result:
            pages = result["pages"]
            page = pages[0] if pages else None
        else:
            page = result
    elif isinstance(result, str) and result.startswith("http"):
        page = {"url": result}

    url = None
    if isinstance(page, dict):
        url = page.get("url") or page.get("page_url") or page.get("public_url")
        if not url and page.get("id"):
            url = f"https://notion.so/{page['id'].replace('-', '')}"

    if not url:
        raise RuntimeError(f"Notion publish succeeded but no URL extracted from: {result}")

    return url


def s12_assemble(state: dict) -> dict:
    """s12 — LLM-driven report assembly + Notion publish.

    LLM with Notion MCP tool access assembles the report from pre-generated
    sections (s8 exec summary, s9 featured, s10 secondary, s11 CTA) and
    publishes to Notion in a single Claude CLI session. Retries once on failure
    (fresh LLM call may format MCP params differently). Hard-fails after 2nd attempt.
    """
    logger.info("[s12] Assembling report from sections + publishing to Notion")
    _s12_start = time.time()

    run_id = state.get("DB_RUN_ID")
    buyer_name = state.get("FEATURED_BUYER_NAME", "Unknown")
    product = state.get("target_company", "")

    if not NOTION_PARENT_PAGE_ID:
        raise RuntimeError("NOTION_PARENT_PAGE_ID not set — cannot publish")

    data_kwargs = {
        "target_company": product,
        "product_description": state.get("product_description", ""),
        "buyer_name": buyer_name,
        "buyer_type": state.get("FEATURED_BUYER_TYPE", ""),
        "section_featured": (
            state.get("SECTION_FEATURED") or ""
        )[:AI_REPORT_SECTION_CHAR_LIMIT],
        "section_secondary": (
            state.get("SECTION_SECONDARY") or ""
        )[:AI_REPORT_SECTION_CHAR_LIMIT],
        "section_exec_summary": (
            state.get("SECTION_EXEC_SUMMARY") or ""
        )[:AI_REPORT_SECTION_CHAR_LIMIT],
        "section_cta": (
            state.get("SECTION_CTA") or ""
        )[:AI_REPORT_SECTION_CHAR_LIMIT],
    }

    # Retry on failure — the LLM may format MCP params wrong or Notion may 500.
    # A fresh LLM call can produce correct params on retry.
    max_attempts = 2
    last_err = None
    for attempt in range(max_attempts):
        try:
            report, notion_url = llm.shape_and_publish_report(
                **data_kwargs,
                notion_parent_page_id=NOTION_PARENT_PAGE_ID,
            )
            break
        except Exception as e:
            last_err = e
            if attempt < max_attempts - 1:
                log_step(run_id, "s12_assemble_retry", "warning",
                         f"Attempt {attempt+1} failed: {e}, retrying...")
                logger.warning(f"  s12 attempt {attempt+1} failed: {e}, retrying...")
            else:
                raise
    report = re.sub(r'\n{3,}', '\n\n', report)
    logger.info(f"  Report shaped + published: {len(report)} chars, URL: {notion_url}")

    log_step(run_id, "s12_assemble", "success",
             f"{len(report)} chars",
             duration=time.time() - _s12_start,
             metadata=_summarize_output({"REPORT_MARKDOWN": report, "NOTION_PAGE_URL": notion_url}))

    return {"REPORT_MARKDOWN": report, "NOTION_PAGE_URL": notion_url}


def s13_validate(state: dict) -> dict:
    """s13 — Deterministic validation checks + mandatory LLM fact-check."""
    logger.info("[s13] Validating report")

    run_id = state.get("DB_RUN_ID")
    report = state.get("REPORT_MARKDOWN", "")
    issues = []
    warnings = []

    # Check 1: buyer name in header
    buyer_name = state.get("FEATURED_BUYER_NAME", "")
    if buyer_name and buyer_name not in report[:500]:
        issues.append(f"Header missing featured buyer name '{buyer_name}'")

    # Check 2: product name in report
    product = state.get("target_company", "")
    if product and product.lower() not in report.lower():
        issues.append(f"Product name '{product}' not found in report")

    # Check 3: footer date is current
    expected_date = datetime.now().strftime("%B %Y")
    if expected_date not in report:
        issues.append(f"Footer missing current date '{expected_date}'")

    # Check 4: no contacts with both email AND phone as "—"
    bad_rows = re.findall(r'\|[^|]+\|[^|]+\|\s*—\s*\|\s*—\s*\|', report)
    if bad_rows:
        issues.append(f"{len(bad_rows)} contact rows with no email AND no phone")

    # Check 5: report is non-trivially long
    if len(report) < 500:
        issues.append(f"Report suspiciously short ({len(report)} chars)")

    # Check 6: email format validation (deterministic)
    email_pattern = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', report)
    for email in email_pattern:
        if not re.match(r'^[\w.+-]+@[\w.-]+\.\w{2,}$', email):
            issues.append(f"Malformed email '{email}' in report")

    # Check 7: secondary buyer names match scored buyers
    secondary_names = {b["buyerName"] for b in (state.get("SECONDARY_BUYERS") or [])}
    if secondary_names:
        for name in secondary_names:
            if name not in report:
                warnings.append(f"Secondary buyer '{name}' not found in report")

    # Check 8: LLM consistency check
    with StepTimer(run_id, "s13_llm_fact_check") as t:
        fc_passed, detail = llm.fact_check(buyer_name, report)
        if not fc_passed:
            warnings.append(f"LLM consistency check: {detail}")
            t.status = "warning"
        t.message = f"{'PASS' if fc_passed else 'FAIL'}: {detail[:100]}"

    passed = len(issues) == 0
    all_findings = issues + warnings
    logger.info(f"  validation: {'PASS' if passed else f'FAIL ({len(issues)} issues)'}"
                f"{f', {len(warnings)} warnings' if warnings else ''}")
    for issue in issues:
        logger.warning(f"    FAIL: {issue}")
    for warning in warnings:
        logger.warning(f"    WARN: {warning}")

    # If any issues or warnings found, fix the report and update Notion
    validated_report = None
    if all_findings:
        notion_url = state.get("NOTION_PAGE_URL")

        # Step 1: LLM fixes the report
        with StepTimer(run_id, "s13_fix_report") as t_fix:
            try:
                validated_report = llm.fix_report(
                    state.get("FEATURED_BUYER_NAME", ""),
                    state.get("REPORT_MARKDOWN", ""),
                    issues, warnings,
                )
                validated_report = re.sub(r'\n{3,}', '\n\n', validated_report)
                t_fix.message = f"Fixed {len(all_findings)} findings, {len(validated_report)} chars"
                logger.info(f"  Report fixed: {len(validated_report)} chars ({len(all_findings)} findings addressed)")
            except Exception as e:
                t_fix.status = "warning"
                t_fix.message = f"Fix failed: {e}"
                logger.warning(f"  Report fix failed (non-blocking): {e}")
                validated_report = None

        # Step 2: Update Notion page with fixed content
        if validated_report and notion_url:
            with StepTimer(run_id, "s13_notion_update") as t_nu:
                try:
                    page_id_match = re.search(r'([0-9a-f]{32})\s*$', notion_url.replace("-", ""))
                    if page_id_match:
                        page_id = page_id_match.group(1)
                        tools.notion_update_page(page_id, content=validated_report)
                        t_nu.message = f"Notion page updated with fixed report"
                        logger.info(f"  Notion page updated with corrected report")
                    else:
                        t_nu.status = "warning"
                        t_nu.message = "Could not extract page ID from Notion URL"
                        logger.warning("  Could not extract page ID from Notion URL")
                except Exception as e:
                    t_nu.status = "warning"
                    t_nu.message = f"Notion update failed: {e}"
                    logger.warning(f"  Notion page update failed (non-blocking): {e}")

    log_step(run_id, "s13_validate", "success" if passed else "failure",
             f"{'PASS' if passed else 'FAIL'}: {len(issues)} issues, {len(warnings)} warnings"
             + (", fixed + Notion updated" if validated_report else ""),
             metadata={"issues": issues, "warnings": warnings, "fixed": validated_report is not None})

    result = {
        "VALIDATION_RESULT": {
            "passed": passed,
            "issues": issues,
            "warnings": warnings,
            "fixed": validated_report is not None,
            "checked_at": datetime.now().isoformat(),
        }
    }
    if validated_report:
        result["VALIDATED_REPORT_MARKDOWN"] = validated_report
    return result


def s14_save_and_respond(state: dict) -> dict:
    """s14 — Update SQLite run, build final response JSON."""
    logger.info("[s14] Saving + building response")

    run_id = state.get("DB_RUN_ID")

    if run_id:
        update_run_completed(run_id, state)
        feat_contacts = state.get("FEAT_CONTACTS") or []
        if feat_contacts:
            insert_contacts(run_id, state.get("FEATURED_BUYER_ID"), feat_contacts)
        logger.info(f"  run {run_id} → completed")

    elapsed = time.time() - state.get("_start_time", time.time())

    log_step(run_id, "s14_pipeline_complete", "success",
             f"total={elapsed:.1f}s",
             duration=elapsed,
             metadata={
                 "total_duration_seconds": round(elapsed, 1),
                 "buyer_name": state.get("FEATURED_BUYER_NAME"),
                 "notion_url": state.get("NOTION_PAGE_URL"),
             })

    response = {
        "status": "success",
        "buyer_id": state.get("FEATURED_BUYER_ID"),
        "buyer_name": state.get("FEATURED_BUYER_NAME"),
        "report_url": state.get("NOTION_PAGE_URL"),
        "report_markdown": state.get("REPORT_MARKDOWN"),
        "metadata": {
            "profile_available": state.get("FEAT_PROFILE") is not None,
            "contacts_count": len(state.get("FEAT_CONTACTS") or []),
            "opportunities_count": len(state.get("FEAT_OPPORTUNITIES") or []),
            "secondary_buyers": len(state.get("SECONDARY_BUYERS") or []),
            "total_signals_scanned": (
                len(state.get("DISCOVERY_SIGNALS_A") or [])
                + len(state.get("DISCOVERY_SIGNALS_B") or [])
            ),
            "validation": state.get("VALIDATION_RESULT", {}),
            "generation_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(elapsed, 1),
        },
    }

    logger.info(f"  Pipeline complete in {elapsed:.1f}s")
    return response


# ── Orchestrator ────────────────────────────────────────────────────────────

def run_pipeline(webhook: dict, stop_event=None, run_id=None) -> dict:
    """Execute the full 18-step intel brief pipeline.

    Phase I-II:  s0 → s1 (sequential — run stub created in s1)
    Phase III:   s2 (LLM sub-agent)
    Phase IV:    s3a, s3b, s3c, s3d (parallel)
    Phase V:     s4 → s5 (sequential — discovery backfilled)
    Phase VI:    4 parallel branches:
                   a) s8           — exec summary (template)
                   b) s6 → s9     — featured intel → featured section
                   c) s7 → s10    — secondary intel → secondary cards
                   d) s11          — CTA (template)
    Phase VII:   s12 → s13 → s14 (sequential — s12 shapes + publishes to Notion)

    Args:
        stop_event: threading.Event — set by /api/kill to cancel the pipeline.
        run_id: Pre-assigned DB run ID (batch mode). If provided, s1 skips
                stub creation and reuses this ID.

    On failure: partial state is persisted to SQLite, run marked 'failed',
    and the error response includes all collected data.
    """
    logger.info("=" * 60)
    logger.info("INTEL BRIEF PIPELINE — START")
    logger.info("=" * 60)

    # Register the stop event so LLM subprocess calls can be killed mid-run
    if stop_event:
        llm.set_cancel_event(stop_event)

    def _check_cancelled():
        if stop_event and stop_event.is_set():
            raise PipelineCancelled("Pipeline killed by user")

    state = {}
    pipeline_error = None

    try:
        # ── Phase I-II: sequential ──────────────────────────────────
        t0 = time.time()
        state = s0_parse_webhook(webhook)
        if run_id:
            state["DB_RUN_ID"] = run_id  # Pre-assigned (batch mode)
        s0_dur = time.time() - t0
        t1 = time.time()
        state |= s1_validate_and_load(state)
        s1_dur = time.time() - t1
        run_id = state["DB_RUN_ID"]
        # Retroactively log s0 + s1 with durations (ran before/during run_id creation)
        log_step(run_id, "s0_parse_webhook", "success",
                 f"target={state.get('target_company')} ({state.get('target_domain')})",
                 duration=s0_dur,
                 metadata={"target_company": state.get("target_company"), "target_domain": state.get("target_domain"),
                           "product_description": state.get("product_description")})
        prior = state.get("PRIOR_RUNS", [])
        log_step(run_id, "s1_validate_and_load", "success",
                 f"run_id={run_id}, prior={len(prior)}, dedup={'on' if ENABLE_PRIOR_RUN_DEDUP else 'off'}",
                 duration=s1_dur,
                 metadata={"run_id": run_id, "prior_runs": len(prior), "dedup_enabled": ENABLE_PRIOR_RUN_DEDUP})

        # ── Phase III: sequential (LLM sub-agent) ────────────────────
        _check_cancelled()
        state |= s2_search_strategy(state)

        # ── Phase IV: parallel discovery ────────────────────────────
        _check_cancelled()
        logger.info("── Phase IV: parallel discovery (s3a, s3b, s3c, s3d) ──")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_DISCOVERY) as pool:
            futures = {
                pool.submit(s3a_primary_search, state): "s3a",
                pool.submit(s3b_alternate_search, state): "s3b",
                pool.submit(s3c_buyer_type_search, state): "s3c",
                pool.submit(s3d_buyer_geo_search, state): "s3d",
            }
            for f in as_completed(futures, timeout=TIMEOUTS.get("s3a", 20)):
                label = futures[f]
                state |= f.result()
                logger.info(f"  {label} ✓")

        # ── Phase V: sequential ─────────────────────────────────────
        _check_cancelled()
        state |= s4_rank_and_select(state)
        state |= s5_persist_discovery(state)

        # ── Phase VI: 5 parallel branches ───────────────────────────
        _check_cancelled()
        logger.info("── Phase VI: parallel enrich + generate ──")

        def _branch_featured(st):
            """s6 → s9: full intel fetch, then generate featured section."""
            r6 = s6_featured_intel(st)
            r9 = s9_featured_section({**st, **r6})
            return {**r6, **r9}

        def _branch_secondary(st):
            """s7 → s10: secondary intel fetch, then generate cards."""
            r7 = s7_secondary_intel(st)
            r10 = s10_secondary_cards({**st, **r7})
            return {**r7, **r10}

        pool = ThreadPoolExecutor(max_workers=MAX_WORKERS_ENRICHMENT)
        try:
            futures = {
                pool.submit(s8_exec_summary, state): "s8 (exec summary)",
                pool.submit(_branch_featured, state): "s6→s9 (featured)",
                pool.submit(_branch_secondary, state): "s7→s10 (secondary)",
                pool.submit(s11_cta, state): "s11 (CTA)",
            }
            for f in as_completed(futures, timeout=TIMEOUTS.get("s6", 330)):
                label = futures[f]
                state |= f.result()
                logger.info(f"  {label} ✓")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

        # ── Phase VII: sequential (s12 shapes + publishes to Notion) ─
        _check_cancelled()
        state |= s12_assemble(state)
        state |= s13_validate(state)
        return s14_save_and_respond(state)

    except PipelineCancelled:
        logger.warning("Pipeline cancelled by user")
        run_id = state.get("DB_RUN_ID")
        elapsed = time.time() - state.get("_start_time", time.time())
        if run_id:
            try:
                update_run_cancelled(run_id)
                log_step(run_id, "pipeline_cancelled", "failure",
                         "Cancelled by user",
                         duration=elapsed,
                         metadata={"last_keys": sorted(state.keys())})
            except Exception as db_err:
                logger.error(f"  Failed to persist cancel state: {db_err}")
        return {
            "status": "cancelled",
            "run_id": run_id,
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "cancelled_after_seconds": round(elapsed, 1),
            },
        }

    except Exception as e:
        pipeline_error = e
        logger.error(f"Pipeline failed: {e}", exc_info=True)

        # ── Persist failure state ───────────────────────────────────
        run_id = state.get("DB_RUN_ID")
        elapsed = time.time() - state.get("_start_time", time.time())

        if run_id:
            try:
                update_run_failed(run_id, str(e), partial_state=state)
                log_step(run_id, "pipeline_failed", "failure",
                         f"{type(e).__name__}: {e}",
                         duration=elapsed,
                         metadata={"last_keys": sorted(state.keys())})
            except Exception as db_err:
                logger.error(f"  Failed to persist failure state: {db_err}")

        return {
            "status": "error",
            "error": str(e),
            "run_id": run_id,
            "partial_state": {
                k: v for k, v in state.items()
                if k not in ("_start_time",) and not callable(v)
            },
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "failed_after_seconds": round(elapsed, 1),
                "last_completed_keys": sorted(state.keys()),
            },
        }
