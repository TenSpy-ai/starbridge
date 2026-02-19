"""Pipeline configuration — timeouts, paths, constants.

Every tunable value used by the pipeline lives here. Env-var overrides are
noted where supported. When something breaks or behaves unexpectedly, this
file is the first place to check.
"""

import os

from dotenv import load_dotenv

# Load .env file from repo root (if present). This makes CLAUDE_CODE_OAUTH_TOKEN,
# DATAGEN_API_KEY, etc. available to os.environ without requiring `source .env`.
# Existing env vars take precedence — .env values don't overwrite them.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Paths ────────────────────────────────────────────────────────────────────

# SQLite database for run history, discovery cache, contacts, and audit log.
# Relative to agent/ — resolves to <repo>/data/pipeline.db.
# The data/ directory is created automatically on first run.
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pipeline.db")

# ── External service config ──────────────────────────────────────────────────

# Notion page that all generated intel reports are published under as children.
# Override via env var for a different workspace / parent page.
# To find the ID: open the parent page in Notion → Share → Copy link → extract
# the 32-char hex ID from the URL (add dashes to make UUID format).
# If empty string or None, s12 skips Notion publishing entirely.
NOTION_PARENT_PAGE_ID = os.environ.get(
    "NOTION_PARENT_PAGE_ID", "30a845c1-6a83-81d8-9a22-f2360c6b1093"
)

# ── LLM config ──────────────────────────────────────────────────────────────

# Which Claude model to use for all LLM sub-agent calls (s2, s9, s10, s13, s14).
# Passed to the `claude` CLI via --model flag.
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-opus-4-6")

# Max output tokens for the claude CLI subprocess. Set via the
# CLAUDE_CODE_MAX_OUTPUT_TOKENS env var in llm.py's subprocess env.
# Official CLI maximum is 64,000 tokens. We max it out to avoid truncation —
# the s13 report shaper can produce long reports (3,000-8,000 tokens).
# Note: this reduces the effective context window before auto-compaction.
LLM_MAX_OUTPUT_TOKENS = 64000

# Timeout for LLM sessions with MCP tool access (seconds).
# Text-only LLM: 300s hardcoded in _call_llm(). With tools: same 300s default.
LLM_TOOL_TIMEOUT = int(os.environ.get("LLM_TOOL_TIMEOUT", "300"))

# ── Timeouts per step (seconds) ─────────────────────────────────────────────
# Used as future.result(timeout=) in ThreadPoolExecutor. If a step exceeds its
# timeout, the future raises TimeoutError and the pipeline hard-fails (no
# fallbacks — the crash handler persists partial state and marks run as failed).
#
# Gotcha: the s6 timeout covers the buyer_chat async polling window. The actual
# HTTP polling happens inside tools.buyer_chat() with its own BUYER_CHAT_MAX_WAIT.
# The s6 timeout here is a safety net on top of that — set it higher than
# BUYER_CHAT_MAX_WAIT to avoid double-timeout races.

TIMEOUTS = {
    "s3a": 300,     # opportunity_search (primary keywords) — typically 3-8s
    "s3b": 300,     # opportunity_search (alternate keywords) — typically 3-8s
    "s3c": 300,     # buyer_search (buyer_types filter) — typically 2-5s
    "s3d": 300,     # buyer_search (geographic filter) — typically 2-5s
    "s6": 330,      # buyer_chat async polling + s9 LLM: up to 300s chat + 30s margin
    "s7": 300,      # buyer_profile + buyer_contacts per secondary — typically 3-5s each
    "s8": 300,      # exec summary (template, no API call) — effectively instant
    "s9": 300,      # featured section LLM generation — typically 5-15s
    "s10": 300,     # secondary cards LLM generation — typically 5-10s
    "s11": 300,     # CTA section (template, no API call) — effectively instant
    "s12": 300,     # LLM shape + Notion publish — MCP connection + tool call
    "s13": 300,     # validation: deterministic checks + LLM fact-check — 5-15s
}

# ── Opportunity search ───────────────────────────────────────────────────────

# Opportunity types are fully LLM-driven — the s2 sub-agent decides which types
# to search based on the product/campaign. Valid values the API accepts:
#   Meeting  = board meetings, committee sessions (highest volume, broad)
#   Purchase = actual purchase orders / procurement records
#   RFP      = Requests for Proposal (strongest buying intent signal)
#   Contract = existing contracts, expirations (renewal / displacement signals)
# If s2 fails entirely, the pipeline falls back to all 4 types.

