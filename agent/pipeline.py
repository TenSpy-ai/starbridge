"""Intel brief pipeline — 19 steps from webhook to published Notion report.

3 ai_writer calls (s2, s9, s10), Starbridge tool calls (s3a, s3b, s3c, s6=profile+contacts+chat, s7×N),
1 Notion call, rest is Python logic/templates.
"""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from datetime import datetime

from . import tools
from .config import (
    BUYER_SEARCH_PAGE_SIZE,
    BUYER_TYPE_EMOJI,
    BUYER_TYPE_LABEL,
    NOTION_PARENT_PAGE_ID,
    OPPORTUNITY_PAGE_SIZE,
    TIMEOUTS,
)
from .db import (
    init_db,
    insert_contacts,
    insert_discoveries,
    insert_run,
    load_existing_insights,
    load_prior_runs,
    update_run_completed,
)

logger = logging.getLogger("pipeline")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _extract_json(text):
    """Extract first JSON object from LLM text response."""
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return {}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    # JSON in ```json ... ``` code block
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Bare JSON object
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {}


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
        "campaign_signal": webhook.get("campaign_signal", ""),
        "campaign_id": webhook.get("campaign_id", ""),
        "prospect_name": webhook.get("prospect_name", ""),
        "prospect_email": webhook.get("prospect_email", ""),
        "tier": int(webhook.get("tier", 1)),
        "_start_time": time.time(),
    }
    logger.info(f"  target: {state['target_company']} ({state['target_domain']})")
    return state


# ── Phase II: INPUT ─────────────────────────────────────────────────────────

def s1_validate_and_load(state: dict) -> dict:
    """s1 — Validate field formats, load SQLite cache."""
    logger.info("[s1] Validating inputs + loading cache")

    domain = state["target_domain"]
    if domain and not re.match(r'^[\w.-]+\.\w{2,}$', domain):
        logger.warning(f"  domain format suspect: {domain}")

    init_db()
    prior_runs = load_prior_runs(domain) if domain else []
    existing = load_existing_insights(domain) if domain else []

    logger.info(f"  prior runs: {len(prior_runs)}, cached discoveries: {len(existing)}")
    return {"PRIOR_RUNS": prior_runs, "EXISTING_INSIGHTS": existing}


# ── Phase III: ANALYZE ──────────────────────────────────────────────────────

def s2_search_strategy(state: dict) -> dict:
    """s2 — ai_writer: analyze target → SLED segments + search keywords."""
    logger.info("[s2] Generating search strategy via ai_writer")

    prompt = (
        "You are a SLED (State, Local, Education, District) procurement intelligence analyst.\n\n"
        "Analyze this vendor/product and determine which SLED buyer segments and search keywords "
        "would surface relevant procurement signals — active contracts, RFPs, board discussions, "
        "budget allocations — where this product could be a fit.\n\n"
        "Return ONLY a JSON object with these exact keys:\n"
        "{\n"
        '  "sled_segments": ["HigherEducation", ...],\n'
        '  "primary_keywords": ["keyword1", "keyword2", "keyword3"],\n'
        '  "alternate_keywords": ["keyword4", "keyword5"],\n'
        '  "buyer_types": ["HigherEducation", "SchoolDistrict"],\n'
        '  "geographic_hints": ["California", ...] or [],\n'
        '  "ideal_buyer_profile": "1-sentence description"\n'
        "}\n\n"
        "Valid buyer_types: HigherEducation, SchoolDistrict, School, City, County, "
        "StateAgency, PoliceDepartment, FireDepartment, Library, SpecialDistrict\n\n"
        "Return 3-5 primary keywords (most likely to match procurement signals) and "
        "2-3 alternate keywords (broader). Keywords should be procurement-relevant: "
        "'career services technology' not just 'career'."
    )

    content = (
        f"Company: {state['target_company']}\n"
        f"Domain: {state['target_domain']}\n"
        f"Product Description: {state['product_description']}\n"
        f"Campaign Signal: {state['campaign_signal']}\n"
    )
    if state.get("PRIOR_RUNS"):
        content += f"\nPrior runs found for this domain: {len(state['PRIOR_RUNS'])}"

    try:
        raw = tools.ai_generate(prompt, content)
        strategy = _extract_json(raw)
    except Exception as e:
        logger.error(f"  ai_writer failed: {e}")
        strategy = {}

    # Ensure required keys with sensible fallbacks
    fallback_kw = state["campaign_signal"] or state["target_company"]
    strategy.setdefault("primary_keywords", [fallback_kw])
    strategy.setdefault("alternate_keywords", [])
    strategy.setdefault("buyer_types", ["HigherEducation"])
    strategy.setdefault("sled_segments", strategy["buyer_types"])
    strategy.setdefault("geographic_hints", [])
    strategy.setdefault("ideal_buyer_profile", state["product_description"][:200])

    logger.info(f"  primary kw: {strategy['primary_keywords']}")
    logger.info(f"  alternate kw: {strategy['alternate_keywords']}")
    logger.info(f"  buyer types: {strategy['buyer_types']}")

    return {"SEARCH_STRATEGY": strategy}


