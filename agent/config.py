"""Pipeline configuration — timeouts, paths, constants."""

import os

# Paths
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pipeline.db")

# Notion parent page for publishing reports (set via env or override)
NOTION_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "30a845c1-6a83-81d8-9a22-f2360c6b1093")

# Timeouts per step (seconds) — for ThreadPoolExecutor future.result(timeout=)
TIMEOUTS = {
    "s3a": 15,
    "s3b": 15,
    "s3c": 15,
    "s6": 90,       # full_intel: 40-60s typical (AI chat SSE is bottleneck)
    "s7": 20,
    "s8": 20,
    "s9": 30,
    "s10": 25,
    "s11": 20,
    "s14": 30,
    "s15": 15,
}

# Starbridge opportunity search defaults
OPPORTUNITY_PAGE_SIZE = 40
BUYER_SEARCH_PAGE_SIZE = 25

# Buyer type emoji mapping
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