# How many opportunities to fetch per search call (s3a, s3b).
# The Starbridge API caps at 100. Higher values = more signals to score but
# slower API response. 40 is a good balance — returns enough variety without
# hitting the response size limit that causes timeouts.
OPPORTUNITY_PAGE_SIZE = 40

# Sort order for opportunity results. "SearchRelevancy" is the Starbridge API's
# built-in relevance ranking. Other known option: "Date" (most recent first).
# SearchRelevancy tends to surface higher-quality matches for keyword queries.
OPPORTUNITY_SORT_FIELD = "SearchRelevancy"

# ── Buyer search ─────────────────────────────────────────────────────────────

# How many buyers to fetch in the s3c buyer_search call.
# Gotcha: buyer_search "query" field is a Name Contains filter, NOT a keyword
# search. We skip the query param entirely and rely on buyer_types + states
# filters. The page_size just controls how many matching buyers come back.
# API cap is 100.
BUYER_SEARCH_PAGE_SIZE = 25

# ── Contact limits ───────────────────────────────────────────────────────────

# How many contacts to fetch for the featured buyer (s6).
# More contacts = better chance of finding a high-quality decision-maker,
# but the API slows down above ~100. 50 is typically enough to get 2-3
# Director+ contacts with verified emails.
FEATURED_CONTACT_PAGE_SIZE = 50

# Contacts per secondary buyer (s7). Lower than featured since we only need
# one contact per card. Keeping this small makes the parallel s7 fetches faster.
SECONDARY_CONTACT_PAGE_SIZE = 20

# ── LLM context truncation limits ────────────────────────────────────────────
# These control how much source data gets passed to the LLM in each sub-agent
# call. The LLM context window is large, but stuffing too much data causes:
#   1. Slower response times (more input tokens to process)
#   2. Higher cost per call
#   3. The LLM can lose focus when context is too large — hallucination risk
#      actually increases with more data beyond a sweet spot
#
# These are CHARACTER limits (not token limits). Rough conversion: 1 token ~ 4 chars.
# So 3000 chars ~ 750 tokens of input.

# Buyer profile JSON passed to s9 featured section writer.
# Profile is usually 500-2000 chars — 3000 gives headroom for verbose profiles.
AI_PROFILE_CHAR_LIMIT = 3000

# Contact list JSON passed to s9. Truncated after AI_CONTACTS_MAX entries.
# Each contact is ~150 chars as JSON, so 20 contacts * 150 = 3000 chars.
AI_CONTACTS_CHAR_LIMIT = 3000

# Opportunities JSON passed to s9. Truncated after AI_OPPS_MAX entries.
# Opportunities are verbose (300-500 chars each), so 15 * ~300 = 4500 chars.
AI_OPPS_CHAR_LIMIT = 4000

# AI strategic context (buyer_chat response) passed to s9.
# This is free-text from the Starbridge AI — can be very long.
# 3000 chars captures the key strategic insights without flooding context.
AI_CONTEXT_CHAR_LIMIT = 3000

# Source data passed to s14 validation fact-checker (per field).
# Smaller than s9 limits because the fact-checker only needs enough to verify,
# not to generate — keeping it tight reduces false positives.
AI_VALIDATION_SOURCE_LIMIT = 2000

# Max number of contacts / opportunities to pass to the LLM (list slicing).
# Applied BEFORE character truncation. Prevents passing 50 contacts when
# the LLM only needs ~10-20 to pick a good one.
AI_CONTACTS_MAX = 20
AI_OPPS_MAX = 15

# ── Report assembly (s12) ──────────────────────────────────────────────────
# Context limits for section generators (s9, s10) that produce content from
# raw source data. s12 assembles these sections into the final report.

# Max opportunities passed to the report shaper (before char truncation).
AI_REPORT_OPPS_MAX = 20

# Character limit for opportunity signals passed to the shaper.
AI_REPORT_OPPS_CHAR_LIMIT = 6000

# Character limit for each pre-generated section (exec summary, CTA) reference.
AI_REPORT_SECTION_CHAR_LIMIT = 3000

# ── Secondary buyers ─────────────────────────────────────────────────────────

