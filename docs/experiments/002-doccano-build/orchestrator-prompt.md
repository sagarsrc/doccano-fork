You are the trial orchestrator for experiment 002-doccano-build.

## Repo
~/doccano-fork (on master, clean state)

## Read these FIRST
- ~/doccano-fork/docs/experiments/002-doccano-build/plans/03-trial-harness-v3.md (the full harness plan)
- ~/doccano-fork/docs/experiments/002-doccano-build/plans/02-build-fleet-task-bundle.md (9 task descriptions)

## What's already done
- docs/ follows /doc skill convention: docs/experiments/002-doccano-build/ with plans/, findings/, checkpoints/, research/, review/, .meta.json
- Fleet files for trials 1-5 are pre-generated at docs/experiments/002-doccano-build/trials/
- Each trial has 9 fleet dirs with fleet.json + builder/reviewer prompts ready
- Generator script at docs/experiments/002-doccano-build/generate-trials.py if you need to regenerate
- 4 checkpoints already exist from prior work

## Skills you MUST use

### /doc skill (experiment index = 2)
Use `/doc` for ALL documentation. This is experiment 002, so pass index 2:
- `/doc ckpt 2 "trial1-launched"` — checkpoint after each milestone
- `/doc finding 2 "sandbox-blocks-codex"` — record observations, failures, learnings
- `/doc plan 2 "revised-approach"` — revise approach mid-trial if needed
- `/doc resume 2` — load context when starting

### /iterative-fleet skill
Use the iterative-fleet skill for ALL fleet operations:
- Launch: `bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/launch.sh <fleet-dir>`
- Status: `bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/status.sh <fleet-dir>`
- Pause: `bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/pause.sh <fleet-dir>`
- Kill: `bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/kill.sh <fleet-dir> all`

## Execute trial 1

### Step 0: Resume experiment context
`/doc resume 2`

### Step 1: Create worktrees
```
cd ~/doccano-fork
for task in ml-service span-dedup timeout toolbar-btn health-indicator bulk-autolabel result-toast setup-script dev-compose; do
  git branch trial1-${task} master
  git worktree add worktrees/trial1-${task} trial1-${task}
done
```

### Step 2: Launch 9 fleets
For each task:
```
bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/launch.sh \
  ~/doccano-fork/docs/experiments/002-doccano-build/trials/trial1/fleet-{task}
```

Then `/doc ckpt 2 "trial1-launched"` — write body with fleet names, tmux sessions, budget

### Step 3: Monitor
Check status periodically for all 9:
```
bash /home/sagar/skills-test/skills/fleet/iterative-fleet/scripts/status.sh \
  ~/doccano-fork/docs/experiments/002-doccano-build/trials/trial1/fleet-{task}
```

Wait for all 9 to complete (builder DONE + reviewer verdict written).

### Step 4: Merge
When all 9 are done:
- Read all 9 completion reports at docs/experiments/002-doccano-build/trials/trial1/fleet-{task}/iterations/completion-report.md
- Create trial1 branch: `git checkout -b trial1 master`
- Merge each task branch into trial1, resolving conflicts using completion reports
- Run full test suite on merged trial1
- Write docs/experiments/002-doccano-build/trials/trial1/summary.md with per-task results
- `/doc ckpt 2 "trial1-merged"` with test results

### Step 5: Evaluate and document
- `/doc finding 2 "{topic}"` for each significant observation
- If not all green:
  - `/doc finding 2 "trial1-failures"` with specific prompt improvements needed
  - Update prompts in docs/experiments/002-doccano-build/trials/trial2/ with learnings
  - Repeat steps 1-4 for trial2 (from fresh master, new worktrees)
  - Continue through trial5 if needed
- If all green:
  - `/doc ckpt 2 "trial-complete"` — ready for promotion review

## Key rules
- Trials NEVER merge to master. Master stays pristine.
- Each trial starts from fresh master, not from the previous trial.
- Only learnings (prompt updates) carry forward between trials.
- Builder sandbox is full-auto (already set in fleet.json).
- Don't kill "stuck" workers — long silence is normal thinking time.
- Only `verdict: lgtm` counts. "Mostly good" = iterate.
- Use `/doc` for every checkpoint and finding — this is the experiment record.
