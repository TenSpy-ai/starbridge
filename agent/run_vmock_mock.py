#!/usr/bin/env python3
"""Test pipeline Phases V-VII with mock discovery data (bypasses Starbridge API).

Use this to validate the orchestrator flow, ai_writer prompts, assembly,
validation, and Notion publish while the STARBRIDGE_API_KEY is being refreshed.
"""

import json
import logging
import sys
import time

from agent.pipeline import (
    s0_parse_webhook,
    s1_validate_and_load,
    s2_search_strategy,
    s4_rank_and_select,
    s5_persist_discovery,
    s8_exec_summary,
    s9_featured_section,
    s10_secondary_cards,
    s11_cta,
    s12_footer,
    s13_assemble,
    s14_validate,
    s15_publish_notion,
    s16_save_and_respond,
)

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
    "campaign_signal": "career services technology",
    "campaign_id": "test_vmock_mock_001",
    "prospect_name": "Test Prospect",
    "prospect_email": "test@vmock.com",
}

# Mock discovery data — simulates what s3a/s3b/s3c would return
MOCK_SIGNALS_A = [
    {
        "id": "opp-001", "buyerId": "buyer-ccc-001", "buyerName": "California Community Colleges",
        "buyerType": "HigherEducation", "type": "Meeting",
        "title": "Board of Governors — Career Technical Education and Workforce Development",
        "summary": "Board approved new CTE pathways including AI-powered career services integration across 116 colleges",
        "date": "2026-01-15", "amount": 2300000,
    },
    {
        "id": "opp-002", "buyerId": "buyer-ccc-001", "buyerName": "California Community Colleges",
        "buyerType": "HigherEducation", "type": "RFP",
        "title": "RFP 2026-CS-001 Career Services Technology Platform",
        "summary": "Request for proposals: AI-powered career readiness and resume optimization platform",
        "date": "2026-02-01", "amount": 500000,
    },
    {
        "id": "opp-003", "buyerId": "buyer-asu-001", "buyerName": "Arizona State University",
        "buyerType": "HigherEducation", "type": "Meeting",
        "title": "Board meeting — Student Success Technology Initiatives",
        "summary": "Discussion of career services modernization and AI adoption for student outcomes",
        "date": "2025-12-10",
    },
    {
        "id": "opp-004", "buyerId": "buyer-lausd-001", "buyerName": "Los Angeles Unified School District",
        "buyerType": "SchoolDistrict", "type": "Purchase",
        "title": "Purchase Order: Career Readiness Assessment Platform",
        "summary": "Annual renewal of career assessment tools for high school students",
        "date": "2025-11-20", "amount": 150000,
    },
]

MOCK_SIGNALS_B = [
    {
        "id": "opp-005", "buyerId": "buyer-ccc-001", "buyerName": "California Community Colleges",
        "buyerType": "HigherEducation", "type": "Contract",
        "title": "Workforce Development Technology Contract Expiration",
        "summary": "Current career services platform contract expires Q3 2026. Replacement evaluation in progress.",
        "date": "2026-06-30", "amount": 800000,
    },
    {
        "id": "opp-006", "buyerId": "buyer-utsys-001", "buyerName": "University of Texas System",
        "buyerType": "HigherEducation", "type": "Meeting",
        "title": "Regents meeting — Innovation in Student Career Development",
        "summary": "Discussion of GenAI career tools for resume optimization and interview preparation",
        "date": "2026-01-25",
    },
]

MOCK_BUYERS = [
    {
        "id": "buyer-ccc-001", "buyerId": "buyer-ccc-001",
        "name": "California Community Colleges", "type": "HigherEducation",
        "stateCode": "CA", "website": "https://www.cccco.edu",
    },
    {
        "id": "buyer-asu-001", "buyerId": "buyer-asu-001",
        "name": "Arizona State University", "type": "HigherEducation",
        "stateCode": "AZ", "website": "https://www.asu.edu",
    },
]

# Mock enrichment data for s6 (featured buyer)
MOCK_FEAT_PROFILE = {
    "id": "buyer-ccc-001",
    "name": "California Community Colleges",
    "type": "HigherEducation",
    "stateCode": "CA",
    "url": "https://www.cccco.edu",
    "metadata": {
        "address": {"city": "Sacramento", "state": "CA", "zip": "95814", "phone": "(916) 322-4005"}
    },
    "extraData": {
        "enrollment": 2108927,
        "procurementHellScore": 65,
        "fiscalYearStartDate": "July 1",
        "parentName": "California Community Colleges Chancellor's Office",
    },
}

MOCK_FEAT_CONTACTS = [
    {"name": "Dr. Sonya Christian", "title": "Chancellor", "email": "schristian@cccco.edu",
     "emailVerified": True, "normalizedTitles": ["Chancellor"], "phone": "(916) 322-4005"},
    {"name": "Marty Alvarado", "title": "Executive Vice Chancellor, Educational Services",
     "email": "malvarado@cccco.edu", "emailVerified": True,
     "normalizedTitles": ["Executive Vice Chancellor"]},
    {"name": "Paul Feist", "title": "Vice Chancellor, Communications and Marketing",
     "email": "pfeist@cccco.edu", "emailVerified": True,
     "normalizedTitles": ["Vice Chancellor"]},
    {"name": "Rebecca Ruan-O'Shaughnessy", "title": "Vice Chancellor, Educational Services and Support",
     "email": "rruan@cccco.edu", "emailVerified": True,
     "normalizedTitles": ["Vice Chancellor"]},
    {"name": "Daisy Gonzales", "title": "Deputy Chancellor",
     "email": "dgonzales@cccco.edu", "emailVerified": True,
     "normalizedTitles": ["Deputy Chancellor"]},
]

