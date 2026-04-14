#!/usr/bin/env python3
"""Generate fleet dirs for trials 1-5, 9 tasks each."""

import json
import os
from pathlib import Path

DOCCANO_ROOT = Path.home() / "doccano-fork"
TRIALS_DIR = DOCCANO_ROOT / "docs" / "experiments" / "002-doccano-build" / "trials"
DOCCANO_WORKTREES = DOCCANO_ROOT / "worktrees"

TASKS = [
    {
        "name": "ml-service",
        "section": "Task 1: FastAPI ML Service",
        "description": """Build a standalone FastAPI service that accepts text and returns named entities + sentiment.

**Endpoint:** `POST /annotate`

**Request:**
```json
{"text": "Apple acquired Beats in 2014."}
```

**Response:**
```json
{
  "sentiment": {"label": "POSITIVE", "score": 0.97},
  "entities": [
    {"label": "ORG", "start_offset": 0, "end_offset": 5, "text": "Apple"},
    {"label": "ORG", "start_offset": 15, "end_offset": 20, "text": "Beats"}
  ]
}
```

**Implementation:** spaCy for NER, TextBlob or simple rule-based for sentiment. Include a `GET /health` endpoint that returns `{"status": "ok"}`.

**Files:** New `fastapi_service/` directory — `main.py`, `models.py`, `ner.py`, `sentiment.py`, `requirements.txt`, `Dockerfile`, `tests/test_annotate.py`

**Why this response shape:** Doccano's `Custom REST Request` provider sends `{"text": "{{ text }}"}` to our service. Two separate auto-labeling configs consume the same response — one extracts `sentiment` as a Category, the other extracts `entities` as Spans. This works because `AutomatedLabeling.create()` loops all configs per example (`views.py:157`).

**Verification:** `curl -X POST http://localhost:8000/annotate -d '{"text":"Apple acquired Beats"}' -H 'Content-Type: application/json'` returns valid JSON. `pytest tests/` passes.""",
    },
    {
        "name": "span-dedup",
        "section": "Task 2: Fix #2370",
        "description": """**Bug:** `LabelCollection.save()` at `backend/auto_labeling/pipeline/labels.py:32` calls `filter_annotatable_labels()` against existing DB rows, then `bulk_create()`. No dedup within a single pipeline result. Spans have no `unique_together` constraint, and `SpanManager.can_annotate()` returns `True` when `allow_overlapping=True`. Repeated auto-label runs create duplicate span annotations.

**Fix:** Add dedup logic before `bulk_create()` — deduplicate labels within the batch by `(example, label, start_offset, end_offset)` for Spans, or add a unique constraint on the Span model.

**Files:**
- `backend/auto_labeling/pipeline/labels.py` — add dedup in `save()`
- `backend/labels/models.py` — consider adding `unique_together` on Span (check if `allow_overlapping` projects need special handling)
- `backend/auto_labeling/tests/test_views.py` — add test for duplicate prevention

**Verification:** `poetry run python manage.py test auto_labeling.tests` passes. Calling auto-label twice on the same example does not create duplicate spans.""",
    },
    {
        "name": "timeout",
        "section": "Task 3: Timeout + Error Handling",
        "description": """**Problem:** `AutomatedLabeling.create()` at `views.py:154-165` calls external ML services synchronously with no timeout, no try/except, no error handling. A slow or dead service freezes the entire HTTP thread. Related GitHub issue #2345 ("server freezes").

**Fix:** Wrap each `execute_pipeline()` call in try/except with a configurable timeout (default 30s). Log failures per-config but continue to the next config. Return partial results with per-config error details in the response.

**Files:**
- `backend/auto_labeling/views.py` — wrap the config loop in `AutomatedLabeling.create()` with try/except + timeout
- `backend/auto_labeling/pipeline/execution.py` — add timeout parameter to `execute_pipeline()`
- `backend/auto_labeling/tests/test_views.py` — add tests for timeout and error scenarios

**Verification:** `poetry run python manage.py test auto_labeling.tests` passes. With ML service down, auto-labeling returns graceful error instead of hanging.""",
    },
    {
        "name": "toolbar-btn",
        "section": "Task 4: Auto-Label Button",
        "description": """**Current state:** Auto-labeling is behind a toggle switch (`ButtonAutoLabeling` → `FormAutoLabeling` dialog → `v-switch`). Users must open a dialog, flip a switch, then navigate examples. Not intuitive.

**Enhancement:** Add a prominent "Auto-Label" action button directly on `ToolbarLaptop` that triggers auto-labeling for the current example with one click. Keep the existing toggle for "auto-label on navigation" behavior.

**Files:**
- `frontend/components/tasks/toolbar/ToolbarLaptop.vue` — add new button that emits an `auto-label` event
- `frontend/components/tasks/toolbar/buttons/` — new `ButtonAutoLabelNow.vue` component (icon button with "Auto-Label This" tooltip)
- Task pages that mount the toolbar (`text-classification/index.vue`, `sequence-labeling/index.vue`, etc.) — handle the new event by calling `autoLabel(projectId, exampleId)`

**Key context:** Auto-label API is `POST /projects/${projectId}/auto-labeling?example=${exampleId}`. All annotation repositories already inherit `AnnotationRepository.autoLabel()` (`frontend/domain/models/tasks/annotationRepository.ts:48-55`). The composables `useTeacherList` and `useTextLabel` already have `autoLabel()` methods.

**Verification:** Button visible on toolbar. Clicking it triggers auto-labeling and annotations appear on current example.""",
    },
    {
        "name": "health-indicator",
        "section": "Task 5: ML Service Health Indicator",
        "description": """**Current state:** `ConfigList.vue` shows a table of auto-labeling configs with name and actions. No indication whether the configured ML service is actually reachable.

**Enhancement:** Add a green/red status dot next to each config in the list. On component mount, ping each config's service URL (via a new lightweight backend endpoint or the existing `testParameters` endpoint with a minimal payload) and show the result.

**Files:**
- `frontend/components/configAutoLabeling/ConfigList.vue` — add status column to `v-data-table`, call health check on mount
- `backend/auto_labeling/views.py` — add a lightweight `GET /projects/${projectId}/auto-labeling/configs/${configId}/health` endpoint that pings the configured URL and returns status (or reuse the existing `request-testing` endpoint)
- `backend/auto_labeling/urls.py` — register new endpoint

**Key context:** Each config stores `model_attrs` with a `url` field. The health check should hit the ML service's `/health` endpoint (Task 1 provides this). Timeout should be short (2-3s) to avoid blocking the UI.

**Verification:** Config list shows green dot when ML service is running, red dot when it's down.""",
    },
    {
        "name": "bulk-autolabel",
        "section": "Task 6: Bulk Auto-Label Button",
        "description": """**Current state:** Auto-labeling works one example at a time. No way to auto-label all unlabeled examples in batch.

**Enhancement:** Add a "Bulk Auto-Label" button on the dataset/examples list page. When clicked, it sends auto-label requests for all selected (or all unlabeled) examples. Show a progress indicator.

**Files:**
- `frontend/pages/projects/_id/dataset/index.vue` — add "Bulk Auto-Label" button to the toolbar, wire up to new API endpoint
- `backend/auto_labeling/views.py` — add `BulkAutoLabeling` endpoint that accepts a list of example IDs and runs the pipeline for each
- `backend/auto_labeling/urls.py` — register bulk endpoint
- `backend/auto_labeling/tests/test_views.py` — add test for bulk endpoint

**Key context:** The existing `AutomatedLabeling.create()` at `views.py:154` handles one example. The bulk endpoint should loop over example IDs and call the same pipeline logic. Consider using Celery for large batches (Celery is already set up for import/export), or keep it synchronous with a progress response for small batches.

**Verification:** Select multiple examples on dataset page → click Bulk Auto-Label → all selected examples get annotations.""",
    },
    {
        "name": "result-toast",
        "section": "Task 7: Auto-Label Result Toast",
        "description": """**Current state:** After auto-labeling completes, the page silently reloads annotations. No feedback on what happened — how many labels were added, whether any configs failed, or if the service was unreachable.

**Enhancement:** After auto-labeling, show a Vuetify snackbar/toast with a summary: "Added 3 entities + 1 sentiment label" or "Auto-labeling failed: service unreachable". This requires the backend to return label counts in the auto-labeling response.

**Files:**
- `backend/auto_labeling/views.py` — modify `AutomatedLabeling.create()` response to include counts of labels created per task type and any errors
- `frontend/components/tasks/toolbar/ToolbarLaptop.vue` or the task pages — add snackbar component, display result summary after auto-label call returns
- Task pages (`text-classification/index.vue`, `sequence-labeling/index.vue`, etc.) — capture the auto-label response and show toast

**Key context:** Currently `AutomatedLabeling.create()` returns a generic 201 response. The response should be enriched with `{"created": {"categories": 1, "spans": 3}, "errors": []}`. The frontend `autoLabel()` in `annotationRepository.ts:48-55` posts to the endpoint — its response can be captured and displayed.

**Verification:** Auto-label an example → toast appears showing "Added 1 category, 3 spans" or error message.""",
    },
    {
        "name": "setup-script",
        "section": "Task 8: Demo Setup Script",
        "description": """**Purpose:** One command to set up a complete demo environment — create project, add label types, import sample data, configure auto-labeling to point at the FastAPI ML service.

**Implementation:** Python script using Django management commands or REST API calls:
1. Create an `IntentDetectionAndSlotFilling` project (supports both Category + Span)
2. Create CategoryTypes: POSITIVE, NEGATIVE, NEUTRAL
3. Create SpanTypes: PER, ORG, LOC, DATE, MISC
4. Import 10-20 sample sentences via the data import API
5. Create two AutoLabelingConfig entries pointing at the FastAPI service:
   - Category config: `model_attrs={"url": "http://localhost:8000/annotate", "method": "POST", "body": {"text": "{{ text }}"}}`, template extracts `sentiment.label`, label_mapping maps to CategoryTypes
   - Span config: same URL, template extracts `entities[]` with `label/start_offset/end_offset`, label_mapping maps to SpanTypes

**Files:** New `scripts/setup-demo.py` (or `.sh`)

**Verification:** Run script → open doccano → project exists with sample data → click auto-label → annotations appear.""",
    },
    {
        "name": "dev-compose",
        "section": "Task 9: docker-compose.dev.yml",
        "description": """**Purpose:** One-command full-stack dev environment with the ML service included.

**Implementation:** Extend the existing `docker/docker-compose.prod.yml` with:
- Volume mounts for backend and frontend source (hot reload)
- ML service container built from `fastapi_service/Dockerfile`
- Django `runserver` instead of gunicorn
- Nuxt `yarn dev` instead of built assets
- Postgres + RabbitMQ from existing compose

**Files:** New `docker/docker-compose.dev.yml`

**Verification:** `docker-compose -f docker-compose.dev.yml up` → all services start → frontend at `localhost:3000`, backend at `localhost:8000`, ML service at `localhost:8001`.""",
    },
]


