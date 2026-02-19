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
import tempfile
import time

from .config import (
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MODEL,
    LLM_TOOL_TIMEOUT,
)

logger = logging.getLogger("pipeline.llm")

# ── Claude CLI backend ──────────────────────────────────────────────────────

_claude_path = None
_oauth_token = None
_cancel_event = None  # threading.Event — set by pipeline to enable kill


def set_cancel_event(event):
    """Register a threading.Event that, when set, kills any running CLI subprocess."""
    global _cancel_event
    _cancel_event = event


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


def _run_cli(cmd, prompt, env, timeout, label):
    """Run a CLI command via Popen with cancel-event polling.

    Polls every 0.5s so the process can be killed within ~500ms of
    _cancel_event being set. Raises PipelineCancelled (imported lazily to
    avoid circular import) or RuntimeError on timeout/failure.
    """
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    proc.stdin.write(prompt)
    proc.stdin.close()

    deadline = time.time() + timeout
    while proc.poll() is None:
        if _cancel_event and _cancel_event.is_set():
            proc.kill()
            proc.wait()
            from .pipeline import PipelineCancelled
            raise PipelineCancelled("Pipeline killed by user (CLI subprocess terminated)")
        if time.time() > deadline:
            proc.kill()
            proc.wait()
            raise RuntimeError(f"{label} timed out after {timeout}s")
        time.sleep(0.5)

    stdout = proc.stdout.read()
    stderr = proc.stderr.read()

    if proc.returncode != 0:
        detail = stderr.strip() or stdout.strip()[:500]
        raise RuntimeError(f"{label} exited {proc.returncode}: {detail}")

    output = stdout.strip()
    if not output:
        raise RuntimeError(f"{label} returned empty output")

    return output


def _call_llm(system_prompt: str, user_content: str, max_tokens: int = None) -> str:
    """Call Claude via the local CLI. Hard-fails on error.

    max_tokens is accepted for interface compatibility but not used by the CLI.
    Uses Popen with a poll loop so the process can be killed mid-run via _cancel_event.
    """
    _init_backend()

    prompt = f"{system_prompt}\n\n---\n\n{user_content}"

    env = {
        **os.environ,
        "CLAUDE_CODE_OAUTH_TOKEN": _oauth_token,
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(LLM_MAX_OUTPUT_TOKENS),
    }
    env.pop("CLAUDECODE", None)

    return _run_cli(
        [_claude_path, "-p", "--model", LLM_MODEL],
        prompt=prompt, env=env, timeout=300, label="claude CLI",
    )


def _build_mcp_config():
    """Build a temporary MCP config file for Datagen tool access (Notion, etc.).

    The Datagen MCP server exposes an `executeTool` meta-tool that calls
    underlying tools by alias name (e.g. mcp_Notion_notion_create_pages).
    The CLI connects via Streamable HTTP transport.

    Returns the temp file path — caller MUST clean up via os.unlink().
    """
    api_key = os.environ.get("DATAGEN_API_KEY", "")
    if not api_key:
        raise RuntimeError("DATAGEN_API_KEY not set — needed for MCP tool access")

    config = {
        "mcpServers": {
            "datagen": {
                "type": "http",
                "url": "https://mcp.datagen.dev/mcp",
                "headers": {"X-API-Key": api_key},
            }
        }
    }

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="mcp_datagen_", delete=False
    )
    json.dump(config, tmp)
    tmp.close()
    return tmp.name