# How many secondary buyer cards to include in the report (after featured).
# Each secondary buyer requires 2 API calls (profile + contacts) in s7,
# so this directly affects pipeline duration. 4 is a good balance between
# report richness and speed. The s4 ranker already sorts by score, so
# buyers 5+ are diminishing returns.
MAX_SECONDARY_BUYERS = 4

# ── Concurrent pipeline runs ──────────────────────────────────────────────────
# Max pipelines executing simultaneously. Each run uses 3-5 API threads
# internally, so 3 concurrent runs ≈ 15 concurrent Datagen calls at peak.
# Batch uploads queue beyond this limit (semaphore-gated).
MAX_CONCURRENT_RUNS = int(os.environ.get("MAX_CONCURRENT_RUNS", "3"))

# ── Prior-run deduplication ──────────────────────────────────────────────────
# When enabled (default), s1 loads completed runs for the same domain and s2
# passes them to the LLM so it diversifies keywords, buyer segments, and
# geographic focus to avoid repeating the same analysis. When disabled, every
# run for a domain starts fresh with no awareness of prior outcomes.
ENABLE_PRIOR_RUN_DEDUP = True

# ── Thread pool sizes ────────────────────────────────────────────────────────
# ThreadPoolExecutor max_workers for each parallel phase.
# These are I/O-bound (API calls), not CPU-bound, so higher counts are fine.
# Gotcha: Datagen custom tool endpoints may rate-limit above 10 concurrent
# requests. Keep individual pool sizes under 5 to stay safe.

# Phase IV: s3a + s3b + s3c + s3d run in parallel. One per search type.
MAX_WORKERS_DISCOVERY = 4

# Phase VI: 4 parallel branches (s8, s6→s9, s7→s10, s11).
MAX_WORKERS_ENRICHMENT = 4

# s6 internal: buyer_profile + buyer_contacts + buyer_chat in parallel.
MAX_WORKERS_FEATURED = 3

# s7: one thread per secondary buyer for profile + contacts fetch.
# Set equal to MAX_SECONDARY_BUYERS to fetch all in parallel.
MAX_WORKERS_SECONDARY = 4

# ── Async polling (Datagen async endpoint) ───────────────────────────────────
# buyer_chat uses the async API to avoid SSE streaming timeouts:
#   POST /apps/{uuid}/async → returns run_id
#   GET  /apps/run/{run_id}/output → poll until status != 202
#
# Gotcha: polling too aggressively (< 2s) can trigger Datagen rate limits.
# Polling too slowly (> 10s) wastes time on fast responses.

# Seconds between poll requests. 3s is a good balance — most buyer_chat
# responses complete in 10-30s, so you'll check 3-10 times.
ASYNC_POLL_INTERVAL = 3

# Default max wait for any async tool call (seconds). Safety ceiling.
ASYNC_DEFAULT_MAX_WAIT = 120

# Max wait specifically for buyer_chat (seconds). Set lower than the s6
# timeout (330s) so that buyer_chat gives up cleanly before the future
# times out. Complex buyers (large districts, agencies with lots of data)
# can take 60-90s+. If this fires, the pipeline hard-fails — there is no
# graceful degradation. All partial state is persisted to SQLite.
BUYER_CHAT_MAX_WAIT = 300

# ── CTA copy (Starbridge marketing numbers) ─────────────────────────────────
# These appear in the "What Starbridge Can Do" section of every report.
# Update when Starbridge's data coverage changes (check with Henry/Kushagra).

CTA_BUYERS_COUNT = "296,000+"      # total SLED buyers monitored
CTA_RECORDS_COUNT = "107M+"        # total indexed board meetings + procurement records

# ── Buyer type emoji mapping ─────────────────────────────────────────────────
# Used in report headers and buyer snapshot cards. Keys must match the exact
# strings returned by the Starbridge buyer_profile and buyer_search APIs.
# If Starbridge adds new buyer types, add them here or they'll render without emoji.

BUYER_TYPE_EMOJI = {
    "HigherEducation": "\U0001f3db\ufe0f",  # 🏛️
    "SchoolDistrict": "\U0001f3eb",          # 🏫
    "City": "\U0001f3d9\ufe0f",             # 🏙️
    "County": "\U0001f3e2",                  # 🏢
    "StateAgency": "\U0001f3db\ufe0f",      # 🏛️
    "School": "\U0001f3eb",
    "PoliceDepartment": "\U0001f46e",
    "FireDepartment": "\U0001f692",
    "Library": "\U0001f4da",
    "SpecialDistrict": "\U0001f3e2",
}