MOCK_FEAT_OPPORTUNITIES = MOCK_SIGNALS_A[:2] + MOCK_SIGNALS_B[:1]

MOCK_FEAT_AI_CONTEXT = (
    "California Community Colleges (CCC) system is the largest system of higher education in the nation, "
    "serving 1.8 million students across 116 colleges. Key strategic priorities include:\n\n"
    "1. **Vision 2030** — comprehensive reform focused on closing equity gaps, with technology modernization "
    "as a core pillar. The Board of Governors approved a 'Common Cloud Data Platform' demonstration project "
    "in November 2025 ($2.3M initial funding).\n\n"
    "2. **Career Technical Education (CTE) Expansion** — Senior Advisor to the Chancellor specifically focused "
    "on 'Workforce Development, Strategic Partnerships, and GenAI.' Active procurement for career services "
    "technology across multiple colleges.\n\n"
    "3. **AB 1705 Implementation** — new transfer-level placement requirements driving demand for student "
    "support technology including career readiness assessments.\n\n"
    "Budget: $12.6B system-wide (FY 2025-26). Recent technology RFPs include LMS evaluation ($5M+) and "
    "student success analytics platforms."
)


def main():
    print("\n" + "=" * 60)
    print("  VMock Test — Mock Discovery Data (Phases V-VII)")
    print("=" * 60 + "\n")

    # ── Phase I-III: run normally (ai_writer works) ──
    state = s0_parse_webhook(VMOCK_WEBHOOK)
    state |= s1_validate_and_load(state)
    state |= s2_search_strategy(state)

    # ── Phase IV: inject mock discovery results ──
    print("\n[MOCK] Injecting mock discovery data (skipping Starbridge API calls)")
    state["DISCOVERY_SIGNALS_A"] = MOCK_SIGNALS_A
    state["DISCOVERY_SIGNALS_B"] = MOCK_SIGNALS_B
    state["DISCOVERY_BUYERS"] = MOCK_BUYERS

    # ── Phase V: rank + persist ──
    state |= s4_rank_and_select(state)
    state |= s5_persist_discovery(state)

    # ── Phase VI: inject mock enrichment + run generation ──
    print("\n[MOCK] Injecting mock enrichment data (skipping Starbridge full_intel)")
    state["FEAT_PROFILE"] = MOCK_FEAT_PROFILE
    state["FEAT_CONTACTS"] = MOCK_FEAT_CONTACTS
    state["FEAT_OPPORTUNITIES"] = MOCK_FEAT_OPPORTUNITIES
    state["FEAT_AI_CONTEXT"] = MOCK_FEAT_AI_CONTEXT
    state["FEAT_AI_CONTEXT_AVAILABLE"] = True
    state["SEC_PROFILES"] = []
    state["SEC_CONTACTS"] = []

    # Run the generation steps that use ai_writer
    print("\n[REAL] Running s8 (template), s9 (ai_writer), s10 (ai_writer), s11 (template), s12 (template)")
    state |= s8_exec_summary(state)
    state |= s9_featured_section(state)  # ai_writer — the big one
    state |= s10_secondary_cards(state)  # ai_writer for secondary buyers
    state |= s11_cta(state)
    state |= s12_footer(state)

    # ── Phase VII: assemble, validate, publish ──
    state |= s13_assemble(state)
    state |= s14_validate(state)
    state |= s15_publish_notion(state)
    result = s16_save_and_respond(state)

    # ── Output ──
    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)
    meta = result.get("metadata", {})
    print(f"  Status:         {result.get('status')}")
    print(f"  Buyer:          {result.get('buyer_name')} ({result.get('buyer_id', 'N/A')})")
    print(f"  Notion URL:     {result.get('report_url') or 'not published'}")
    print(f"  Duration:       {meta.get('total_duration_seconds', '?')}s")
    print(f"  Signals:        {meta.get('total_signals_scanned', '?')}")
    print(f"  Contacts:       {meta.get('contacts_count', '?')}")
    print(f"  AI Chat:        {'yes' if meta.get('ai_chat_available') else 'no'}")

    validation = meta.get("validation", {})
    print(f"  Validation:     {'PASS' if validation.get('passed') else 'FAIL'}")
    if validation.get("issues"):
        for issue in validation["issues"]:
            print(f"    - {issue}")

    report = result.get("report_markdown")
    if report:
        print("\n" + "=" * 60)
        print("  REPORT MARKDOWN")
        print("=" * 60)
        print(report)

    try:
        import os
        os.makedirs("data", exist_ok=True)
        with open("data/vmock_mock_result.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Full result saved to data/vmock_mock_result.json")
    except Exception as e:
        print(f"\n  Could not save result: {e}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