# ── Phase IV: DISCOVER ──────────────────────────────────────────────────────

def s3a_primary_search(state: dict) -> dict:
    """s3a — opportunity_search with primary keywords."""
    kw = " ".join(state["SEARCH_STRATEGY"].get("primary_keywords", []))
    logger.info(f"[s3a] Opportunity search (primary): '{kw}'")

    try:
        raw = tools.opportunity_search(
            search_query=kw,
            types=["Meeting", "Purchase", "RFP", "Contract"],
            page_size=OPPORTUNITY_PAGE_SIZE,
        )
        opps = _opps_list(raw)
        logger.info(f"  → {len(opps)} results")
    except Exception as e:
        logger.error(f"  s3a failed: {e}")
        opps = []

    return {"DISCOVERY_SIGNALS_A": opps}


def s3b_alternate_search(state: dict) -> dict:
    """s3b — opportunity_search with alternate keywords."""
    kw = " ".join(state["SEARCH_STRATEGY"].get("alternate_keywords", []))
    if not kw.strip():
        logger.info("[s3b] No alternate keywords, skipping")
        return {"DISCOVERY_SIGNALS_B": []}

    logger.info(f"[s3b] Opportunity search (alternate): '{kw}'")

    try:
        raw = tools.opportunity_search(
            search_query=kw,
            types=["Meeting", "Purchase", "RFP", "Contract"],
            page_size=OPPORTUNITY_PAGE_SIZE,
        )
        opps = _opps_list(raw)
        logger.info(f"  → {len(opps)} results")
    except Exception as e:
        logger.error(f"  s3b failed: {e}")
        opps = []

    return {"DISCOVERY_SIGNALS_B": opps}


def s3c_buyer_search(state: dict) -> dict:
    """s3c — buyer_search by type + geographic hints."""
    strategy = state["SEARCH_STRATEGY"]
    buyer_types = strategy.get("buyer_types", [])
    geo = strategy.get("geographic_hints", [])
    # Use only the first keyword — long queries return 0 results on buyer search
    first_kw = (strategy.get("primary_keywords") or [""])[0]
    query = first_kw.split()[0] if first_kw else ""

    logger.info(f"[s3c] Buyer search: types={buyer_types}, query='{query}'")

    try:
        raw = tools.buyer_search(
            query=query if query else None,
            buyer_types=buyer_types or None,
            states=geo[:3] if geo else None,
            page_size=BUYER_SEARCH_PAGE_SIZE,
        )
        buyers = _buyers_list(raw)
        logger.info(f"  → {len(buyers)} buyers")
    except Exception as e:
        logger.error(f"  s3c failed: {e}")
        buyers = []

    return {"DISCOVERY_BUYERS": buyers}


# ── Phase V: SELECT ─────────────────────────────────────────────────────────

