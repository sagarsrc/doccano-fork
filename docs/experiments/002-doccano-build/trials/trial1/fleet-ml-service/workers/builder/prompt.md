You are a cold-start development agent. You have never seen this codebase before.

## Your Code Repository
/home/sagar/doccano-fork/worktrees/trial1-ml-service

IMPORTANT: `cd` to this directory FIRST before doing anything.

## Your Task
Build a standalone FastAPI service that accepts text and returns named entities + sentiment.

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

**Verification:** `curl -X POST http://localhost:8000/annotate -d '{"text":"Apple acquired Beats"}' -H 'Content-Type: application/json'` returns valid JSON. `pytest tests/` passes.

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
Write `{output dir}/attempt-{N}.md` with this structure:

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
`{output dir}/completion-report.md` — see the completion report spec below.

## Output Directory
/home/sagar/doccano-fork/docs/experiments/002-doccano-build/trials/trial1/fleet-ml-service/iterations

Write attempt-{N}.md into this directory.

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
