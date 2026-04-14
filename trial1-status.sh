#!/usr/bin/env bash
# trial1-status.sh — One-shot status for all 9 trial1 iterative fleets
set -uo pipefail

TRIAL_ROOT="/home/sagar/doccano-fork/docs/experiments/002-doccano-build/trials/trial1"
WT_ROOT="/home/sagar/doccano-fork/worktrees"
FLEETS=(ml-service span-dedup timeout toolbar-btn health-indicator bulk-autolabel result-toast setup-script dev-compose)

G='\e[32m'; R='\e[31m'; Y='\e[33m'; B='\e[1m'; N='\e[0m'

echo -e "${B}Trial 1 Status — $(date -u '+%Y-%m-%d %H:%M:%S UTC')${N}\n"

# Table
{
  echo "FLEET|COMMITS|BUILDER|REVIEWER|B.STATE|R.STATE|ORCHESTRATOR"
  echo "─|─|─|─|─|─|─"
  for fleet in "${FLEETS[@]}"; do
    base="$TRIAL_ROOT/fleet-$fleet"
    wt="$WT_ROOT/trial1-$fleet"

    commits=$(git -C "$wt" rev-list --count master..HEAD 2>/dev/null || echo "?")

    bf="$base/workers/builder/session.jsonl"
    [ -f "$bf" ] && [ -s "$bf" ] && bsz="$(( $(wc -c < "$bf") / 1024 ))KB" || bsz="—"

    rf="$base/workers/reviewer/session.jsonl"
    [ -f "$rf" ] && [ -s "$rf" ] && rsz="$(( $(wc -c < "$rf") / 1024 ))KB" || rsz="—"

    if [ -f "$base/workers/builder/.done" ]; then bs="DONE"
    elif [ -f "$base/workers/builder/.failed" ]; then bs="FAIL"
    elif [ -f "$bf" ] && [ -s "$bf" ]; then bs="RUN"
    else bs="—"; fi

    if [ -f "$base/workers/reviewer/.done" ]; then rs="DONE"
    elif [ -f "$base/workers/reviewer/.failed" ]; then rs="FAIL"
    elif [ -f "$rf" ] && [ -s "$rf" ]; then rs="RUN"
    else rs="—"; fi

    orch=$(tmux capture-pane -t "trial1-$fleet:orchestrator" -p 2>/dev/null | grep '\[orchestrator\]' | tail -1 | sed 's/.*\] //' | head -c40)
    [ -z "$orch" ] && orch="(no tmux)"

    echo "$fleet|$commits|$bsz|$rsz|$bs|$rs|$orch"
  done
} | column -t -s'|'

# Commits
echo ""
echo -e "${B}Commits${N}"
any=0
for task in "${FLEETS[@]}"; do
  wt="$WT_ROOT/trial1-$task"
  count=$(git -C "$wt" rev-list --count master..HEAD 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    any=1
    echo -e "  ${G}$task${N} ($count):"
    git -C "$wt" log --oneline master..HEAD 2>/dev/null | sed 's/^/    /'
  fi
done
[ "$any" -eq 0 ] && echo "  (none yet)"

# Verdicts
echo ""
echo -e "${B}Verdicts${N}"
any=0
for fleet in "${FLEETS[@]}"; do
  dir="$TRIAL_ROOT/fleet-$fleet/iterations"
  while IFS= read -r rv; do
    [ -z "$rv" ] && continue
    any=1
    verdict=$(grep -i 'verdict:' "$rv" 2>/dev/null | head -1 | sed 's/.*[Vv]erdict:[[:space:]]*//' | tr -d '*')
    # Extract iter number from path: iterations/N/review.md or iterations/review-N.md
    parent=$(basename "$(dirname "$rv")")
    fname=$(basename "$rv")
    if [[ "$parent" =~ ^[0-9]+$ ]]; then
      iter="$parent"
    elif [[ "$fname" =~ review-([0-9]+) ]]; then
      iter="${BASH_REMATCH[1]}"
    else
      iter="?"
    fi
    lv=$(echo "$verdict" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
    case "$lv" in
      lgtm*)             c="$G" ;;
      iterate*|rejected*) c="$Y" ;;
      escalate*)         c="$R" ;;
      *)                 c="$N" ;;
    esac
    echo -e "  $fleet iter $iter: ${c}${verdict}${N}"
  done < <(find "$dir" -name "review*.md" 2>/dev/null | sort)
done
[ "$any" -eq 0 ] && echo "  (none yet)"

# Errors
echo ""
echo -e "${B}Errors${N}"
any=0
for fleet in "${FLEETS[@]}"; do
  for role in builder reviewer; do
    f="$TRIAL_ROOT/fleet-$fleet/workers/$role/session.jsonl"
    [ -f "$f" ] || continue
    err=$(grep '"type":"error"' "$f" 2>/dev/null | head -1)
    if [ -n "$err" ]; then
      any=1
      msg=$(echo "$err" | python3 -c "import sys,json; print(json.loads(sys.stdin.readline()).get('message','?')[:80])" 2>/dev/null || echo "?")
      echo -e "  ${R}$fleet/$role${N}: $msg"
    fi
  done
done
[ "$any" -eq 0 ] && echo -e "  ${G}none${N}"