def s4_rank_and_select(state: dict) -> dict:
    """s4 — Fully deterministic: merge, dedupe, score, select featured + secondary."""
    logger.info("[s4] Ranking buyers (deterministic)")

    opps_a = state.get("DISCOVERY_SIGNALS_A") or []
    opps_b = state.get("DISCOVERY_SIGNALS_B") or []
    direct_buyers = state.get("DISCOVERY_BUYERS") or []
    all_opps = opps_a + opps_b

    # ── Build buyer → signals map from opportunity results ──
    buyer_signals = {}  # buyer_id → {name, type, signals: [opp]}
    for opp in all_opps:
        bid = opp.get("buyerId") or opp.get("buyer_id") or opp.get("id")
        bname = opp.get("buyerName") or opp.get("buyer_name") or opp.get("name", "Unknown")
        btype = opp.get("buyerType") or opp.get("buyer_type") or ""
        if not bid:
            continue
        if bid not in buyer_signals:
            buyer_signals[bid] = {"name": bname, "type": btype, "signals": []}
        buyer_signals[bid]["signals"].append(opp)

    # ── Add direct buyers from s3c (may have zero signals) ──
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
    # Weights: signal count 20%, recency 20%, urgency 15%, dollar value 10%,
    #          keyword overlap 10%, buyer type match 25%
    primary_kw = state.get("SEARCH_STRATEGY", {}).get("primary_keywords", [])
    kw_set = set(w.lower() for kw in primary_kw for w in kw.split())
    target_types = set(t.lower() for t in state.get("SEARCH_STRATEGY", {}).get("buyer_types", []))

    scored = []
    for bid, info in buyer_signals.items():
        signals = info["signals"]

        # Signal count
        sig_count = len(signals)

        # Recency — most recent signal date, normalized to 0-1 (1 = today, 0 = 1yr+ ago)
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

        # Urgency — has deadline-type signals (RFP, contract expiration)
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

        # Dollar value — max amount found
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

        # Keyword overlap — count of keyword hits in signal titles/summaries
        kw_hits = 0
        for s in signals:
            text = f"{s.get('title', '')} {s.get('summary', '')}".lower()
            kw_hits += sum(1 for w in kw_set if w in text)

        # Buyer type match — does this buyer's type match the search strategy?
        buyer_type_raw = (info["type"] or "").lower()
        # Handle comma-separated types from buyer_search (e.g. "HigherEducation, SchoolDistrict")
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
    # Weights: type match 25%, signal count 20%, recency 20%, urgency 15%, dollar 10%, kw 10%
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
        # Clean up internal scoring fields
        for k in ("_sig", "_rec", "_urg", "_dol", "_kw", "_type"):
            del s[k]

    scored.sort(key=lambda x: x["score"], reverse=True)

    featured = scored[0]
    secondary = scored[1:5]

    rationale = (
        f"Selected {featured['buyerName']} (score: {featured['score']:.3f}) "
        f"with {featured['signalCount']} signals. "
        f"Top signal: {featured['topSignalType']} — {featured['topSignalSummary'][:100]}"
    )

    logger.info(f"  Featured: {featured['buyerName']} (score={featured['score']:.3f}, signals={featured['signalCount']})")
    logger.info(f"  Secondary: {[s['buyerName'] for s in secondary]}")

    return {
        "FEATURED_BUYER_ID": featured["buyerId"],
        "FEATURED_BUYER_NAME": featured["buyerName"],
        "FEATURED_BUYER_TYPE": featured.get("buyerType", ""),
        "SECONDARY_BUYERS": secondary,
        "SELECTION_RATIONALE": rationale,
        "ALL_SCORED_BUYERS": scored,
    }


def s5_persist_discovery(state: dict) -> dict:
    """s5 — INSERT into runs + discoveries tables."""
    logger.info("[s5] Persisting discovery to SQLite")

    try:
        run_id = insert_run(state)
        all_scored = state.get("ALL_SCORED_BUYERS", [])
        insert_discoveries(run_id, state["target_domain"], all_scored)
        logger.info(f"  run_id={run_id}, {len(all_scored)} discoveries saved")
        return {"DB_RUN_ID": run_id}
    except Exception as e:
        logger.error(f"  SQLite persist failed (non-blocking): {e}")
        return {"DB_RUN_ID": None}


# ── Phase VI: ENRICH & GENERATE ────────────────────────────────────────────