def fleet_json(trial_num: int, task: dict) -> dict:
    return {
        "fleet_name": f"trial{trial_num}-{task['name']}",
        "type": "iterative",
        "config": {
            "max_concurrent": 2,
            "model": "gpt-5.4",
            "fallback_model": "gpt-5.4",
            "provider": "codex",
            "reasoning_effort": "medium",
            "record": False,
            "max_iterations": 10,
            "cost_cap_usd": 40.0,
        },
        "workers": [
            {
                "id": "builder",
                "type": "code-run",
                "description": "Cold-start TDD agent: discover, plan, test, implement, commit, document",
                "task": task["section"],
                "model": "gpt-5.4",
                "provider": "codex",
                "reasoning_effort": "medium",
                "sandbox": "full-auto",
                "max_budget_per_iter": 20.0,
            },
            {
                "id": "reviewer",
                "type": "reviewer",
                "description": "Critical code reviewer: verify tests are real, code correct, scope respected",
                "task": f"Review {task['section']}",
                "model": "claude-opus-4-6",
                "provider": "claude",
                "reasoning_effort": "medium",
                "depends_on": ["builder"],
                "max_budget_per_iter": 20.0,
            },
        ],
        "stop_when": {
            "reviewer_lgtm_count": 1,
            "max_iterations": 10,
            "cost_cap_usd": 40.0,
        },
    }


