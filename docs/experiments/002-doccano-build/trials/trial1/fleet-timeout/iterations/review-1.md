### Verdict: REJECTED

### Per-Task Status
| Task | Status | Notes |
|------|--------|-------|
| Task 3: Timeout + Error Handling | FAIL | The endpoint now returns partial results, but the timeout does not stop the underlying ML call and can leak stuck worker threads indefinitely. |

### Test Results
```text
$ /home/sagar/doccano-fork/backend/.venv/bin/python manage.py test auto_labeling.tests
Creating test database for alias 'default'...
Found 22 test(s).
System check identified some issues:

WARNINGS:
?: (staticfiles.W004) The directory '/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/client/dist/static' in the STATICFILES_DIRS setting does not exist.

System check identified 1 issue (0 silenced).

Running tests...
----------------------------------------------------------------------
/home/sagar/doccano-fork/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-timeout/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
.......Auto-labeling failed for config_id=2 project_id=1 example_id=1
Traceback (most recent call last):
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/pipeline/execution.py", line 36, in execute_pipeline
    labels = future.result(timeout=timeout)
  File "/usr/lib/python3.10/concurrent/futures/_base.py", line 460, in result
    raise TimeoutError()
concurrent.futures._base.TimeoutError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/views.py", line 167, in create
    labels = execute_pipeline(example.data, config=config, timeout=timeout)
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/pipeline/execution.py", line 39, in execute_pipeline
    raise TimeoutError(f"Auto-labeling request timed out after {timeout} seconds.") from exc
TimeoutError: Auto-labeling request timed out after 0.01 seconds.
...............
.
----------------------------------------------------------------------
Ran 22 tests in 4.428s

OK

Generating XML reports...
Destroying test database for alias 'default'...

$ /home/sagar/doccano-fork/backend/.venv/bin/python manage.py test
Found 543 test(s).
Creating test database for alias 'default'...
System check identified some issues:

WARNINGS:
?: (staticfiles.W004) The directory '/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/client/dist/static' in the STATICFILES_DIRS setting does not exist.

System check identified 1 issue (0 silenced).

Running tests...
----------------------------------------------------------------------
....Setting password for User admin.
......../home/sagar/doccano-fork/backend/.venv/lib/python3.10/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /home/sagar/doccano-fork/worktrees/trial1-timeout/backend/staticfiles/
  mw_instance = middleware(adapted_handler)
.......Auto-labeling failed for config_id=2 project_id=1 example_id=1
Traceback (most recent call last):
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/pipeline/execution.py", line 36, in execute_pipeline
    labels = future.result(timeout=timeout)
  File "/usr/lib/python3.10/concurrent/futures/_base.py", line 460, in result
    raise TimeoutError()
concurrent.futures._base.TimeoutError

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/views.py", line 167, in create
    labels = execute_pipeline(example.data, config=config, timeout=timeout)
  File "/home/sagar/doccano-fork/worktrees/trial1-timeout/backend/auto_labeling/pipeline/execution.py", line 39, in execute_pipeline
    raise TimeoutError(f"Auto-labeling request timed out after {timeout} seconds.") from exc
TimeoutError: Auto-labeling request timed out after 0.01 seconds.
................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 543 tests in 49.736s

OK

Generating XML reports...
Destroying test database for alias 'default'...
```

### Issues Found
1. [CRITICAL] The new timeout does not actually stop the external ML request; it only stops waiting on it.
   - File: `backend/auto_labeling/pipeline/execution.py`
   - Line: `33`
   - Why it's wrong: `future.cancel()` has no effect once `_run_pipeline()` has started, and `executor.shutdown(wait=False, cancel_futures=True)` does not kill a running worker thread. A hung `requests` or boto3 call will keep running indefinitely in the background. That means each timeout can leak a stuck thread, so repeated auto-labeling requests can still exhaust server resources even though the HTTP response returns. This does not fully solve the "dead service freezes" problem at the ML-call boundary.
   - How to fix: Pass the timeout into the actual network clients used by the pipeline. For REST models, use `requests.request(..., timeout=timeout)` / `requests.post(..., timeout=timeout)`. For AWS clients, configure botocore timeouts via `Config(connect_timeout=..., read_timeout=...)` or equivalent. Then thread-level waiting can be secondary protection, not the only enforcement.

2. [MAJOR] The view now swallows every exception in the loop, including persistence and programming errors, and converts them into a 201 response.
   - File: `backend/auto_labeling/views.py`
   - Line: `170`
   - Why it's wrong: The task was to harden external ML execution, not to hide arbitrary server-side failures. If `labels.save(...)` breaks because of a DB problem, invalid label state, or a regression, the API will now quietly return `"status": "error"` for that config instead of surfacing a real server bug. That makes genuine defects harder to detect and debug.
   - How to fix: Narrow the `try/except` to the external execution path and expected recoverable mapping/service failures. Let unexpected save/database errors propagate, or catch them separately and re-raise after logging.

3. [MAJOR] The new tests do not verify that a real request timeout is configured on the ML clients, so they miss the main correctness gap above.
   - File: `backend/auto_labeling/tests/test_views.py`
   - Line: `249`
   - Why it's wrong: Both new tests patch `auto_labeling.pipeline.execution.pipeline`, so they only prove that the wrapper thread returns partial results when the mocked function sleeps or raises. They never exercise the actual request layer in `auto_labeling_pipeline.models`, where the real network calls still have no timeout configured. These tests pass even with the current thread-leak implementation.
   - How to fix: Add execution-layer tests that assert the timeout is propagated into the concrete request clients. For example, patch `requests.request` / `requests.post` and verify they receive `timeout=...`, and patch AWS client construction to verify botocore timeout config is applied.

### What the Next Builder Must Do (if REJECTED)
1. Rework `execute_pipeline()` so the timeout reaches the real outbound ML calls instead of only wrapping them in a worker thread.
2. Update the relevant request model implementations used by auto-labeling to accept and apply timeouts to `requests` and AWS/botocore clients.
3. Narrow the `AutomatedLabeling.create()` exception handling so recoverable ML-call failures are reported per-config, but unexpected `labels.save()` or other server-side errors are not silently converted into success-path API responses.
4. Replace or extend the new tests so they verify timeout propagation at the network-client layer, not just a sleeping mock of `pipeline()`.
5. Re-run `/home/sagar/doccano-fork/backend/.venv/bin/python manage.py test auto_labeling.tests` and `/home/sagar/doccano-fork/backend/.venv/bin/python manage.py test` and include the new passing output.

### What Was Done Well
The builder kept the code changes tightly scoped to the intended files, added response details per config, and covered the partial-success behavior in tests. The endpoint now logs config-specific failures and continues processing later configs, which is the right high-level API behavior to preserve in the next attempt.
