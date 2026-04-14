---
title: "fix-fleet-ordering"
experiment: 002-doccano-build
created: "2026-04-13 20:13 UTC"
---

## Plan: Fix Reviewer Ordering in Iterative Fleet

### Problem
Reviewer spawns alongside builders at launch time. Must only spawn after builders complete each iteration.

### Fix — 2 changes in `launch.sh`

#### Change 1: Skip reviewer in spawn loop (lines 435-510)
In the worker spawn loop, check `WORKER_TYPE` and skip reviewer-type workers. Instead, save the reviewer's spawn command for the orchestrator to use.

```bash
if [[ "${WORKER_TYPE}" == "reviewer" ]]; then
  # Save reviewer config for orchestrator to spawn on-demand
  success "  Deferred reviewer: ${WORKER_ID} (spawned by orchestrator per iteration)"
  continue
fi
```

#### Change 2: Orchestrator spawns reviewer per iteration (template at lines 150-379)
After `wait_for_workers()`, the orchestrator:
1. Spawns reviewer in a new tmux window
2. Waits for reviewer to write verdict
3. Kills reviewer tmux window after verdict (clean slate per iteration)

The orchestrator template needs a `spawn_reviewer()` function that builds the same `INNER_CMD` the launch loop would have used, but launches it on-demand.

### Implementation Detail
The reviewer's `INNER_CMD` must be baked into the orchestrator at generation time (launch.sh generates orchestrator.sh as a heredoc). Store the reviewer's full spawn command as a variable in the generated orchestrator.sh.

### Test
Add scenario I5 to `test/fleet/iterative-fleet/fixtures-claude/run-all.sh`:
- Launch fleet (not dry-run)
- Verify reviewer tmux window does NOT exist immediately after launch
- Confirms reviewer is deferred, not spawned at launch time