def prior_trial_learnings_builder(trial_num: int, task: dict) -> str:
    """Generate the prior-trial learnings section for trials 2-5."""
    if trial_num <= 1:
        return ""

    tn = task["name"]
    lines = [
        "",
        "## Prior Trial Learnings",
        "",
        "Previous trials attempted this EXACT same task. Their agents documented what",
        "worked, what failed, and what the reviewer caught. You MUST read these before",
        "starting — they are the single biggest advantage you have over a cold start.",
        "",
        "Read these files IN ORDER (oldest trial first). Focus on:",
        "- What approaches were tried and whether the reviewer approved them",
        "- What specific mistakes the reviewer flagged — do NOT repeat them",
        "- What the completion report says about remaining issues",
        "- What the trial summary says about this task's merge status",
        "",
    ]

    for prev in range(1, trial_num):
        prev_iterations = TRIALS_DIR / f"trial{prev}" / f"fleet-{tn}" / "iterations"
        prev_summary = TRIALS_DIR / f"trial{prev}" / "summary.md"
        lines.append(f"### Trial {prev}")
        lines.append(f"- Iterations dir: `{prev_iterations}/`")
        lines.append(f"  Read ALL `attempt-*.md` and `review-*.md` files in this directory.")
        lines.append(f"  If `completion-report.md` exists, read it — it's the most important file.")
        lines.append(f"- Trial summary: `{prev_summary}`")
        lines.append(f"  Read the section about `fleet-{tn}` for the merger's assessment.")
        lines.append("")

    lines.extend([
        "### How to use prior learnings",
        "1. If a prior trial got LGTM: study what worked and replicate the approach",
        "2. If a prior trial was rejected: read every review-N.md to understand why",
        "3. If the reviewer flagged fake tests: yours must be meaningfully different",
        "4. If the merger flagged conflicts: be aware of which files other tasks touch",
        "5. DO NOT blindly copy prior code — you're on a fresh branch from master",
        "   Prior trial code is NOT in your worktree. Learn from it, then implement fresh.",
        "",
    ])

    return "\n".join(lines)


