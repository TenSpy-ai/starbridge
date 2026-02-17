"""LLM sub-agent layer — calls Claude via the local `claude` CLI.

Each public function is a focused sub-agent with a specific role and system prompt.

Backend: `claude -p` (Claude Code CLI in print mode). Uses the OAuth token from
CLAUDE_CODE_OAUTH_TOKEN in .env — no separate API key needed.

If the claude CLI is not available or fails, the pipeline hard-fails and preserves
all state collected up to that point.
"""

import json
import logging
import os
import re
import shutil
import subprocess

from .config import LLM_MAX_TURNS, LLM_MODEL

logger = logging.getLogger("pipeline.llm")

# ── Claude CLI backend ──────────────────────────────────────────────────────

_claude_path = None
_oauth_token = None


def _init_backend():
    """Locate the claude CLI and OAuth token. Called once, cached."""
    global _claude_path, _oauth_token

    if _claude_path is not None:
        return

    path = shutil.which("claude")
    if not path:
        raise RuntimeError(
            "claude CLI not found on PATH. Install Claude Code: "
            "https://docs.anthropic.com/en/docs/claude-code"
        )

    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        raise RuntimeError(
            "CLAUDE_CODE_OAUTH_TOKEN not set. Add it to .env or export it. "
            "Generate one with: claude setup-token"
        )

    _claude_path = path
    _oauth_token = token
    logger.info(f"LLM backend: claude CLI ({path})")


