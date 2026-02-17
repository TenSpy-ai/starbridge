# Claude Agent SDK — Reference for Pipeline Implementation

Patterns, APIs, and best practices relevant to building the intel report pipeline as a Claude Code agent.

## Core Concepts

### Orchestrator + Subagents

The SDK supports spawning subagents via the `Task` tool. Each subagent:
- Runs in a **separate context window** (independent conversation history)
- Cannot spawn its own subagents (single level of delegation)
- Returns a single result message to the orchestrator
- Can run in parallel with other subagents

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Task", "Bash"],
    agents={
        "data-gatherer": AgentDefinition(
            description="Fetches buyer data from Starbridge API",
            prompt="You fetch data. Call the API, return structured JSON.",
            tools=["Bash"],
            model="sonnet",
        ),
    }
)

async for message in query(prompt="Run the pipeline...", options=options):
    process(message)
```

### Subagent Configuration

| Field | Purpose | Pipeline Recommendation |
|---|---|---|
| `description` | When to invoke this subagent | Be specific: "Use for Starbridge API profile lookups" |
| `prompt` | System prompt for the subagent | Single responsibility — fetch OR process OR validate |
| `tools` | Tools available to the subagent | Restrict aggressively: data-gatherer gets Bash only |
| `model` | Model to use | Sonnet for parallel API work, Opus for complex generation |

### Skills vs. Subagents

| | Subagents | Skills |
|---|---|---|
| **Definition** | Programmatic (SDK) or filesystem (`.claude/agents/`) | Filesystem only (`.claude/skills/`) |
| **Lifecycle** | Spawned on-demand via Task tool | Always available, auto-invoked |
| **Context** | Full isolation — separate conversation | Lightweight — runs in main conversation |
| **Parallelization** | Yes | No |
| **Use case** | Complex multi-step workflows | Specialized formatting/processing |

**Pipeline mapping:**
- **Subagents** for: data gathering (s3a-c, s6-s7), LLM generation (s2, s8-s11), validation
- **Skills** for: SLED signal bullet formatting, buyer type mapping

## Parallel Execution

### Spawning parallel subagents

The orchestrator invokes multiple Task tools in a single message. The SDK runs them concurrently:

```python
# Orchestrator sees all three Task calls in one turn
# SDK runs them in parallel, returns all results before next turn

# Task 1: s3a — Primary signal search
# Task 2: s3b — Alternate signal search
# Task 3: s3c — Buyer type search
```

### Wave execution for dependencies

```
Wave 1: s3a, s3b, s3c (parallel) — no dependencies
         ↓ all complete
Wave 2: s4 (sequential) — needs all Wave 1 results
         ↓
Wave 3: s6, s7 (parallel) — needs s4's buyer selection
         ↓ all complete
Wave 4: s8, s9, s10, s11 (parallel) — needs Wave 3 data
         ↓ all complete
Wave 5: s13, s14, s15, s16 (sequential)
```

### Timeout handling for parallel groups

```python
STEP_TIMEOUTS = {
    "s3a": 10,   # API search, usually <5s
    "s3b": 10,
    "s3c": 10,
    "s6":  35,   # AI chat bottleneck: 10-30s
    "s7":  15,   # 2 calls × N buyers
    "s8":  15,   # LLM generation
    "s9":  15,
    "s10": 15,
    "s11": 15,
}

# If s6's buyer_chat times out, proceed with partial data:
# FEAT_AI_CONTEXT = null, FEAT_AI_CONTEXT_AVAILABLE = false
```

## Tool Implementation

### MCP tool schema pattern

```python
@tool(
    "starbridge_opportunity_search",
    "Search Starbridge for procurement signals by keyword",
    {
        "searchQuery": str,
        "types": list,        # ["Meeting", "RFP", "Contract"]
        "buyerIds": list,     # optional — omit for discovery mode
        "pageSize": int,      # default 40
        "sortField": str,     # "SearchRelevancy"
    },
)
async def starbridge_opportunity_search(args):
    result = await client.execute_tool(
        "starbridge_opportunity_search", args
    )
    return {"content": [{"type": "text", "text": json.dumps(result)}]}
