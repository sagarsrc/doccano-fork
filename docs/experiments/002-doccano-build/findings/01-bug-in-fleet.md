---
title: "bug-in-fleet"
experiment: 002-doccano-build
created: "2026-04-13 20:13 UTC"
---

## Bug: Reviewer Runs Before Builder in Iterative Fleet

### Observed Behavior
When launching 9 iterative fleets for trial 1, all 9 reviewers completed and wrote REJECTED verdicts within ~2 minutes, while all 9 builders were still working on their first attempt. The reviewers found no code changes and rejected — wasting ~$5.50 in reviewer budget on empty reviews.

### Root Cause
`launch.sh` (lines 435-510) spawns **all workers** into tmux windows in a sequential loop with no type filtering. Both builder and reviewer are launched simultaneously. The reviewer (claude-opus-4-6) starts immediately, finds no builder output, and writes its verdict.

The orchestrator (`orchestrator.sh`) has the correct ordering logic:
1. `wait_for_workers()` — polls for non-reviewer workers to finish
2. `wait_for_verdict()` — polls for reviewer's review.md

But the orchestrator is a **passive observer** — it doesn't control when workers start. By the time `wait_for_verdict()` runs, the reviewer already wrote its verdict minutes ago.

### Why fleet.json Didn't Protect This
The `type: "reviewer"` field in fleet.json is only used for:
- Orchestrator's `wait_for_workers()` to exclude reviewer from the "are builders done?" check
- Identifying which worker writes the verdict file

It is **never used** in `launch.sh`'s spawn loop to gate when the reviewer starts. The spawn loop at line 435 iterates all `WORKER_IDS` without checking type.

### Impact
- $5.50 wasted on 9 empty reviews
- All 9 fleets in broken state (reviewer done, builder still working, orchestrator confused)
- Had to kill all 9 fleets and restart

### Files Involved
- `/home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/launch.sh` — spawn loop (435-510), orchestrator template (150-379)
- `/home/sagar/skills-test/skills/fleet/_lib/worker-spawn.sh` — `build_inner_cmd()` function