# Human-readable labels for buyer types. Used in exec summary, CTA, and
# secondary cards. Same key constraint as BUYER_TYPE_EMOJI above.
BUYER_TYPE_LABEL = {
    "HigherEducation": "Higher Education",
    "SchoolDistrict": "School District",
    "City": "City",
    "County": "County",
    "StateAgency": "State Agency",
    "School": "School",
    "PoliceDepartment": "Police Department",
    "FireDepartment": "Fire Department",
    "Library": "Library",
    "SpecialDistrict": "Special District",
}

# ── State name → two-letter code ────────────────────────────────────────────
# The buyer_search API requires two-letter state codes, but the s2 LLM
# sub-agent may return full names ("California"), abbreviations ("CA"),
# or lowercase ("california"). The s3c step normalizes using this map.
# Gotcha: only US states + DC. If Starbridge expands to territories (PR, GU,
# VI, AS, MP), add them here.

STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}

# ── Config metadata (used by GET /api/config) ─────────────────────────────
# Categories and descriptions for the pipeline explorer config panel.
# Only tunables are included — reference data (STATE_CODES, BUYER_TYPE_*)
# and paths (DB_PATH) are excluded.

CONFIG_METADATA = {
    "LLM_MODEL":                    {"cat": "LLM",           "type": "str",  "desc": "Claude model for all LLM sub-agents"},
    "LLM_MAX_OUTPUT_TOKENS":        {"cat": "LLM",           "type": "int",  "desc": "Max output tokens for CLI subprocess"},
    "LLM_TOOL_TIMEOUT":             {"cat": "LLM",           "type": "int",  "desc": "Timeout for MCP tool sessions (seconds)", "unit": "s"},
    "TIMEOUTS":                     {"cat": "Timeouts",      "type": "dict", "desc": "Per-step timeout seconds"},
    "OPPORTUNITY_PAGE_SIZE":        {"cat": "Search",        "type": "int",  "desc": "Results per opportunity search call"},
    "OPPORTUNITY_SORT_FIELD":       {"cat": "Search",        "type": "str",  "desc": "Sort order for opportunity results"},
    "BUYER_SEARCH_PAGE_SIZE":       {"cat": "Search",        "type": "int",  "desc": "Results per buyer search call"},
    "FEATURED_CONTACT_PAGE_SIZE":   {"cat": "Contacts",      "type": "int",  "desc": "Contacts fetched for featured buyer"},
    "SECONDARY_CONTACT_PAGE_SIZE":  {"cat": "Contacts",      "type": "int",  "desc": "Contacts fetched per secondary buyer"},
    "AI_PROFILE_CHAR_LIMIT":        {"cat": "LLM Limits",    "type": "int",  "desc": "Profile JSON char limit for s9"},
    "AI_CONTACTS_CHAR_LIMIT":       {"cat": "LLM Limits",    "type": "int",  "desc": "Contacts JSON char limit for s9"},
    "AI_OPPS_CHAR_LIMIT":           {"cat": "LLM Limits",    "type": "int",  "desc": "Opportunities JSON char limit for s9"},
    "AI_CONTEXT_CHAR_LIMIT":        {"cat": "LLM Limits",    "type": "int",  "desc": "AI context char limit for s9"},
    "AI_VALIDATION_SOURCE_LIMIT":   {"cat": "LLM Limits",    "type": "int",  "desc": "Source data char limit for s13 fact-check"},
    "AI_CONTACTS_MAX":              {"cat": "LLM Limits",    "type": "int",  "desc": "Max contacts passed to LLM"},
    "AI_OPPS_MAX":                  {"cat": "LLM Limits",    "type": "int",  "desc": "Max opportunities passed to LLM"},
    "AI_REPORT_OPPS_MAX":           {"cat": "LLM Limits",    "type": "int",  "desc": "Max opps for report shaper (s12)"},
    "AI_REPORT_OPPS_CHAR_LIMIT":    {"cat": "LLM Limits",    "type": "int",  "desc": "Opp signals char limit for shaper"},
    "AI_REPORT_SECTION_CHAR_LIMIT": {"cat": "LLM Limits",    "type": "int",  "desc": "Section reference char limit"},
    "MAX_SECONDARY_BUYERS":         {"cat": "Pipeline",      "type": "int",  "desc": "Secondary buyer cards in report"},
    "MAX_CONCURRENT_RUNS":          {"cat": "Pipeline",      "type": "int",  "desc": "Max simultaneous pipeline runs"},
    "ENABLE_PRIOR_RUN_DEDUP":       {"cat": "Pipeline",      "type": "bool", "desc": "Diversify keywords across runs for same domain"},
    "MAX_WORKERS_DISCOVERY":        {"cat": "Thread Pools",  "type": "int",  "desc": "Phase IV pool size"},
    "MAX_WORKERS_ENRICHMENT":       {"cat": "Thread Pools",  "type": "int",  "desc": "Phase VI pool size"},
    "MAX_WORKERS_FEATURED":         {"cat": "Thread Pools",  "type": "int",  "desc": "s6 internal pool size"},
    "MAX_WORKERS_SECONDARY":        {"cat": "Thread Pools",  "type": "int",  "desc": "s7 per-buyer pool size"},
    "ASYNC_POLL_INTERVAL":          {"cat": "Async Polling", "type": "int",  "desc": "Seconds between poll requests", "unit": "s"},
    "ASYNC_DEFAULT_MAX_WAIT":       {"cat": "Async Polling", "type": "int",  "desc": "Default async tool max wait", "unit": "s"},
    "BUYER_CHAT_MAX_WAIT":          {"cat": "Async Polling", "type": "int",  "desc": "buyer_chat async max wait", "unit": "s"},
    "CTA_BUYERS_COUNT":             {"cat": "CTA Copy",      "type": "str",  "desc": "Total SLED buyers (marketing number)"},
    "CTA_RECORDS_COUNT":            {"cat": "CTA Copy",      "type": "str",  "desc": "Total indexed records (marketing number)"},
    "NOTION_PARENT_PAGE_ID":        {"cat": "External",      "type": "str",  "desc": "Notion parent page for published reports"},
}