def s6_featured_intel(state: dict) -> dict:
    """s6 — Parallel fetch: buyer_profile + buyer_contacts + buyer_chat for featured buyer.

    Replaces full_intel (which was just a combo of these) to avoid SSE timeout.
    Opportunities are reused from s3a/s3b discovery results — no need to re-fetch.
    """
    buyer_id = state["FEATURED_BUYER_ID"]
    buyer_name = state["FEATURED_BUYER_NAME"]
    logger.info(f"[s6] Enriching featured buyer: {buyer_name} ({buyer_id[:8]}...)")

    ai_question = (
        f"What are {buyer_name}'s key strategic priorities, recent technology initiatives, "
        f"major procurement activity, and any leadership changes in the past 12 months? "
        f"Include specific initiative names, dollar amounts, and dates where available."
    )

    profile = None
    contacts = []
    ai_ctx = None

    # Don't use `with` — its __exit__ calls shutdown(wait=True) which blocks
    # until buyer_chat's HTTP request completes, defeating our timeout.
    pool = ThreadPoolExecutor(max_workers=3)
    f_profile = pool.submit(tools.buyer_profile, buyer_id)
    f_contacts = pool.submit(tools.buyer_contacts, buyer_id, 50)
    f_ai_chat = pool.submit(tools.buyer_chat, buyer_id, ai_question)

    # Profile and contacts are fast (~1-3s)
    try:
        raw_prof = f_profile.result(timeout=TIMEOUTS.get("s7", 20))
        if isinstance(raw_prof, dict):
            profile = raw_prof.get("profile") or raw_prof
        else:
            profile = raw_prof
        logger.info("  buyer_profile ✓")
    except Exception as e:
        logger.warning(f"  buyer_profile failed: {e}")

    try:
        raw_con = f_contacts.result(timeout=TIMEOUTS.get("s7", 20))
        contacts = _contacts_list(raw_con)
        logger.info(f"  buyer_contacts ✓ ({len(contacts)})")
    except Exception as e:
        logger.warning(f"  buyer_contacts failed: {e}")

    # AI chat uses async endpoint (POST async + poll) — typically 10-30s, up to 90s.
    # The async polling handles the wait; future.result timeout is a safety net.
    try:
        raw_chat = f_ai_chat.result(timeout=TIMEOUTS.get("s6", 90))
        if isinstance(raw_chat, dict):
            ai_ctx = raw_chat.get("ai_response") or raw_chat.get("response") or raw_chat.get("answer")
            if not ai_ctx:
                ai_ctx = json.dumps(raw_chat)
        elif raw_chat:
            ai_ctx = str(raw_chat)
        logger.info(f"  buyer_chat ✓ ({len(ai_ctx or '')} chars)")
    except Exception as e:
        logger.warning(f"  buyer_chat timed out or failed (non-blocking): {e}")

    # Shutdown without waiting — let buyer_chat finish in background if still running
    pool.shutdown(wait=False, cancel_futures=True)

    # Reuse opportunities from discovery phase — filter to featured buyer
    all_opps = (state.get("DISCOVERY_SIGNALS_A") or []) + (state.get("DISCOVERY_SIGNALS_B") or [])
    opps = [o for o in all_opps if (o.get("buyerId") or o.get("buyer_id")) == buyer_id]

    ai_available = bool(ai_ctx)
    logger.info(f"  profile: {'yes' if profile else 'no'}, contacts: {len(contacts)}, "
                f"opportunities: {len(opps)}, AI: {'yes' if ai_available else 'no'}")

    return {
        "FEAT_PROFILE": profile,
        "FEAT_CONTACTS": contacts,
        "FEAT_OPPORTUNITIES": opps,
        "FEAT_AI_CONTEXT": ai_ctx,
        "FEAT_AI_CONTEXT_AVAILABLE": ai_available,
    }


def s7_secondary_intel(state: dict) -> dict:
    """s7 — buyer_profile + buyer_contacts per secondary buyer (parallel via ThreadPool)."""
    secondaries = state.get("SECONDARY_BUYERS") or []
    if not secondaries:
        logger.info("[s7] No secondary buyers, skipping")
        return {"SEC_PROFILES": [], "SEC_CONTACTS": []}

    logger.info(f"[s7] Fetching intel for {len(secondaries)} secondary buyers")

    def _fetch_one(buyer):
        bid = buyer["buyerId"]
        bname = buyer["buyerName"]
        prof, cons = None, []
        try:
            prof = tools.buyer_profile(bid)
        except Exception as e:
            logger.warning(f"  profile failed for {bname}: {e}")
        try:
            cons = _contacts_list(tools.buyer_contacts(bid, page_size=20))
        except Exception as e:
            logger.warning(f"  contacts failed for {bname}: {e}")
        return {"profile": prof, "contacts": cons, "buyerId": bid, "buyerName": bname}

    profiles = []
    contacts_out = []

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_fetch_one, b): b["buyerName"] for b in secondaries[:4]}
        try:
            for f in as_completed(futures, timeout=TIMEOUTS.get("s7", 20)):
                try:
                    r = f.result()
                    profiles.append(r["profile"])
                    contacts_out.append({
                        "buyerId": r["buyerId"],
                        "buyerName": r["buyerName"],
                        "contacts": r["contacts"],
                    })
                except Exception as e:
                    logger.warning(f"  secondary fetch error: {e}")
        except FuturesTimeout:
            logger.warning("  some secondary fetches timed out")

    logger.info(f"  fetched {len(profiles)} profiles, {len(contacts_out)} contact sets")
    return {"SEC_PROFILES": profiles, "SEC_CONTACTS": contacts_out}


def s8_exec_summary(state: dict) -> dict:
    """s8 — Template: executive summary (no LLM)."""
    logger.info("[s8] Exec summary (template)")

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

    return {"SECTION_EXEC_SUMMARY": summary}


