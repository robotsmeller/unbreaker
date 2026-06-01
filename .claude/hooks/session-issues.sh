#!/usr/bin/env bash
# SessionStart hook: surface open GitHub issues, grouped by work status.
#
# Status model (maps onto GitHub's native machinery):
#   fixed       = issue CLOSED        -> excluded by `is:open`, never shown
#   in progress = open + `in-progress` label
#   new         = open, no `in-progress` label (untriaged)
#
# To mark an issue in progress:  gh issue edit <N> --add-label in-progress
# Pure gh (no jq dependency). Output goes to stdout, injected into session context.

command -v gh >/dev/null 2>&1 || exit 0

TPL='{{range .}}#{{.number}} {{.title}}{{"\n"}}{{end}}'

inprog=$(gh issue list --limit 50 --search 'is:open label:in-progress' \
  --json number,title --template "$TPL" 2>/dev/null) || exit 0
fresh=$(gh issue list --limit 50 --search 'is:open -label:in-progress' \
  --json number,title --template "$TPL" 2>/dev/null)

echo '## GitHub Issues (open = new or in progress; closed/fixed ignored)'
echo '### In progress'
[ -n "$inprog" ] && echo "$inprog" || echo '(none)'
echo '### New / untriaged'
[ -n "$fresh" ] && echo "$fresh" || echo '(none)'

# Flag issues that appeared since the previous session.
cache="${CLAUDE_PROJECT_DIR:-.}/.claude/.issue-cache"
nums=$(gh issue list --state open --limit 50 --json number \
  --template '{{range .}}{{.number}}{{"\n"}}{{end}}' 2>/dev/null | sort)
if [ -f "$cache" ]; then
  newly=$(comm -13 "$cache" <(printf '%s\n' "$nums"))
  [ -n "$newly" ] && { echo '### NEW since last session:'; printf '#%s\n' $newly; }
fi
printf '%s\n' "$nums" > "$cache"
echo '---'
