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
# If empty string or None, s15 skips Notion publishing entirely.
NOTION_PARENT_PAGE_ID = os.environ.get(
    "NOTION_PARENT_PAGE_ID", "30a845c1-6a83-81d8-9a22-f2360c6b1093"
)

# ── LLM config ──────────────────────────────────────────────────────────────

# Which Claude model to use for all LLM sub-agent calls (s2, s9, s10, s14).
# Passed to the `claude` CLI via --model flag. Override via env var LLM_MODEL.
# Options:
#   "claude-opus-4-6"               — highest quality (default)
#   "claude-sonnet-4-5-20250929"    — faster, cheaper, slightly lower quality
#   "claude-haiku-4-5-20251001"     — 3x faster, cheapest, lower quality
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-5-20250929")

# Max output tokens per LLM call. 4096 is plenty for report sections.
# The featured section (s9) is the longest output — typically 1500-2500 tokens.
# Bump to 8192 if you see truncated outputs.
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))

# Temperature for LLM generation. Lower = more deterministic / factual.
# 0.0–0.3 is good for structured extraction (s2) and fact-checking (s14).
# 0.3–0.7 gives more natural prose for report writing (s9, s10).
# We use a single value for all steps — 0.3 is a safe middle ground.
# Note: not used by the claude CLI backend (no temperature flag available).
LLM_TEMPERATURE = 0.3

# Max agentic turns the claude CLI can take per call. The CLI may use tool
# calls (reading files, etc.) before responding, each counting as a turn.
# 1 is too few — structured prompts often need 2-3 turns. 4 gives headroom
# without letting it spiral. Increase if you see "Reached max turns" errors.
LLM_MAX_TURNS = int(os.environ.get("LLM_MAX_TURNS", "4"))

# ── Timeouts per step (seconds) ─────────────────────────────────────────────
# Used as future.result(timeout=) in ThreadPoolExecutor. If a step exceeds its
# timeout, the future raises TimeoutError and the pipeline moves on (graceful
# degradation — the step's output is missing but the report still generates).
#
# Gotcha: the s6 timeout covers the buyer_chat async polling window. The actual
# HTTP polling happens inside tools.buyer_chat() with its own BUYER_CHAT_MAX_WAIT.
# The s6 timeout here is a safety net on top of that — set it higher than
# BUYER_CHAT_MAX_WAIT to avoid double-timeout races.

TIMEOUTS = {
    "s3a": 20,      # opportunity_search (primary keywords) — typically 3-8s
    "s3b": 20,      # opportunity_search (alternate keywords) — typically 3-8s
    "s3c": 20,      # buyer_search (type + state filters) — typically 2-5s
    "s6": 90,       # buyer_chat async polling: 10-60s typical, 90s safety net
    "s7": 20,       # buyer_profile + buyer_contacts per secondary — typically 3-5s each
    "s8": 20,       # exec summary (template, no API call) — effectively instant
    "s9": 30,       # featured section LLM generation — typically 5-15s
    "s10": 25,      # secondary cards LLM generation — typically 5-10s
    "s11": 20,      # CTA section (template, no API call) — effectively instant
    "s14": 30,      # validation: deterministic checks + LLM fact-check — 5-15s
    "s15": 15,      # Notion publish via Datagen MCP — typically 2-5s
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

# ── Secondary buyers ─────────────────────────────────────────────────────────

# How many secondary buyer cards to include in the report (after featured).
# Each secondary buyer requires 2 API calls (profile + contacts) in s7,
# so this directly affects pipeline duration. 4 is a good balance between
# report richness and speed. The s4 ranker already sorts by score, so
# buyers 5+ are diminishing returns.
MAX_SECONDARY_BUYERS = 4

# ── Thread pool sizes ────────────────────────────────────────────────────────
# ThreadPoolExecutor max_workers for each parallel phase.
# These are I/O-bound (API calls), not CPU-bound, so higher counts are fine.
# Gotcha: Datagen custom tool endpoints may rate-limit above 10 concurrent
# requests. Keep individual pool sizes under 5 to stay safe.

# Phase IV: s3a + s3b + s3c run in parallel. Always 3 — one per search type.
MAX_WORKERS_DISCOVERY = 3

# Phase VI: 5 parallel branches (s8, s6→s9, s7→s10, s11, s12).
MAX_WORKERS_ENRICHMENT = 5

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
# timeout (90s) so that buyer_chat gives up cleanly before the future
# times out. 60s covers ~95% of responses. Some complex buyers (large
# districts, agencies with lots of data) can take 60-90s — those will
# timeout and the report generates without AI context (graceful degradation).
BUYER_CHAT_MAX_WAIT = 60

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
