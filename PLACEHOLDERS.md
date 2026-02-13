# Placeholder Tagging Convention

## Tags

| Tag | Meaning | Count |
|---|---|---|
| `{{UNKNOWN: description}}` | Information completely missing — needs discovery | 223 |
| `{{UNVERIFIED: description}}` | Information inferred or assumed — needs confirmation | 38 |
| `{{TBD: description}}` | Decision not yet made — needs team alignment | 59 |

**Total open items**: 320 across 59 files

*Note: Counts are approximate and may drift as files are edited. Run the grep commands below to get the current count at any time.*

## How to Use

- Tags go **inline** where the gap exists, not in a separate section
- Always include a brief description of what's needed and ideally who to ask
- When a placeholder is resolved, **delete the tag entirely** and replace with confirmed info

## Find All Placeholders

```bash
# All placeholders
grep -rn '{{UNKNOWN\|{{UNVERIFIED\|{{TBD' . --include='*.md'

# By type
grep -rn '{{UNKNOWN' . --include='*.md'
grep -rn '{{UNVERIFIED' . --include='*.md'
grep -rn '{{TBD' . --include='*.md'

# Count by file
grep -rc '{{UNKNOWN\|{{UNVERIFIED\|{{TBD' . --include='*.md' | grep -v ':0$' | sort -t: -k2 -rn
```

## Who Resolves What

| Person | Resolves |
|---|---|
| **Kushagra** | Supabase schema, signal taxonomy, signal allocation, endgame-lookup bot internals |
| **Yurii** | Starbridge API access, auth, endpoints, DM data location |
| **Neil** | Gemini prompts, signal processing logic |
| **Nastia** | Brand assets, report template design, Webflow setup |
| **Henry** | Strategic decisions (report format, tier criteria, BDR assignment, channel priorities) |
| **Hagel** | Current process details, edge cases, manual workflow specifics |
| **Jeremy** | Technical decisions (Datagen architecture, Clay config, pipeline design) |

## Highest-Priority Unknowns (V1 Blockers)

1. Supabase table schema and column names → **Kushagra**
2. Smartlead webhook configuration and payload schema → **explore / Smartlead docs**
3. Clay workspace webhook source config → **explore workspace**
4. LLM prompt design for signal ranking → **adapt Neil's Gemini prompts**
5. Report generation tool decision (Notion vs. Super.so vs. Webflow) → **Henry / Nastia**
6. BDR assignment logic for Slack @-mentions → **Henry / Hagel**
7. Positive reply classification method in Smartlead → **explore / Smartlead docs**