def prior_trial_learnings_reviewer(trial_num: int, task: dict) -> str:
    """Generate the prior-trial context section for reviewer in trials 2-5."""
    if trial_num <= 1:
        return ""

    tn = task["name"]
    lines = [
        "",
        "## Prior Trial Context",
        "",
        "This is trial {0}. Previous trials attempted this same task. Use their history".format(trial_num),
        "to calibrate your review — if prior builders kept making the same mistake,",
        "check whether this builder actually fixed it or just moved the problem.",
        "",
    ]

    for prev in range(1, trial_num):
        prev_iterations = TRIALS_DIR / f"trial{prev}" / f"fleet-{tn}" / "iterations"
        prev_summary = TRIALS_DIR / f"trial{prev}" / "summary.md"
        lines.append(f"### Trial {prev}")
        lines.append(f"- Iterations dir: `{prev_iterations}/`")
        lines.append(f"  Read prior `review-*.md` files to see what previous reviewers flagged.")
        lines.append(f"  Read `completion-report.md` if it exists for the final state.")
        lines.append(f"- Trial summary: `{prev_summary}`")
        lines.append("")

    lines.extend([
        "### How to use prior context",
        "- If prior reviewers flagged fake tests: be EXTRA vigilant about test quality",
        "- If prior trials hit the same bug repeatedly: check if the root cause is addressed",
        "- If the task was escalated before: consider whether this attempt overcomes the fundamental blocker",
        "- Hold this builder to a HIGHER standard than trial 1 — they had learnings to work from",
        "",
    ])

    return "\n".join(lines)