def s9_featured_section(state: dict) -> dict:
    """s9 — ai_writer: featured buyer deep-dive (snapshot + bullets + contact + signals)."""
    logger.info("[s9] Featured buyer section via ai_writer")

    profile = state.get("FEAT_PROFILE")
    contacts = state.get("FEAT_CONTACTS") or []
    opps = state.get("FEAT_OPPORTUNITIES") or []
    ai_ctx = state.get("FEAT_AI_CONTEXT") or ""
    buyer_name = state.get("FEATURED_BUYER_NAME", "Unknown")
    buyer_type = state.get("FEATURED_BUYER_TYPE", "")
    product = state.get("target_company", "")
    product_desc = state.get("product_description", "")
    campaign_signal = state.get("campaign_signal", "")

    prompt = (
        "You are generating the Featured Buyer section for a Starbridge SLED intelligence report.\n\n"
        "CRITICAL: You MUST use ONLY the data provided below. Do NOT use any outside knowledge.\n"
        "The buyer name, profile data, contacts, and opportunities below are the ONLY source of truth.\n"
        "If a field is missing from the data, OMIT that line — do NOT guess or fill in from memory.\n\n"
        "Generate these sub-sections in order:\n\n"
        "1. **BUYER SNAPSHOT CARD** — A blockquote card with:\n"
        "   - Emoji for buyer type (🏛️=HigherEducation/StateAgency, 🏫=SchoolDistrict/School, "
        "🏙️=City, 🏢=County)\n"
        "   - Buyer name (MUST match the BUYER field below) and type label on the first line\n"
        "   - State, City, size metric (Enrollment for education, Population for government)\n"
        "   - Procurement Score (procurementHellScore, 0-100), Fiscal Year Start, Website, Phone\n"
        "   - Omit any line where data is unavailable — do NOT invent values\n\n"
        "2. **WHY THIS BUYER MATTERS** — Exactly 3 bullets. Each MUST:\n"
        "   - Reference a SPECIFIC signal from the OPPORTUNITIES data below by name/title\n"
        "   - Explain why it creates an opening for the prospect's product\n"
        "   - Be concrete enough for a BDR to reference on a phone call\n"
        '   BAD: "They invest in technology."\n'
        '   GOOD: "Board approved $2.3M demonstration project for shared data infrastructure."\n\n'
        "3. **KEY CONTACT** — Pick the single best contact from CONTACTS data below:\n"
        "   - Prefer emailVerified=true, Director+ seniority, role overlap with product\n"
        "   - Format: Name — Title — Email\n"
        "   - MUST be a contact from the provided data, not invented\n\n"
        "4. **RECENT STRATEGIC SIGNALS** — Top 3-5 signals from OPPORTUNITIES below:\n"
        "   - Each: titled paragraph (2-4 sentences)\n"
        "   - Include dates, dollar amounts, initiative names — ONLY from provided data\n"
        "   - End each with parenthetical source: *(Board meeting, Nov 2025)*\n\n"
        "Output as clean markdown. No meta-commentary. ZERO outside knowledge — data below only."
    )

    content = (
        f"PROSPECT PRODUCT: {product}\n"
        f"PRODUCT DESCRIPTION: {product_desc}\n"
        f"CAMPAIGN SIGNAL: {campaign_signal}\n\n"
        f"BUYER: {buyer_name}\n"
        f"BUYER TYPE: {buyer_type}\n\n"
        f"BUYER PROFILE:\n{json.dumps(profile, indent=2, default=str)[:3000]}\n\n"
        f"CONTACTS ({len(contacts)} total):\n{json.dumps(contacts[:20], indent=2, default=str)[:3000]}\n\n"
        f"OPPORTUNITIES ({len(opps)} total):\n{json.dumps(opps[:15], indent=2, default=str)[:4000]}\n\n"
    )
    if ai_ctx:
        content += f"AI STRATEGIC CONTEXT:\n{str(ai_ctx)[:3000]}\n"

    try:
        section = tools.ai_generate(prompt, content)
    except Exception as e:
        logger.error(f"  ai_writer failed for s9: {e}")
        emoji = BUYER_TYPE_EMOJI.get(buyer_type, "📊")
        label = BUYER_TYPE_LABEL.get(buyer_type, buyer_type)
        section = (
            f"> {emoji}\n>\n"
            f"> **{buyer_name}** | {label}\n\n"
            f"*Featured buyer section generation failed. "
            f"Data was collected ({len(contacts)} contacts, {len(opps)} opportunities) "
            f"but LLM generation encountered an error.*"
        )

    return {"SECTION_FEATURED": section}