```

### Error responses

```python
# Mark errors explicitly so Claude knows to retry or degrade
return {
    "content": [{"type": "text", "text": f"API timeout: {err}"}],
    "isError": True  # Claude sees this and can decide to retry or proceed
}
```

## Hooks

### Pre-tool hooks for timeout injection

```python
async def inject_timeout_context(input_data, tool_use_id, context):
    tool = input_data["tool_name"]
    if tool == "starbridge_buyer_chat":
        return {
            "additionalContext": "This call may take 10-30s. If timeout, set FEAT_AI_CONTEXT=null and FEAT_AI_CONTEXT_AVAILABLE=false."
        }
    return {}
```

### Post-tool hooks for audit logging

```python
async def log_tool_call(input_data, tool_use_id, context):
    audit = {
        "timestamp": datetime.now().isoformat(),
        "tool": input_data["tool_name"],
        "status": "error" if input_data.get("tool_response", {}).get("isError") else "success",
    }
    await write_audit_log(audit)
    return {}
```

## Validation Loop Pattern

The s14 ↔ s11 retry loop:

```python
# ORCHESTRATOR LOGIC (pseudocode)

# Step 13: Assemble
report = assemble_sections(all_sections)

# Step 14: Validate
validation = run_validation(report, source_data)

if validation.cta_failed and retry_count < 1:
    # Re-spawn s11 subagent with feedback
    new_cta = await spawn_subagent("cta-generator", {
        "feedback": validation.cta_issues,
        "previous_cta": sections["SECTION_CTA"],
        # ... same inputs as before
    })
    sections["SECTION_CTA"] = new_cta
    report = assemble_sections(sections)  # re-run s13
    validation = run_validation(report, source_data)  # re-run s14
    retry_count += 1

# Proceed regardless — best-effort delivery
validated_report = apply_deterministic_fixes(report, validation)
```

## Cost Estimates

```
Per report (19-step pipeline):

Orchestrator (Opus):     ~15K tokens input, ~5K output   = ~$0.12
Subagents (Sonnet):      ~50K tokens input, ~15K output  = ~$0.05
API calls:               Free (Starbridge/Notion via Datagen)
SQLite:                  Free (local)
───────────────────────────────────────────────────────────
Total per report:        ~$0.15-0.20

At scale (1000 reports/month): ~$150-200/month in LLM costs
```

## Skill Definition Example

```markdown
# .claude/skills/sled-signal-formatting/SKILL.md

---
description: "Formats raw procurement signals into SLED Signal Bullets. Use when converting raw opportunity data into 1-2 sentence summaries with specific dates, amounts, and procurement context."
---

## Rules

Each bullet must:
- Lead with the specific fact (dollar amount, board action, RFP due date)
- Explain procurement timing ("contract expiring = replacement window")
- Be 1-2 sentences maximum
- Use SLED procurement language, not vendor marketing speak

## Example

Input: { type: "Contract", title: "CCCCO Common Data Platform", summary: "Board approved $2.3M demonstration project", date: "2025-11" }

Output: "Board of Governors approved a $2.3M 'demonstration project' in November 2025 to create shared data infrastructure across all 116 colleges. This procurement will likely move to full RFP in Q2 2026."
```

## Key SDK Constraints

1. **Subagents cannot spawn subagents** — only 1 level of delegation
2. **Subagents don't share context** — orchestrator must pass all needed data explicitly
3. **Parallel subagents** require all Task calls in a single orchestrator message
4. **Model override** per subagent is supported — use Sonnet for parallel work, Opus for complex generation
5. **Hooks** run on the orchestrator, not inside subagents
6. **Skills** run in the main conversation context, not isolated like subagents