def _call_llm_with_tools(
    system_prompt: str,
    user_content: str,
    mcp_config_path: str,
    allowed_tools: list = None,
    timeout: int = None,
) -> str:
    """Call Claude CLI with MCP tool access. Returns final text output.

    Like _call_llm() but adds --mcp-config and --allowedTools for MCP server
    access. Used by s12 to give the LLM direct Notion access.
    Uses Popen with a poll loop so the process can be killed mid-run via _cancel_event.
    """
    _init_backend()

    prompt = f"{system_prompt}\n\n---\n\n{user_content}"
    timeout = timeout or LLM_TOOL_TIMEOUT

    env = {
        **os.environ,
        "CLAUDE_CODE_OAUTH_TOKEN": _oauth_token,
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(LLM_MAX_OUTPUT_TOKENS),
    }
    env.pop("CLAUDECODE", None)

    cmd = [
        _claude_path,
        "-p",
        "--model", LLM_MODEL,
        "--mcp-config", mcp_config_path,
    ]
    if allowed_tools:
        cmd.extend(["--allowedTools", ",".join(allowed_tools)])

    return _run_cli(cmd, prompt=prompt, env=env, timeout=timeout, label="claude CLI (with tools)")


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
                    prior_runs=None):
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
        "variations. Focus on terms a procurement officer would use, not marketing language.\n\n"
        "If PRIOR RUNS are provided, you MUST diversify — use different keyword angles, "
        "target different buyer segments, or shift geographic focus. Do NOT repeat the same "
        "primary_keywords or buyer_types from prior runs unless no alternatives exist."
    )

    content = (
        f"Company: {target_company}\n"
        f"Domain: {target_domain}\n"
        f"Product Description: {product_description}\n"
    )
    if prior_runs:
        completed = [r for r in prior_runs if r.get("status") == "completed"]
        if completed:
            content += "\n--- PRIOR RUNS FOR THIS DOMAIN ---\n"
            content += "Diversify your strategy — avoid repeating the same keywords and buyer selections.\n\n"
            for i, r in enumerate(completed):
                content += f"Run {i+1} ({r.get('created_at', '?')}):\n"
                strat = r.get("search_strategy", "")
                if strat:
                    content += f"  Strategy: {strat[:500]}\n"
                if r.get("featured_buyer_name"):
                    content += f"  Featured: {r['featured_buyer_name']}\n"
                sec = r.get("secondary_buyers", "")
                if sec:
                    content += f"  Secondary: {sec[:300]}\n"
                content += "\n"

    raw = _call_llm(system_prompt, content)
    strategy = _extract_json(raw)

    # Ensure required keys with sensible fallbacks
    fallback_kw = target_company
    strategy.setdefault("primary_keywords", [fallback_kw])
    strategy.setdefault("alternate_keywords", [])
    strategy.setdefault("meeting_keywords", [])
    strategy.setdefault("rfp_keywords", [])
    strategy.setdefault("buyer_types", [])
    strategy.setdefault("sled_segments", strategy["buyer_types"])
    strategy.setdefault("geographic_hints", [])
    strategy.setdefault("ideal_buyer_profile", product_description[:200])

    return strategy


# ── Sub-agent: Featured Buyer Report Writer ─────────────────────────────────