def s10_secondary_cards(state: dict) -> dict:
    """s10 — ai_writer: compact cards for each secondary buyer."""
    secondaries = state.get("SECONDARY_BUYERS") or []
    if not secondaries:
        logger.info("[s10] No secondary buyers, skipping")
        return {"SECTION_SECONDARY": ""}

    sec_profiles = state.get("SEC_PROFILES") or []
    sec_contacts = state.get("SEC_CONTACTS") or []

    logger.info(f"[s10] Generating {len(secondaries)} secondary cards via ai_writer")

    product = state.get("target_company", "")
    product_desc = state.get("product_description", "")

    prompt = (
        "Generate compact buyer cards for secondary SLED buyers.\n\n"
        "For each buyer, output exactly:\n\n"
        "**[Buyer Name]** | [Type Label]\n"
        "- **Top Signal:** [Most relevant initiative, RFP, or procurement activity]\n"
        "- **Key Contact:** [Name — Title — Email] (or 'No contacts available')\n"
        "- **Relevance:** [1 sentence on why this buyer matters for the product]\n\n"
        "Keep each card to 3-4 lines. Be specific — name initiatives, not generic claims.\n"
        "Output as clean markdown. No meta-commentary."
    )

    content = f"PROSPECT PRODUCT: {product}\nPRODUCT DESCRIPTION: {product_desc}\n\n"

    for i, buyer in enumerate(secondaries[:4]):
        content += f"--- BUYER {i+1} ---\n"
        content += f"Name: {buyer['buyerName']} | Type: {buyer.get('buyerType', 'Unknown')}\n"
        content += f"Score: {buyer.get('score', 0):.3f} | Signals: {buyer.get('signalCount', 0)}\n"
        content += f"Top Signal: {buyer.get('topSignalType', '')} — {buyer.get('topSignalSummary', '')}\n"

        if i < len(sec_profiles) and sec_profiles[i]:
            content += f"Profile: {json.dumps(sec_profiles[i], default=str)[:800]}\n"

        matching = [sc for sc in sec_contacts if sc.get("buyerId") == buyer["buyerId"]]
        if matching and matching[0].get("contacts"):
            content += f"Contacts: {json.dumps(matching[0]['contacts'][:5], default=str)[:800]}\n"

        content += "\n"

    try:
        section = tools.ai_generate(prompt, content)
    except Exception as e:
        logger.error(f"  ai_writer failed for s10: {e}")
        cards = []
        for b in secondaries[:4]:
            label = BUYER_TYPE_LABEL.get(b.get("buyerType", ""), b.get("buyerType", ""))
            cards.append(
                f"**{b['buyerName']}** | {label}\n"
                f"- Top Signal: {b.get('topSignalSummary', 'N/A')}"
            )
        section = "\n\n".join(cards)

    return {"SECTION_SECONDARY": section}


def s11_cta(state: dict) -> dict:
    """s11 — Template: Starbridge CTA section (no LLM)."""
    logger.info("[s11] CTA (template)")

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
        f"Starbridge monitors **296,000+ government and education buyers** across all 50 states, "
        f"with **107M+ indexed board meetings and procurement records**. "
        f"For {product} targeting {seg_str} buyers, we surface:\n\n"
        f"- **Active procurement signals** — RFPs, contract expirations, board discussions, and budget allocations\n"
        f"- **Verified decision-maker contacts** — directors, VPs, superintendents, and budget authorities\n"
        f"- **AI-powered buyer analysis** — strategic context synthesized from public records and FOIA data\n\n"
        f"This scan surfaced **{total_signals} signals** across **{len(all_buyers)} buyers** "
        f"in the {seg_str} space."
    )

    return {"SECTION_CTA": cta}


def s12_footer(state: dict) -> dict:
    """s12 — Template: report footer (no LLM)."""
    logger.info("[s12] Footer (template)")

    now = datetime.now()
    month_year = now.strftime("%B %Y")
    ai_available = state.get("FEAT_AI_CONTEXT_AVAILABLE", False)

    footer = f"*Generated Starbridge Intelligence {month_year}*\n\n"
    if ai_available:
        footer += "*Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database*"
    else:
        footer += "*Data source: Starbridge buyer profile, contacts, and opportunity database. AI analysis was unavailable.*"

    return {"SECTION_FOOTER": footer}


# ── Phase VII: ASSEMBLE & VALIDATE ──────────────────────────────────────────

