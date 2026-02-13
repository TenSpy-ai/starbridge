#!/bin/bash
# PostToolUse hook for Bash — detects mkdir commands and reminds Claude to update CLAUDE.md

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only fire on mkdir commands
if echo "$COMMAND" | grep -qE '\bmkdir\b'; then
  cat <<'EOF'
⚠️ NEW FOLDER CREATED — You MUST update the "## Repo Structure" section in CLAUDE.md to include the new folder(s), following the existing format (indented folder name + inline # comment describing its contents). Do NOT skip this step. This rule applies to folders only, not individual files.
EOF
fi

exit 0
