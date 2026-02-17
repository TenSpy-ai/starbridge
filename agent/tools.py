"""Datagen tool layer — Starbridge custom tools (REST), ai_writer (SDK), Notion MCP (SDK).

Starbridge tools are Datagen *custom deployments* — they're called via the sync
REST endpoint at api.datagen.dev/apps/{uuid}, NOT via client.execute_tool().
Long-running tools (buyer_chat) use the async endpoint: POST /apps/{uuid}/async
then poll GET /apps/run/{run_id}/output until ready (status != 202).
Standard tools (ai_writer, Notion MCP) still go through the SDK.
"""

import json
import logging
import os
import time

import httpx
from datagen_sdk import DatagenClient

logger = logging.getLogger("pipeline.tools")
client = DatagenClient()

# ── Datagen REST config for custom tool sync execution ──────────────────────

DATAGEN_API_KEY = os.environ.get("DATAGEN_API_KEY", client.api_key)
DATAGEN_APPS_URL = "https://api.datagen.dev/apps"

# Starbridge custom tool UUIDs (from searchCustomTools)
_UUIDS = {
    "starbridge_opportunity_search": "c15b3524-cd08-4f7a-ae78-d73f6a6c2bad",
    "starbridge_buyer_search":      "e69f8d37-6601-4e73-a517-c8ea434b877b",
    "starbridge_buyer_profile":     "74345947-2f94-4eed-97a3-d10b2b2e3ad9",
    "starbridge_buyer_contacts":    "b81036af-1c0f-4b9a-a03b-4c301927518f",
    "starbridge_buyer_chat":        "043dc240-4517-4185-9dbb-e24ae0abf04d",
    "starbridge_full_intel":        "711d57c2-cf2e-40a5-a505-e0a5e0ee8947",
}


def _call_custom(tool_name, params):
    """Execute a Starbridge custom tool via Datagen sync REST endpoint."""
    uuid = _UUIDS[tool_name]
    url = f"{DATAGEN_APPS_URL}/{uuid}"
    logger.info(f"  tool: {tool_name} (custom/{uuid[:8]})")

    resp = httpx.post(
        url,
        headers={"x-api-key": DATAGEN_API_KEY, "Content-Type": "application/json"},
        json={"input_vars": params},
        timeout=120,
    )

    data = resp.json()

    # Sync endpoint wraps output in {"success": true, "data": {"output_vars": {...}}}
    # or returns error in {"success": false, "error": {...}}
    if not data.get("success", True):
        error_msg = data.get("error", {})
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("message", error_msg)
        raise RuntimeError(f"{tool_name} failed: {error_msg}")

    # Extract the actual output — may be nested under data.output_vars.output
    inner = data.get("data", data)
    out = inner.get("output_vars", inner)
    if isinstance(out, dict) and "output" in out:
        out = out["output"]
    # If the output is a JSON string, parse it
    if isinstance(out, str):
        try:
            out = json.loads(out)
        except (json.JSONDecodeError, TypeError):
            pass

    # Some custom tools wrap API errors in their output rather than raising
    if isinstance(out, dict) and out.get("error"):
        status = out.get("status_code", "unknown")
        raise RuntimeError(f"{tool_name}: API error {status}")

    return out