def s13_assemble(state: dict) -> dict:
    """s13 — Concatenate sections into final markdown report."""
    logger.info("[s13] Assembling report")

    buyer_name = state.get("FEATURED_BUYER_NAME", "Unknown")
    product = state.get("target_company", "")

    header = f"# 📊 {buyer_name} — Intelligence Report for {product}"

    # Regenerate footer here — s12 runs in parallel with s6 and may not have
    # the correct AI availability flag at generation time
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    ai_available = state.get("FEAT_AI_CONTEXT_AVAILABLE", False)
    footer = f"*Generated Starbridge Intelligence {month_year}*\n\n"
    if ai_available:
        footer += "*Data source: Starbridge buyer profile, contacts, AI analysis, and opportunity database*"
    else:
        footer += "*Data source: Starbridge buyer profile, contacts, and opportunity database. AI analysis was unavailable.*"

    sections = [
        header,
        state.get("SECTION_EXEC_SUMMARY", ""),
        state.get("SECTION_FEATURED", ""),
        state.get("SECTION_SECONDARY", ""),
        state.get("SECTION_CTA", ""),
        footer,
    ]

    parts = [s.strip() for s in sections if s and s.strip()]
    report = "\n\n---\n\n".join(parts)
    report = re.sub(r'\n{3,}', '\n\n', report)

    logger.info(f"  report assembled: {len(report)} chars, {len(parts)} sections")
    return {"REPORT_MARKDOWN": report}


def s14_validate(state: dict) -> dict:
    """s14 — 5 deterministic checks + 1 ai_writer hallucination check."""
    logger.info("[s14] Validating report")

    report = state.get("REPORT_MARKDOWN", "")
    issues = []

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

    # Check 6: ai_writer hallucination check
    try:
        check_prompt = (
            "You are a fact-checker. Compare this report against the source data below.\n\n"
            "CHECK FOR:\n"
            "- Contact names, titles, or emails that do NOT appear in the CONTACTS data\n"
            "- Buyer names, locations, or attributes that contradict the PROFILE data\n"
            "- Dollar amounts or initiative names NOT found in OPPORTUNITIES or AI CONTEXT\n"
            "- Statistics that contradict the REPORT METRICS line\n\n"
            "DO NOT FLAG:\n"
            "- Dates (the report generation date and opportunity dates are correct as provided)\n"
            "- Aggregate counts like total signals or buyers (these come from a separate data source)\n"
            "- Formatting or style choices\n\n"
            "If all factual claims about the buyer, contacts, and opportunities check out, "
            "respond with exactly: PASS\n"
            "If there are material factual errors, respond with: FAIL followed by a numbered list."
        )

        total_signals = (
            len(state.get("DISCOVERY_SIGNALS_A") or [])
            + len(state.get("DISCOVERY_SIGNALS_B") or [])
        )
        total_buyers = len(state.get("ALL_SCORED_BUYERS") or [])

        source = (
            f"BUYER: {buyer_name}\n"
            f"REPORT METRICS: {total_signals} total signals scanned, {total_buyers} total buyers found\n"
            f"NOTE: The report date 'February 2026' is CORRECT — that is the current date.\n"
            f"PROFILE: {json.dumps(state.get('FEAT_PROFILE'), default=str)[:2000]}\n"
            f"CONTACTS: {json.dumps((state.get('FEAT_CONTACTS') or [])[:10], default=str)[:1500]}\n"
            f"OPPORTUNITIES: {json.dumps((state.get('FEAT_OPPORTUNITIES') or [])[:10], default=str)[:2000]}\n"
            f"AI CONTEXT: {str(state.get('FEAT_AI_CONTEXT', ''))[:1500]}\n\n"
            f"REPORT TO CHECK:\n{report[:4000]}"
        )

        result = tools.ai_generate(check_prompt, source)
        if isinstance(result, str) and "FAIL" in result.upper():
            issues.append(f"Hallucination check: {result[:500]}")
    except Exception as e:
        logger.warning(f"  hallucination check skipped: {e}")

    passed = len(issues) == 0
    logger.info(f"  validation: {'PASS' if passed else f'FAIL ({len(issues)} issues)'}")
    for issue in issues:
        logger.warning(f"    - {issue}")

    return {
        "VALIDATION_RESULT": {
            "passed": passed,
            "issues": issues,
            "checked_at": datetime.now().isoformat(),
        }
    }