def builder_prompt(trial_num: int, task: dict) -> str:
    tn = task["name"]
    worktree = DOCCANO_WORKTREES / f"trial{trial_num}-{tn}"
    output_dir = TRIALS_DIR / f"trial{trial_num}" / f"fleet-{tn}" / "iterations"

    prior_learnings = prior_trial_learnings_builder(trial_num, task)

    return f"""You are a cold-start development agent. You have never seen this codebase before.

## Your Code Repository
{worktree}

IMPORTANT: `cd` to this directory FIRST before doing anything.

## Your Task
{task['description']}
{prior_learnings}
## Protocol — follow this order strictly

### 0. READ PRIOR LEARNINGS (if any exist above)
If a "Prior Trial Learnings" section exists above, read EVERY file listed there
BEFORE you touch the codebase. Take notes on what worked, what failed, and what
the reviewer rejected. This is not optional — skipping this step means you will
repeat mistakes that prior agents already documented.

### 1. DISCOVER
Read the repo structure. Find relevant files. Understand architecture, patterns, existing tests.
Do NOT start coding until you understand the codebase.

### 2. PLAN (TDD)
Design your tests FIRST. Write a concrete test plan:
- What test files you'll create
- What each test validates
- What assertions prove the feature works
- Tests must be REAL:
  - Backend: pytest hitting real endpoints/DB. No mocks that fake the behavior under test.
  - Frontend: tests that validate actual user workflows. No shallow snapshots, no always-pass stubs.
  - If a reviewer catches fake tests, your attempt is rejected.

### 3. WRITE TESTS
Implement the tests. Run them. They MUST FAIL (red phase).
If tests pass before you've implemented anything, your tests are fake. Rewrite them.

### 4. IMPLEMENT
Write the minimum code to make tests pass (green phase). No over-engineering.

### 5. VERIFY
Run ALL tests — yours AND existing test suite. Everything must pass.
If existing tests break, you introduced a regression. Fix it.

### 6. COMMIT
`git add` your changes and `git commit` with a descriptive message.
EVERY attempt commits, not just the final one. If this is attempt 3, your commit
sits on top of attempts 1 and 2 in git history.

### 7. DOCUMENT
Write `{{output dir}}/attempt-{{N}}.md` with this structure:

#### Exploration
- What I found in the codebase (key files, architecture, patterns I discovered)
- What I had to understand before I could start

#### Approach
- What approach I took and why
- What tests I wrote and what they validate

#### Results
- Test output (pass/fail counts, error messages if any)
- What worked

#### Problems
- What didn't work and why (errors, test failures, dead ends)
- Specific error messages and stack traces

#### Advice for Next Attempt
- What I'd do differently
- What the next agent should know to avoid my mistakes

This documentation is NOT optional. The next agent's success depends on your notes.

On your FINAL attempt (LGTM from reviewer, or attempt 10), also write
`{{output dir}}/completion-report.md` — see the completion report spec below.

## Output Directory
{output_dir}

Write attempt-{{N}}.md into this directory.

## Completion Report (write on FINAL attempt only)

```markdown
## Exploration
- What I found in the codebase (key files, architecture, patterns)
- What I had to understand before I could start

## What I Built
- Per-task: what was implemented, where, why this approach
- Files created/modified (with brief description of each change)

## Tests
- What tests I wrote and what they validate
- Full test output (pass/fail)

## Journey
- Attempt-by-attempt summary: what each attempt tried, what the reviewer caught
- Key decisions I made and alternatives I considered

## Remaining Issues
- What's not done or not perfect
- Known limitations
- What a merge agent should watch out for
```
"""


