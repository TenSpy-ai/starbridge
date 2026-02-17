"""SQLite operations for the pipeline — runs, discoveries, contacts tables."""

import sqlite3
import json
import os
from .config import DB_PATH


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_domain TEXT NOT NULL,
            prospect_email TEXT,
            target_company TEXT,
            product_description TEXT,
            campaign_id TEXT,
            search_strategy TEXT,
            discovery_signals_a TEXT,
            discovery_signals_b TEXT,
            discovery_buyers TEXT,
            featured_buyer_id TEXT,
            featured_buyer_name TEXT,
            secondary_buyers TEXT,
            feat_profile TEXT,
            feat_contacts TEXT,
            feat_opportunities TEXT,
            feat_ai_context TEXT,
            feat_ai_context_available INTEGER,
            sec_profiles TEXT,
            sec_contacts TEXT,
            section_exec_summary TEXT,
            section_featured TEXT,
            section_secondary TEXT,
            section_cta TEXT,
            section_footer TEXT,
            report_markdown TEXT,
            notion_url TEXT,
            status TEXT DEFAULT 'processing',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            target_domain TEXT NOT NULL,
            buyer_id TEXT,
            buyer_name TEXT,
            signal_type TEXT,
            signal_summary TEXT,
            signal_score REAL,
            discovered_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            buyer_id TEXT,
            contact_name TEXT,
            contact_title TEXT,
            contact_email TEXT,
            email_verified INTEGER,
            relevance_score REAL,
            discovered_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );

        CREATE INDEX IF NOT EXISTS idx_runs_domain ON runs(target_domain);
        CREATE INDEX IF NOT EXISTS idx_discoveries_domain ON discoveries(target_domain);
        CREATE INDEX IF NOT EXISTS idx_contacts_buyer ON contacts(buyer_id);
    """)
    conn.close()


def load_prior_runs(target_domain):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM runs WHERE target_domain = ? ORDER BY created_at DESC LIMIT 5",
        (target_domain,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_existing_insights(target_domain):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM discoveries WHERE target_domain = ? ORDER BY signal_score DESC LIMIT 50",
        (target_domain,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_run(data):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO runs (
            target_domain, prospect_email, target_company, product_description,
            campaign_id, search_strategy,
            discovery_signals_a, discovery_signals_b, discovery_buyers,
            featured_buyer_id, featured_buyer_name, secondary_buyers
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["target_domain"], data.get("prospect_email"), data.get("target_company"),
        data.get("product_description"), data.get("campaign_id"),
        json.dumps(data.get("SEARCH_STRATEGY")),
        json.dumps(data.get("DISCOVERY_SIGNALS_A")),
        json.dumps(data.get("DISCOVERY_SIGNALS_B")),
        json.dumps(data.get("DISCOVERY_BUYERS")),
        data.get("FEATURED_BUYER_ID"), data.get("FEATURED_BUYER_NAME"),
        json.dumps(data.get("SECONDARY_BUYERS")),
    ))
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id


def insert_discoveries(run_id, target_domain, all_discovered):
    conn = get_connection()
    for d in all_discovered:
        conn.execute("""
            INSERT INTO discoveries (run_id, target_domain, buyer_id, buyer_name,
                                     signal_type, signal_summary, signal_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, target_domain, d.get("buyerId"), d.get("buyerName"),
            d.get("topSignalType"), d.get("topSignalSummary", ""),
            d.get("score", 0),
        ))
    conn.commit()
    conn.close()


def update_run_completed(run_id, data):
    conn = get_connection()
    conn.execute("""
        UPDATE runs SET
            feat_profile = ?, feat_contacts = ?, feat_opportunities = ?,
            feat_ai_context = ?, feat_ai_context_available = ?,
            sec_profiles = ?, sec_contacts = ?,
            section_exec_summary = ?, section_featured = ?,
            section_secondary = ?, section_cta = ?, section_footer = ?,
            report_markdown = ?, notion_url = ?,
            status = 'completed', completed_at = datetime('now')
        WHERE id = ?
    """, (
        json.dumps(data.get("FEAT_PROFILE")),
        json.dumps(data.get("FEAT_CONTACTS")),
        json.dumps(data.get("FEAT_OPPORTUNITIES")),
        data.get("FEAT_AI_CONTEXT"),
        1 if data.get("FEAT_AI_CONTEXT_AVAILABLE") else 0,
        json.dumps(data.get("SEC_PROFILES")),
        json.dumps(data.get("SEC_CONTACTS")),
        data.get("SECTION_EXEC_SUMMARY"),
        data.get("SECTION_FEATURED"),
        data.get("SECTION_SECONDARY"),
        data.get("SECTION_CTA"),
        data.get("SECTION_FOOTER"),
        data.get("VALIDATED_REPORT_MARKDOWN") or data.get("REPORT_MARKDOWN"),
        data.get("NOTION_PAGE_URL"),
        run_id,
    ))
    conn.commit()
    conn.close()


def insert_contacts(run_id, buyer_id, contacts):
    conn = get_connection()
    for c in (contacts or []):
        conn.execute("""
            INSERT INTO contacts (run_id, buyer_id, contact_name, contact_title,
                                  contact_email, email_verified, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, buyer_id, c.get("name"), c.get("title"),
            c.get("email"), 1 if c.get("emailVerified") else 0, 0,
        ))
    conn.commit()
    conn.close()