def _call_llm(system_prompt: str, user_content: str, max_tokens: int = None) -> str:
    """Call Claude via the local CLI. Hard-fails on error.

    max_tokens is accepted for interface compatibility but not used by the CLI.
    """
    _init_backend()

    # Combine system + user into a single prompt for the CLI
    prompt = f"{system_prompt}\n\n---\n\n{user_content}"

    env = {
        **os.environ,
        "CLAUDE_CODE_OAUTH_TOKEN": _oauth_token,
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "128000",
    }
    env.pop("CLAUDECODE", None)  # remove to allow nested invocation

    try:
        result = subprocess.run(
            [_claude_path, "-p", "--model", LLM_MODEL, "--max-turns", str(LLM_MAX_TURNS)],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        if result.returncode != 0:
            # stderr is often empty — include stdout too for diagnostics
            detail = result.stderr.strip() or result.stdout.strip()[:500]
            raise RuntimeError(
                f"claude CLI exited {result.returncode}: {detail}"
            )

        output = result.stdout.strip()
        if not output:
            raise RuntimeError("claude CLI returned empty output")

        return output

    except subprocess.TimeoutExpired:
        raise RuntimeError("claude CLI timed out after 120s")


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
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {}


# ── Sub-agent: Search Strategy Analyst ───────────────────────────────────────

def search_strategy(target_company, target_domain, product_description,
                    campaign_signal, prior_run_count=0):
    """Analyze vendor/product → SLED segments, keywords, buyer types, opportunity types.

    Returns typed keyword lists optimized per opportunity type:
    - primary_keywords / alternate_keywords: general procurement terms
    - meeting_keywords: board-meeting agenda language for early buying intent
    - rfp_keywords: terms that appear in RFP/procurement documents
    """
    system_prompt = (
        "You are a SLED (State, Local, Education, District) procurement intelligence analyst.\n\n"
        "Analyze this vendor/product and determine which SLED buyer segments and search keywords "
        "would surface relevant procurement signals — active contracts, RFPs, board discussions, "
        "budget allocations — where this product could be a fit.\n\n"
        "Return ONLY a JSON object with these exact keys:\n"
        "{\n"
        '  "sled_segments": ["HigherEducation", ...],\n'
        '  "primary_keywords": ["keyword1", "keyword2", "keyword3"],\n'
        '  "alternate_keywords": ["keyword4", "keyword5"],\n'
        '  "meeting_keywords": ["phrase1", "phrase2", ...],\n'
        '  "rfp_keywords": ["term1", "term2", ...],\n'
        '  "buyer_types": ["HigherEducation", "SchoolDistrict"],\n'
        '  "opportunity_types": ["Meeting", "Purchase", "RFP", "Contract"],\n'
        '  "geographic_hints": ["California", ...] or [],\n'
        '  "ideal_buyer_profile": "1-sentence description"\n'
        "}\n\n"
        "Valid buyer_types: HigherEducation, SchoolDistrict, School, City, County, "
        "StateAgency, PoliceDepartment, FireDepartment, Library, SpecialDistrict\n\n"
        "Valid opportunity_types: Meeting, Purchase, RFP, Contract\n"
        "You MUST return opportunity_types — this controls which procurement signals are searched.\n"
        "Select the types most relevant to this product — include all 4 if broadly applicable, "
        "or narrow to 2-3 if the product targets specific procurement channels.\n\n"
        "KEYWORD GUIDELINES:\n\n"
        "primary_keywords (3-5): Most likely to match procurement signals overall. "
        "Should be procurement-relevant: 'career services technology' not just 'career'.\n\n"
        "alternate_keywords (2-3): Broader terms for fallback searches.\n\n"
        "meeting_keywords (up to 8): Action-oriented phrases matching board meeting agenda "
        "language — focus on PRE-procurement signals: problem identification, solution exploration, "
        "and planning activities. Use language like 'discussed challenges in [X]', "
        "'explored options for [Y]', 'requested analysis of [Z]'. Include specific service areas "
        "in the phrases. AVOID late-stage procurement language (approved contract, awarded vendor). "
        "These surface early buying intent before an RFP is issued.\n\n"
        "rfp_keywords (up to 8): Terms that appear in RFP/procurement documents — both specific "
        "product categories and general service descriptions. Include both specific and general "
        "variations. Focus on terms a procurement officer would use, not marketing language."
    )

    content = (
        f"Company: {target_company}\n"
        f"Domain: {target_domain}\n"
        f"Product Description: {product_description}\n"
        f"Campaign Signal: {campaign_signal}\n"
    )
    if prior_run_count:
        content += f"\nPrior runs found for this domain: {prior_run_count}"

    raw = _call_llm(system_prompt, content)
    strategy = _extract_json(raw)

    # Ensure required keys with sensible fallbacks
    fallback_kw = campaign_signal or target_company
    strategy.setdefault("primary_keywords", [fallback_kw])
    strategy.setdefault("alternate_keywords", [])
    strategy.setdefault("meeting_keywords", [])
    strategy.setdefault("rfp_keywords", [])
    strategy.setdefault("buyer_types", [])
    strategy.setdefault("sled_segments", strategy["buyer_types"])
    strategy.setdefault("geographic_hints", [])
    strategy.setdefault("ideal_buyer_profile", product_description[:200])

    return strategy


# ── Sub-agent: Buyer Profile Summarizer ──────────────────────────────────────

def buyer_profile_summary(buyer_name, buyer_type, profile_json, product_desc):
    """Synthesize raw buyer profile data into a structured narrative summary.

    Adapted from Starbridge's [ULTRA] Long Organization Description prompt.
    Returns a sales-focused factual profile suitable for feeding into featured_section().
    """
    system_prompt = (
        "You are a SLED procurement intelligence analyst producing a buyer profile summary.\n\n"
        "Given raw buyer profile data, produce a structured factual overview of this "
        "government/education buyer. Use ONLY the data provided — do not use outside knowledge.\n\n"
        "RULES:\n"
        "- Tone: neutral, professional, sales enablement style. No superlatives or speculation.\n"
        "- Use placeholders exactly: 'Not available in profile data' for missing fields.\n"
        "- Do NOT use 'unknown', 'likely', 'appears to', or other speculative phrasing.\n"
        "- Valid Markdown only. Use bullets and short paragraphs.\n\n"
        "OUTPUT SECTIONS (in order, skip any with no data):\n\n"
        "## [Buyer Name]: [One-line positioning]\n"
        "One sentence: what this buyer is, where, and what they oversee.\n\n"
        "## Key Attributes\n"
        "- Type, state, city, enrollment/population, fiscal year, procurement score\n"
        "- Website, phone, any other identifiers from the profile\n\n"
        "## Institutional Mission & Scope\n"
        "- What this buyer's mandate covers based on type and available data\n"
        "- Size/scale indicators (enrollment, budget, service area)\n\n"
        "## Technology & Procurement Context\n"
        "- Any technology, systems, or procurement patterns visible in the data\n"
        "- Procurement score interpretation (high = complex/slow, low = streamlined)\n\n"
        "## Relevance to [Product]\n"
        "- Why this buyer type typically needs products like the one described\n"
        "- Which departments or functions would be involved\n\n"
        "Keep the summary to 150-250 words. Focus on what a BDR needs to know before a call."
    )

    content = (
        f"BUYER: {buyer_name}\n"
        f"BUYER TYPE: {buyer_type}\n"
        f"PROSPECT PRODUCT: {product_desc}\n\n"
        f"RAW PROFILE DATA:\n{profile_json}\n"
    )

    return _call_llm(system_prompt, content)


# ── Sub-agent: Featured Buyer Report Writer ─────────────────────────────────

def featured_section(buyer_name, buyer_type, product, product_desc, campaign_signal,
                     profile_json, contacts_json, opps_json, ai_context=None):
    """Generate the featured buyer deep-dive section."""
    system_prompt = (
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
        f"BUYER PROFILE:\n{profile_json}\n\n"
        f"CONTACTS:\n{contacts_json}\n\n"
        f"OPPORTUNITIES:\n{opps_json}\n\n"
    )
    if ai_context:
        content += f"AI STRATEGIC CONTEXT:\n{ai_context}\n"

    return _call_llm(system_prompt, content)


# ── Sub-agent: Secondary Buyer Card Writer ──────────────────────────────────

def secondary_cards(product, product_desc, buyers_content):
    """Generate compact cards for secondary SLED buyers."""
    system_prompt = (
        "Generate compact buyer cards for secondary SLED buyers.\n\n"
        "For each buyer, output exactly:\n\n"
        "**[Buyer Name]** | [Type Label]\n"
        "- **Top Signal:** [Most relevant initiative, RFP, or procurement activity]\n"
        "- **Key Contact:** [Name — Title — Email] (or 'No contacts available')\n"
        "- **Relevance:** [1 sentence on why this buyer matters for the product]\n\n"
        "Keep each card to 3-4 lines. Be specific — name initiatives, not generic claims.\n"
        "Output as clean markdown. No meta-commentary."
    )

    content = f"PROSPECT PRODUCT: {product}\nPRODUCT DESCRIPTION: {product_desc}\n\n{buyers_content}"

    return _call_llm(system_prompt, content)


# ── Sub-agent: Fact Checker ─────────────────────────────────────────────────

def fact_check(buyer_name, report_text, source_data):
    """Check report for hallucinations against source data. Returns (passed, detail)."""
    system_prompt = (
        "You are a fact-checker. Compare this intelligence report against the source data.\n\n"
        "CHECK FOR material errors ONLY:\n"
        "- Contact names or emails that do NOT appear in the CONTACTS data\n"
        "- Buyer attributes (location, enrollment, scores) that contradict PROFILE data\n"
        "- Initiative names or dollar amounts NOT found in OPPORTUNITIES or AI CONTEXT\n\n"
        "IGNORE these (they are correct):\n"
        "- ALL dates including the generation date and opportunity dates\n"
        "- Aggregate counts (total signals, total buyers) — sourced separately\n"
        "- Formatting, style, section structure\n"
        "- Any information from the AI CONTEXT section (it's a trusted source)\n\n"
        "Respond with ONLY: PASS or FAIL followed by a numbered list of material factual errors."
    )

    result = _call_llm(system_prompt, source_data, max_tokens=1024)

    if isinstance(result, str) and "FAIL" in result.upper():
        return False, result[:500]
    return True, result[:200]


# ── Standalone Q&A sub-agent ────────────────────────────────────────────────

def ask(question: str, context: str = None) -> str:
    """Simple Q&A — ask Claude anything with optional context.

    Usage from Python:
        from agent.llm import ask
        answer = ask("What buyer types does Starbridge track?")

    Usage from CLI:
        python -m agent.llm "What buyer types does Starbridge track?"
    """
    system = (
        "You are a helpful assistant for the Starbridge GTM pipeline. "
        "Answer concisely and accurately."
    )
    content = question
    if context:
        content = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"

    return _call_llm(system, content)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m agent.llm \"your question here\"")
        print("       python -m agent.llm \"question\" --context \"optional context\"")
        sys.exit(1)

    question = sys.argv[1]
    ctx = None
    if "--context" in sys.argv:
        idx = sys.argv.index("--context")
        if idx + 1 < len(sys.argv):
            ctx = sys.argv[idx + 1]

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print(ask(question, ctx))
