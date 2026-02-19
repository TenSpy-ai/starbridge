#!/usr/bin/env python3
"""Test entry point — run the intel brief pipeline with VMock webhook data."""

import json
import logging
import sys

from agent.pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    datefmt="%H:%M:%S",
)

VMOCK_WEBHOOK = {
    "target_company": "VMock",
    "target_domain": "vmock.com",
    "product_description": (
        "AI-powered career services platform for universities — resume reviews, "
        "interview prep, career readiness assessments, and employer matching"
    ),
    "campaign_id": "test_vmock_001",
    "prospect_name": "Test Prospect",
    "prospect_email": "test@vmock.com",
}


def main():
    print("\n" + "=" * 60)
    print("  VMock Test — Intel Brief Pipeline")
    print("=" * 60 + "\n")

    result = run_pipeline(VMOCK_WEBHOOK)

    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)

    # Print metadata summary
    meta = result.get("metadata", {})
    print(f"  Status:         {result.get('status')}")
    print(f"  Buyer:          {result.get('buyer_name')} ({result.get('buyer_id', 'N/A')})")
    print(f"  Notion URL:     {result.get('report_url') or 'not published'}")
    print(f"  Duration:       {meta.get('total_duration_seconds', '?')}s")
    print(f"  Signals:        {meta.get('total_signals_scanned', '?')}")
    print(f"  Contacts:       {meta.get('contacts_count', '?')}")
    print(f"  Opportunities:  {meta.get('opportunities_count', '?')}")
    print(f"  AI Chat:        {'yes' if meta.get('ai_chat_available') else 'no'}")
    print(f"  Secondaries:    {meta.get('secondary_buyers', 0)}")

    validation = meta.get("validation", {})
    print(f"  Validation:     {'PASS' if validation.get('passed') else 'FAIL'}")
    if validation.get("issues"):
        for issue in validation["issues"]:
            print(f"    FAIL: {issue}")
    if validation.get("warnings"):
        for w in validation["warnings"]:
            print(f"    WARN: {w}")

    # Print report markdown
    report = result.get("report_markdown")
    if report:
        print("\n" + "=" * 60)
        print("  REPORT MARKDOWN")
        print("=" * 60)
        print(report)

    # Dump full JSON to file for inspection
    out_path = "data/vmock_result.json"
    try:
        import os
        os.makedirs("data", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Full result saved to {out_path}")
    except Exception as e:
        print(f"\n  Could not save result: {e}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