def _call_custom_async(tool_name, params, poll_interval=3, max_wait=120):
    """Execute a Starbridge custom tool via async endpoint + polling.

    POST /apps/{uuid}/async → get run_id
    GET  /apps/run/{run_id}/output → poll until status != 202
    """
    uuid = _UUIDS[tool_name]
    url = f"{DATAGEN_APPS_URL}/{uuid}/async"
    headers = {"x-api-key": DATAGEN_API_KEY, "Content-Type": "application/json"}
    logger.info(f"  tool: {tool_name} (async/{uuid[:8]})")

    # Submit async run
    resp = httpx.post(url, headers=headers, json={"input_vars": params}, timeout=30)
    data = resp.json()

    inner_data = data.get("data", {})
    run_id = (
        data.get("run_id") or data.get("run_uuid")
        or inner_data.get("run_id") or inner_data.get("run_uuid")
    )
    if not run_id:
        raise RuntimeError(f"{tool_name} async submit failed: no run_id in {data}")

    logger.info(f"  async run_id: {run_id}")

    # Poll for completion
    poll_url = f"https://api.datagen.dev/apps/run/{run_id}/output"
    start = time.time()

    while time.time() - start < max_wait:
        time.sleep(poll_interval)
        poll_resp = httpx.get(poll_url, headers={"x-api-key": DATAGEN_API_KEY}, timeout=15)

        if poll_resp.status_code == 202:
            continue  # Still pending

        poll_data = poll_resp.json()

        if not poll_data.get("success", True):
            error_msg = poll_data.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", error_msg)
            raise RuntimeError(f"{tool_name} async failed: {error_msg}")

        # Extract output (same structure as sync)
        inner = poll_data.get("data", poll_data)
        out = inner.get("output_vars", inner)
        if isinstance(out, dict) and "output" in out:
            out = out["output"]
        if isinstance(out, str):
            try:
                out = json.loads(out)
            except (json.JSONDecodeError, TypeError):
                pass

        if isinstance(out, dict) and out.get("error"):
            status = out.get("status_code", "unknown")
            raise RuntimeError(f"{tool_name}: API error {status}")

        elapsed = time.time() - start
        logger.info(f"  async complete in {elapsed:.1f}s")
        return out

    raise TimeoutError(f"{tool_name} async polling timed out after {max_wait}s")


def _call_sdk(tool_alias, params=None):
    """Execute a standard Datagen tool via the SDK."""
    logger.info(f"  tool: {tool_alias} (sdk)")
    return client.execute_tool(tool_alias, params or {})


# ── Starbridge Custom Tools ──────────────────────────────────────────────────

def opportunity_search(search_query, types=None, page_size=40, buyer_ids=None,
                       sort_field="SearchRelevancy"):
    params = {"search_query": search_query, "page_size": page_size, "sort_field": sort_field}
    if types:
        params["types"] = types
    if buyer_ids:
        params["buyer_ids"] = buyer_ids
    return _call_custom("starbridge_opportunity_search", params)


def buyer_search(query=None, buyer_types=None, states=None, page_size=25):
    params = {"page_size": page_size}
    if query:
        params["query"] = query
    if buyer_types:
        params["buyer_types"] = buyer_types
    if states:
        params["states"] = states
    return _call_custom("starbridge_buyer_search", params)


def buyer_profile(buyer_id):
    return _call_custom("starbridge_buyer_profile", {"buyer_id": buyer_id})


def buyer_contacts(buyer_id, page_size=50):
    return _call_custom("starbridge_buyer_contacts", {"buyer_id": buyer_id, "page_size": page_size})


def buyer_chat(buyer_id, question, max_wait=90):
    """AI chat about a buyer — uses async endpoint to avoid SSE timeout."""
    return _call_custom_async(
        "starbridge_buyer_chat",
        {"buyer_id": buyer_id, "question": question},
        poll_interval=3,
        max_wait=max_wait,
    )


def full_intel(search_query, ai_question=None, contact_page_size=50,
               opportunity_types=None):
    params = {
        "search_query": search_query,
        "contact_page_size": contact_page_size,
        "include_opportunities": True,
    }
    if ai_question:
        params["ai_question"] = ai_question
    if opportunity_types:
        params["opportunity_types"] = opportunity_types
    return _call_custom("starbridge_full_intel", params)


# ── AI Writer (LLM generation via Datagen) ───────────────────────────────────

def ai_generate(instruction_prompt, content):
    """Call Datagen ai_writer for LLM generation steps."""
    result = _call_sdk("ai_writer", {
        "instruction_prompt": instruction_prompt,
        "content": content,
    })
    # ai_writer returns a string directly
    if isinstance(result, dict):
        return result.get("text") or result.get("output") or json.dumps(result)
    return str(result)


# ── Notion MCP ───────────────────────────────────────────────────────────────

def notion_create_page(title, content, parent_page_id=None):
    params = {
        "pages": [{"properties": {"title": title}, "content": content}]
    }
    if parent_page_id:
        params["parent"] = {"page_id": parent_page_id}
    return _call_sdk("mcp_Notion_notion_create_pages", params)