def get_config_snapshot():
    """Return all tunable config values for the API. Reads live module state."""
    import copy
    g = globals()
    return {key: copy.deepcopy(g[key]) for key in CONFIG_METADATA if key in g}


# Factory defaults — captured once at module load. Used by reset_config().
import copy as _copy
_FACTORY_DEFAULTS = {
    key: _copy.deepcopy(val)
    for key, val in ((k, globals().get(k)) for k in CONFIG_METADATA)
    if val is not None
}


def reset_config():
    """Reset all tunable config values to factory defaults (as defined in source).

    Returns the restored snapshot. Like set_config_value, this only updates
    module globals — call apply_config_to_modules() to push to pipeline/tools/llm.
    """
    import copy
    g = globals()
    for key, val in _FACTORY_DEFAULTS.items():
        g[key] = copy.deepcopy(val)
    return get_config_snapshot()


def set_config_value(key: str, value):
    """Set a single config value at runtime. Returns (ok, error_msg).

    Validates the key exists in CONFIG_METADATA and coerces the value to
    the declared type. Changes are held in this module's globals until
    apply_config_to_modules() pushes them into the pipeline/tools/llm modules.
    """
    if key not in CONFIG_METADATA:
        return False, f"Unknown config key: {key}"

    meta = CONFIG_METADATA[key]
    declared_type = meta["type"]

    try:
        if declared_type == "int":
            value = int(value)
        elif declared_type == "str":
            value = str(value)
        elif declared_type == "bool":
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            else:
                value = bool(value)
        elif declared_type == "dict":
            if not isinstance(value, dict):
                return False, f"{key} requires a dict value"
            value = {k: int(v) for k, v in value.items()}
    except (ValueError, TypeError) as e:
        return False, f"Invalid value for {key}: {e}"

    globals()[key] = value
    return True, None


def apply_config_to_modules(snapshot=None):
    """Push config values into pipeline.py / tools.py / llm.py cached bindings.

    These modules use `from .config import X` which creates module-level copies.
    Changing config globals alone doesn't update those copies — this function
    monkey-patches them so the next run_pipeline() call sees the new values.

    If snapshot is None, reads current config globals.
    """
    if snapshot is None:
        snapshot = get_config_snapshot()

    import agent.pipeline as p
    import agent.tools as t
    import agent.llm as l
    for key, val in snapshot.items():
        for mod in (p, t, l):
            if hasattr(mod, key):
                setattr(mod, key, val)