def reviewer_prompt(trial_num: int, task: dict) -> str:
    tn = task["name"]
    worktree = DOCCANO_WORKTREES / f"trial{trial_num}-{tn}"
    output_dir = TRIALS_DIR / f"trial{trial_num}" / f"fleet-{tn}" / "iterations"

    prior_context = prior_trial_learnings_reviewer(trial_num, task)

    return f"""You are a senior code reviewer. Your job is to be CRITICAL and find real problems.
You are NOT here to rubber-stamp. If the work is not right, reject it clearly.

## Code Repository
{worktree}

IMPORTANT: `cd` to this directory FIRST. Read the code. Run the tests yourself.

## Task the Builder Was Assigned
{task['description']}
{prior_context}
## Review Protocol

### 1. READ THE CODE
Examine every file the builder changed. Understand what was done.

### 2. CHECK TESTS EXIST
- Are there new test files for the task?
- If no tests: REJECT. "No tests written" is an automatic rejection.

### 3. CHECK TESTS ARE REAL
This is the most important check. Look for:
- Tests that mock the thing they're supposed to test (REJECT)
- Assertions that always pass regardless of implementation (REJECT)
- Tests that only check types/existence, not behavior (REJECT)
- Tests that duplicate what the framework already guarantees (REJECT)
- Tests should exercise the actual feature path end-to-end

### 4. RUN TESTS
Actually run the test suite. Commands:
- Backend: `cd backend && poetry run python manage.py test` or `poetry run pytest`
- Frontend: `cd frontend && yarn test` (if configured)
Report exact output — pass count, fail count, error messages.

### 5. CHECK CODE CORRECTNESS
- Does the implementation match the task requirements?
- Are there obvious bugs, missing error handling, security issues?
- Is the code minimal and focused (not over-engineered)?

### 6. CHECK FOR REGRESSIONS
Run the FULL existing test suite (not just the new tests).
If existing tests break, the builder introduced a regression.

### 7. CHECK SCOPE
Did the builder stay within reasonable scope for the task?
Touching unrelated files is a yellow flag. Refactoring unrelated code is a red flag.

## Write Your Verdict

Write to `{{output dir}}/review-{{N}}.md` with this EXACT structure:

### Verdict: [LGTM | REJECTED]

### Per-Task Status
| Task | Status | Notes |
|------|--------|-------|
| {task['section']} | PASS/FAIL | {{one line}} |

### Test Results
```
{{paste actual test output here}}
```

### Issues Found
{{numbered list of every problem, with file paths and line numbers}}

1. [CRITICAL/MAJOR/MINOR] {{description}}
   - File: {{path}}
   - Line: {{number}}
   - Why it's wrong: {{explanation}}
   - How to fix: {{specific guidance}}

### What the Next Builder Must Do (if REJECTED)
{{ordered list of exactly what needs to happen for the next attempt to pass}}
1. {{specific action}}
2. {{specific action}}
...

Be SPECIFIC. The next builder agent starts COLD. It has never seen this codebase.
Vague feedback like "improve tests" is useless. Say exactly which test, what's wrong
with it, and what a correct test would check.

### What Was Done Well
{{acknowledge good work — helps the next builder know what to keep}}

## Verdict Rules
- `verdict: lgtm` — ALL checks pass. Tests are real, they pass, code is correct, no regressions.
- `verdict: iterate` — ANY check fails. Be specific about what to fix.
- `verdict: escalate` — fundamental approach is wrong, task may be impossible as described.
  Only use this if you believe 10 more attempts won't fix it.

If in doubt, the verdict is `iterate`. NEVER give LGTM if tests don't pass.

## Output Directory
{output_dir}

Write review-{{N}}.md into this directory.
"""


def main():
    count = 0
    for trial_num in range(1, 6):
        for task in TASKS:
            tn = task["name"]
            fleet_dir = TRIALS_DIR / f"trial{trial_num}" / f"fleet-{tn}"
            workers_dir = fleet_dir / "workers"
            iterations_dir = fleet_dir / "iterations"

            # Create dirs
            (workers_dir / "builder").mkdir(parents=True, exist_ok=True)
            (workers_dir / "reviewer").mkdir(parents=True, exist_ok=True)
            iterations_dir.mkdir(parents=True, exist_ok=True)

            # fleet.json
            with open(fleet_dir / "fleet.json", "w") as f:
                json.dump(fleet_json(trial_num, task), f, indent=2)
                f.write("\n")

            # builder prompt
            with open(workers_dir / "builder" / "prompt.md", "w") as f:
                f.write(builder_prompt(trial_num, task))

            # reviewer prompt
            with open(workers_dir / "reviewer" / "prompt.md", "w") as f:
                f.write(reviewer_prompt(trial_num, task))

            count += 3

    print(f"Generated {count} files across 5 trials x 9 tasks")


if __name__ == "__main__":
    main()
