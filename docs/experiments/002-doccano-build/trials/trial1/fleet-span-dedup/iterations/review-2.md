### Verdict: LGTM

### Per-Task Status
| Task | Status | Notes |
|------|--------|-------|
| Task 2: Fix #2370 | PASS | Span auto-label batches are deduplicated before `bulk_create()`, with end-to-end tests covering single-run and repeated-run duplicate prevention. |

### Test Results
```text
$ .venv/bin/python manage.py test auto_labeling.tests
Found 22 test(s).
System check identified some issues:

WARNINGS:
?: (staticfiles.W004) The directory '/home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/client/dist/static' in the STATICFILES_DIRS setting does not exist.

System check identified 1 issue (0 silenced).

Running tests...
----------------------------------------------------------------------
/home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
......................
----------------------------------------------------------------------
Ran 22 tests in 2.172s

OK

Generating XML reports...
Destroying test database for alias 'default'...

$ .venv/bin/python manage.py test
Found 543 test(s).
System check identified some issues:

WARNINGS:
?: (staticfiles.W004) The directory '/home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/client/dist/static' in the STATICFILES_DIRS setting does not exist.

System check identified 1 issue (0 silenced).

Running tests...
----------------------------------------------------------------------
....Setting password for User admin.
......../home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
.................................................................../home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
................................................................................/home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-span-dedup/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
.............................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 543 tests in 43.853s

OK

Generating XML reports...
Destroying test database for alias 'default'...
```

### Issues Found
None.

### What the Next Builder Must Do (if REJECTED)
Not applicable.

### What Was Done Well
The fix stays tightly scoped to `backend/auto_labeling/pipeline/labels.py` and addresses the actual failure mode before `bulk_create()`, which is the right place to prevent duplicate unsaved spans.

The new tests in `backend/auto_labeling/tests/test_views.py` exercise the real auto-labeling view path and verify both duplicate spans returned in a single pipeline result and duplicate spans created by repeated auto-label runs when `allow_overlapping=True`.
