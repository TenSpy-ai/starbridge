"""Datagen tool layer — Starbridge custom tools (REST) and Notion MCP (SDK).

Starbridge tools are Datagen *custom deployments* — they're called via the sync
REST endpoint at api.datagen.dev/apps/{uuid}, NOT via client.execute_tool().
Long-running tools (buyer_chat) use the async endpoint: POST /apps/{uuid}/async
then poll GET /apps/run/{run_id}/output until ready (status != 202).
Notion MCP goes through the SDK.
"""

import json
import logging
import os
import time

import httpx
from datagen_sdk import DatagenClient

from .config import (
    ASYNC_DEFAULT_MAX_WAIT,
    ASYNC_POLL_INTERVAL,
    BUYER_CHAT_MAX_WAIT,
    OPPORTUNITY_SORT_FIELD,
)

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
        timeout=300,
    )

    data = resp.json()

    if not data.get("success", True):
        error_msg = data.get("error", {})
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("message", error_msg)
        raise RuntimeError(f"{tool_name} failed: {error_msg}")

    inner = data.get("data", data)
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

    return out


def _call_custom_async(tool_name, params,
                       poll_interval=ASYNC_POLL_INTERVAL,
                       max_wait=ASYNC_DEFAULT_MAX_WAIT):
    """Execute a Starbridge custom tool via async endpoint + polling.

    POST /apps/{uuid}/async → get run_id
    GET  /apps/run/{run_id}/output → poll until status != 202
    """
    uuid = _UUIDS[tool_name]
    url = f"{DATAGEN_APPS_URL}/{uuid}/async"
    headers = {"x-api-key": DATAGEN_API_KEY, "Content-Type": "application/json"}
    logger.info(f"  tool: {tool_name} (async/{uuid[:8]})")

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

    poll_url = f"https://api.datagen.dev/apps/run/{run_id}/output"
    start = time.time()

    while time.time() - start < max_wait:
        time.sleep(poll_interval)
        poll_resp = httpx.get(poll_url, headers={"x-api-key": DATAGEN_API_KEY}, timeout=15)

        if poll_resp.status_code == 202:
            continue

        poll_data = poll_resp.json()

        if not poll_data.get("success", True):
            error_msg = poll_data.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", error_msg)
            raise RuntimeError(f"{tool_name} async failed: {error_msg}")

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


# ── Starbridge Custom Tools ────────────────────────────────────────────────

def opportunity_search(search_query, types=None, page_size=40, buyer_ids=None,
                       sort_field=OPPORTUNITY_SORT_FIELD):
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


def buyer_chat(buyer_id, question, max_wait=BUYER_CHAT_MAX_WAIT):
    """AI chat about a buyer — uses async endpoint to avoid SSE timeout.

    max_wait=60s gives most responses time to complete (typical: 10-30s)
    while leaving margin within the Phase VI 90s timeout window.
    """
    return _call_custom_async(
        "starbridge_buyer_chat",
        {"buyer_id": buyer_id, "question": question},
        poll_interval=ASYNC_POLL_INTERVAL,
        max_wait=max_wait,
    )


# ── Notion MCP ──────────────────────────────────────────────────────────────

NOTION_MAX_RETRIES = 3
NOTION_RETRY_DELAYS = [2, 5, 10]  # seconds between retries


def _call_notion(tool_name, params):
    """Call a Notion MCP tool with auto-retry on transient failures (500, timeout)."""
    last_err = None
    for attempt in range(NOTION_MAX_RETRIES):
        try:
            return client.execute_tool(tool_name, params)
        except Exception as e:
            last_err = e
            err_str = str(e)
            # Retry on 500 / 502 / 503 / timeout — not on 4xx (schema/auth errors)
            transient = any(code in err_str for code in
                           ["500", "502", "503", "timeout", "ETIMEDOUT", "ECONNRESET"])
            if not transient or attempt == NOTION_MAX_RETRIES - 1:
                raise
            delay = NOTION_RETRY_DELAYS[attempt]
            logger.warning(f"  Notion {tool_name} attempt {attempt+1} failed ({type(e).__name__}), "
                           f"retrying in {delay}s...")
            time.sleep(delay)
    raise last_err  # unreachable, but keeps type checker happy


def notion_create_page(title, content, parent_page_id=None):
    params = {
        "pages": [{"properties": {"title": title}, "content": content}]
    }
    if parent_page_id:
        params["parent"] = {"page_id": parent_page_id}
    return _call_notion("mcp_Notion_notion_create_pages", params)


def notion_search(query, query_type=None):
    """Search Notion pages/databases by query string.

    query_type: "internal" (pages/databases) or "user" (people). None defaults to internal.
    Returns: list of matching pages/databases with id, title, url.
    """
    params = {"query": query}
    if query_type:
        params["query_type"] = query_type
    return _call_notion("mcp_Notion_notion_search", params)


def notion_fetch(page_id):
    """Fetch a Notion page's content by page ID."""
    return _call_notion("mcp_Notion_notion_fetch", {"id": page_id})


def notion_update_page(page_id, properties=None, content=None):
    """Update an existing Notion page's properties and/or content.

    properties: dict of property updates (e.g. {"title": "New Title"}).
    content: markdown string to replace page body.
    """
    if content:
        # Replace entire page body
        data = {"page_id": page_id, "command": "replace_content", "new_str": content}
        return _call_notion("mcp_Notion_notion_update_page", {"data": data})
    elif properties:
        data = {"page_id": page_id, "command": "update_properties", "properties": properties}
        return _call_notion("mcp_Notion_notion_update_page", {"data": data})
    else:
        raise ValueError("notion_update_page requires either properties or content")
