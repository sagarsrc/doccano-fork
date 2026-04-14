You are a cold-start development agent. You have never seen this codebase before.

## Your Code Repository
/home/sagar/doccano-fork/worktrees/trial1-bulk-autolabel

IMPORTANT: `cd` to this directory FIRST before doing anything.

## Your Task
**Current state:** Auto-labeling works one example at a time. No way to auto-label all unlabeled examples in batch.

**Enhancement:** Add a "Bulk Auto-Label" button on the dataset/examples list page. When clicked, it sends auto-label requests for all selected (or all unlabeled) examples. Show a progress indicator.

**Files:**
- `frontend/pages/projects/_id/dataset/index.vue` — add "Bulk Auto-Label" button to the toolbar, wire up to new API endpoint
- `backend/auto_labeling/views.py` — add `BulkAutoLabeling` endpoint that accepts a list of example IDs and runs the pipeline for each
- `backend/auto_labeling/urls.py` — register bulk endpoint
- `backend/auto_labeling/tests/test_views.py` — add test for bulk endpoint

**Key context:** The existing `AutomatedLabeling.create()` at `views.py:154` handles one example. The bulk endpoint should loop over example IDs and call the same pipeline logic. Consider using Celery for large batches (Celery is already set up for import/export), or keep it synchronous with a progress response for small batches.

**Verification:** Select multiple examples on dataset page → click Bulk Auto-Label → all selected examples get annotations.

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
/home/sagar/doccano-fork/docs/experiments/002-doccano-build/trials/trial1/fleet-bulk-autolabel/iterations

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