def s15_publish_notion(state: dict) -> dict:
    """s15 — Publish report to Notion via Datagen MCP."""
    logger.info("[s15] Publishing to Notion")

    if not NOTION_PARENT_PAGE_ID:
        logger.warning("  NOTION_PARENT_PAGE_ID not set — skipping Notion publish")
        return {"NOTION_PAGE_URL": None}

    buyer_name = state.get("FEATURED_BUYER_NAME", "Unknown")
    product = state.get("target_company", "")
    title = f"{buyer_name} — Intelligence Report for {product}"
    report = state.get("REPORT_MARKDOWN", "")

    try:
        result = tools.notion_create_page(
            title=title,
            content=report,
            parent_page_id=NOTION_PARENT_PAGE_ID,
        )

        # SDK returns varied structures — unwrap to find the page object
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

        logger.info(f"  Notion URL: {url}")
        return {"NOTION_PAGE_URL": url}
    except Exception as e:
        logger.error(f"  Notion publish failed: {e}")
        return {"NOTION_PAGE_URL": None}


def s16_save_and_respond(state: dict) -> dict:
    """s16 — Update SQLite run, build final response JSON."""
    logger.info("[s16] Saving + building response")

    run_id = state.get("DB_RUN_ID")

    if run_id:
        try:
            update_run_completed(run_id, state)
            feat_contacts = state.get("FEAT_CONTACTS") or []
            if feat_contacts:
                insert_contacts(run_id, state.get("FEATURED_BUYER_ID"), feat_contacts)
            logger.info(f"  run {run_id} → completed")
        except Exception as e:
            logger.error(f"  SQLite final update failed: {e}")

    elapsed = time.time() - state.get("_start_time", time.time())

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
            "ai_chat_available": state.get("FEAT_AI_CONTEXT_AVAILABLE", False),
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

def run_pipeline(webhook: dict) -> dict:
    """Execute the full 19-step intel brief pipeline.

    Phase I-II:  s0 → s1 (sequential)
    Phase III:   s2 (ai_writer)
    Phase IV:    s3a, s3b, s3c (parallel)
    Phase V:     s4 → s5 (sequential)
    Phase VI:    5 parallel branches:
                   a) s8           — exec summary (template)
                   b) s6 → s9     — featured intel → featured section
                   c) s7 → s10    — secondary intel → secondary cards
                   d) s11          — CTA (template)
                   e) s12          — footer (template)
    Phase VII:   s13 → s14 → s15 → s16 (sequential)
    """
    logger.info("=" * 60)
    logger.info("INTEL BRIEF PIPELINE — START")
    logger.info("=" * 60)

    try:
        # ── Phase I-II: sequential ──────────────────────────────────
        state = s0_parse_webhook(webhook)
        state |= s1_validate_and_load(state)

        # ── Phase III: sequential (ai_writer) ───────────────────────
        state |= s2_search_strategy(state)

        # ── Phase IV: parallel discovery ────────────────────────────
        logger.info("── Phase IV: parallel discovery (s3a, s3b, s3c) ──")
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(s3a_primary_search, state): "s3a",
                pool.submit(s3b_alternate_search, state): "s3b",
                pool.submit(s3c_buyer_search, state): "s3c",
            }
            try:
                for f in as_completed(futures, timeout=TIMEOUTS.get("s3a", 15)):
                    label = futures[f]
                    try:
                        state |= f.result()
                        logger.info(f"  {label} ✓")
                    except Exception as e:
                        logger.error(f"  {label} failed: {e}")
            except FuturesTimeout:
                logger.warning("  discovery phase timed out — proceeding with partial results")

        # ── Phase V: sequential ─────────────────────────────────────
        state |= s4_rank_and_select(state)
        state |= s5_persist_discovery(state)

        # ── Phase VI: 5 parallel branches ───────────────────────────
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

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(s8_exec_summary, state): "s8 (exec summary)",
                pool.submit(_branch_featured, state): "s6→s9 (featured)",
                pool.submit(_branch_secondary, state): "s7→s10 (secondary)",
                pool.submit(s11_cta, state): "s11 (CTA)",
                pool.submit(s12_footer, state): "s12 (footer)",
            }
            try:
                for f in as_completed(futures, timeout=TIMEOUTS.get("s6", 45)):
                    label = futures[f]
                    try:
                        state |= f.result()
                        logger.info(f"  {label} ✓")
                    except Exception as e:
                        logger.error(f"  {label} failed: {e}")
            except FuturesTimeout:
                logger.warning("  Phase VI timed out — proceeding with completed branches")

        # ── Phase VII: sequential ───────────────────────────────────
        state |= s13_assemble(state)
        state |= s14_validate(state)
        state |= s15_publish_notion(state)
        return s16_save_and_respond(state)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "generation_timestamp": datetime.now().isoformat(),
            },
        }