def featured_section(buyer_name, buyer_type, product, product_desc,
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
        f"PRODUCT DESCRIPTION: {product_desc}\n\n"
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


# ── Sub-agent: Report Shaper + Notion Publisher (s12) ─────────────────────

def shape_and_publish_report(
    target_company, product_description,
    buyer_name, buyer_type,
    section_featured, section_secondary,
    section_exec_summary, section_cta,
    notion_parent_page_id,
):
    """Assemble intel report from pre-generated sections AND publish to Notion.

    The LLM has direct MCP tool access via the Datagen server. It:
    1. Assembles the report from sections produced by specialized sub-agents
    2. Publishes to Notion via the executeTool MCP tool
    3. Returns both the markdown and the Notion page URL

    Sections come from: s8 (exec summary), s9 (featured buyer), s10 (secondary
    cards), s11 (CTA template). Raw data generation happened upstream — this
    step only combines and publishes.

    Returns: (report_markdown: str, notion_url: str)
    Raises on failure — no fallback, pipeline hard-fails.
    """
    system_prompt = (
        "You are assembling a final SLED intelligence report from pre-generated "
        "sections and publishing it to Notion.\n\n"

        "═══ YOUR ROLE ═══\n\n"

        "You are an ASSEMBLER. Specialized sub-agents have already generated each "
        "section from raw source data. Your job is to combine them into a single, "
        "cohesive report and publish it.\n\n"

        "YOU MUST:\n"
        "1. Add the report title header: # \U0001f4ca [Buyer Name] — Intelligence Report for [Product]\n"
        "2. Include the FEATURED BUYER SECTION as-is\n"
        "3. Include the ADDITIONAL BUYERS SECTION as-is (OMIT if empty or 'No secondary buyers')\n"
        "4. Include the EXEC SUMMARY SECTION as-is\n"
        "5. Include the CTA SECTION as-is\n"
        "6. Add horizontal rules (---) between major sections\n"
        "7. Add the footer: *Generated Starbridge Intelligence [Current Month Year]*\n"
        "   followed by: *Data source: Starbridge buyer profile, contacts, and opportunity database*\n"
        "8. Publish the assembled report to Notion\n\n"

        "YOU MUST NOT:\n"
        "- Add facts, names, numbers, dates, or analysis not already in the sections\n"
        "- Remove or significantly alter content from the provided sections\n"
        "- Re-generate sections from scratch — use them as provided\n\n"

        "═══ SECTION ORDER ═══\n\n"

        "1. Title header\n"
        "2. Featured Buyer Section (buyer snapshot, signals, contacts, analysis)\n"
        "3. Additional Buyers Section (secondary buyer cards) — omit if none\n"
        "4. Exec Summary Section\n"
        "5. CTA Section\n"
        "6. Footer\n\n"

        "═══ NOTION PUBLISHING ═══\n\n"

        "After assembling the report markdown above, you MUST publish it to Notion.\n\n"
        "Use the `executeTool` MCP tool with these parameters:\n"
        "  tool_alias_name: \"mcp_Notion_notion_create_pages\"\n"
        "  parameters: {\n"
        "    \"parent\": {\"page_id\": \"" + notion_parent_page_id + "\"},\n"
        "    \"pages\": [{\n"
        "      \"properties\": {\"title\": \"[Buyer Name] — Intelligence Report for [Product]\"},\n"
        "      \"content\": \"[THE FULL ASSEMBLED REPORT MARKDOWN]\"\n"
        "    }]\n"
        "  }\n\n"

        "═══ FINAL OUTPUT FORMAT ═══\n\n"

        "After publishing to Notion, output your response in EXACTLY this format:\n"
        "1. The complete report markdown (same content you published)\n"
        "2. A delimiter line: ---NOTION_URL---\n"
        "3. The Notion page URL from the tool result on its own line\n\n"
        "If the Notion tool fails, still output the report markdown but put "
        "PUBLISH_FAILED after the delimiter.\n\n"

        "OUTPUT: The report markdown + delimiter + URL. No meta-commentary."
    )

    content = (
        f"TARGET COMPANY: {target_company}\n"
        f"PRODUCT DESCRIPTION: {product_description}\n\n"
        f"FEATURED BUYER: {buyer_name}\n"
        f"BUYER TYPE: {buyer_type}\n\n"
        f"--- FEATURED BUYER SECTION (generated by specialized sub-agent) ---\n"
        f"{section_featured}\n\n"
        f"--- ADDITIONAL BUYERS SECTION (generated by specialized sub-agent) ---\n"
        f"{section_secondary or 'No secondary buyers.'}\n\n"
        f"--- EXEC SUMMARY SECTION (generated by specialized sub-agent) ---\n"
        f"{section_exec_summary}\n\n"
        f"--- CTA SECTION (generated by template) ---\n"
        f"{section_cta}\n"
    )

    mcp_config = _build_mcp_config()

    try:
        # The Datagen MCP server exposes executeTool which calls underlying tools.
        # We allow executeTool so the LLM can publish to Notion.
        allowed_tools = ["mcp__datagen__executeTool"]

        output = _call_llm_with_tools(
            system_prompt, content,
            mcp_config_path=mcp_config,
            allowed_tools=allowed_tools,
        )

        # Parse output — split on delimiter
        if "---NOTION_URL---" in output:
            parts = output.split("---NOTION_URL---", 1)
            report_md = parts[0].strip()
            url_part = parts[1].strip()

            if "PUBLISH_FAILED" in url_part:
                raise RuntimeError("LLM reported Notion publish failed")

            notion_url = url_part.split("\n")[0].strip()
        else:
            # LLM didn't follow delimiter — try to extract URL from output
            report_md = output
            url_match = re.search(
                r"https://(?:www\.)?notion\.(?:so|site)/\S+", output
            )
            notion_url = url_match.group(0) if url_match else None

        if not notion_url or not notion_url.startswith("http"):
            raise RuntimeError(
                f"Notion URL not found in LLM output (output length: {len(output)})"
            )

        return report_md, notion_url

    finally:
        try:
            os.unlink(mcp_config)
        except OSError:
            pass


# ── Sub-agent: Fact Checker ─────────────────────────────────────────────────

def fix_report(buyer_name, report_markdown, issues, warnings):
    """Fix a report based on validation findings. Returns corrected markdown.

    Called by s13 when validation finds issues or warnings. The LLM gets the
    original report + the specific problems and must return ONLY the corrected
    report markdown — no commentary, no delimiters, no explanation.
    """
    system_prompt = (
        "You are a report editor fixing issues in a SLED intelligence report.\n\n"
        "You will receive the original report markdown and a list of issues/warnings found by validation.\n\n"
        "YOUR TASK:\n"
        "- Fix every issue listed (these are blocking problems)\n"
        "- Fix every warning listed (these are quality problems)\n"
        "- Preserve ALL other content exactly as-is — do not rewrite, restyle, or reorganize\n"
        "- If an issue mentions truncated/incomplete text, remove the broken fragment rather than guessing content\n"
        "- If an issue mentions naming contradictions, pick the more specific/correct name and use it consistently\n"
        "- If an issue mentions missing content (e.g. buyer name not in header), add it\n\n"
        "OUTPUT:\n"
        "Return ONLY the corrected report markdown. No commentary, no explanation, no delimiters.\n"
        "The output must be the complete report — not a diff or partial update."
    )

    findings = ""
    if issues:
        findings += "BLOCKING ISSUES:\n" + "\n".join(f"- {i}" for i in issues) + "\n\n"
    if warnings:
        findings += "WARNINGS:\n" + "\n".join(f"- {w}" for w in warnings) + "\n\n"

    content = (
        f"BUYER: {buyer_name}\n\n"
        f"VALIDATION FINDINGS:\n{findings}\n"
        f"ORIGINAL REPORT:\n{report_markdown}"
    )

    return _call_llm(system_prompt, content)


def fact_check(buyer_name, report_text):
    """Check report for internal consistency. Returns (passed, detail)."""
    system_prompt = (
        "You are a fact-checker reviewing a SLED intelligence report for internal consistency.\n\n"
        "CHECK FOR:\n"
        "- Contradictions within the report (e.g. buyer name differs between sections)\n"
        "- Claims that appear fabricated (generic statements with no specifics)\n"
        "- Contact information that looks malformed or placeholder-like\n"
        "- Sections that reference data not present elsewhere in the report\n\n"
        "IGNORE these (they are correct):\n"
        "- ALL dates including the generation date and opportunity dates\n"
        "- Aggregate counts (total signals, total buyers)\n"
        "- Formatting, style, section structure\n\n"
        "Respond with ONLY: PASS or FAIL followed by a numbered list of issues found."
    )

    content = f"BUYER: {buyer_name}\n\nREPORT TO CHECK:\n{report_text[:4000]}"
    result = _call_llm(system_prompt, content, max_tokens=1024)

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
