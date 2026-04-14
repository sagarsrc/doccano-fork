---
title: "iterative-dag-fix"
experiment: 002-doccano-build
created: "2026-04-13 20:20 UTC"
---

## Insight: Fleet Types Are Composable Primitives

```
worktree  = isolation   (each worker gets a branch)
dag       = ordering    (depends_on between workers)
iterative = repetition  (loop until verdict)
```

These compose:
- **iterative + dag**: each iteration executes a DAG. Builder→reviewer is just the simplest DAG.
- **iterative + dag + worktree**: each iteration is a DAG, each worker in its own worktree.
- **dag + worktree**: one-shot DAG where workers are branch-isolated.

Currently these are 3 separate monolith skills. The `depends_on` field exists in dag-fleet but is ignored by iterative-fleet and worktree-fleet. That's the bug.

## The Fix

### Principle
`depends_on` in fleet.json is the **single source of truth** for worker ordering. ALL fleet types respect it. No type-based hacks (`if type == "reviewer" then defer`).

### Step 1: Extract DAG primitives into `_lib/dag.sh`

From dag-fleet/launch.sh, extract into shared lib:
- `topo_sort(fleet_json)` → returns workers in layered order
- `get_layer(worker_id, fleet_json)` → which layer a worker is in
- `get_deps(worker_id, fleet_json)` → list of depends_on IDs
- `check_deps_done(worker_id, fleet_root)` → are all deps complete?

### Step 2: Update iterative-fleet to use DAG per iteration

**launch.sh changes:**
1. Topo-sort workers at launch
2. Only spawn layer-0 workers (no deps) immediately  
3. Write sorted layer info into orchestrator

**orchestrator.sh changes:**
Each iteration:
```
for layer in 0, 1, 2, ...:
    spawn all workers in this layer
    wait for all workers in this layer to complete
iteration done → check verdict → loop or stop
```

### Step 3: Update fleet.json schema

Reviewer declares its dependency explicitly:
```json
{
  "id": "reviewer",
  "type": "reviewer",
  "depends_on": ["builder"],
  ...
}
```

No more implicit ordering from worker type. The DAG is explicit.

### Step 4: Revert the type-based hack

Remove the `if type == "reviewer"` check from the current fix. Replace with `depends_on`-aware spawn logic.

### Step 5: Update generate-trials.py

Add `depends_on: ["builder"]` to the reviewer worker in all trial fleet.json files.

### Step 6: Tests

- I5 test: update to check that layer-1 workers (with deps) are NOT spawned at launch
- New test: verify topo-sort output for basic builder→reviewer DAG
- New test: verify multi-layer DAG (a→b→c) spawns in correct order

### Future: Worktree compose

The worktree-fleet can also adopt `depends_on` from `_lib/dag.sh`. Each worker runs in its own worktree AND respects DAG ordering. This is the full compound: isolation × ordering × repetition.

