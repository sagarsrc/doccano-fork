## Exploration
- The relevant request path is `backend/auto_labeling/views.py`, where `AutomatedLabeling.create()` loops over `AutoLabelingConfig` rows for a project and calls `execute_pipeline()` synchronously before saving labels.
- The outbound ML call path is `backend/auto_labeling/pipeline/execution.py`. It builds a request model, mapping template, and post-processor, then calls `auto_labeling_pipeline.pipeline.pipeline(...)`.
- Existing auto-labeling tests live in `backend/auto_labeling/tests/test_views.py`. Most endpoint tests already use real API requests and DB assertions, but existing automated-labeling tests patch `auto_labeling.views.execute_pipeline`, so I needed a lower seam for the new timeout/failure coverage.
- I also checked `backend/auto_labeling/pipeline/labels.py` to confirm label persistence behavior and avoid changing save semantics unnecessarily.

## Approach
- I added two real endpoint tests in `backend/auto_labeling/tests/test_views.py` and patched only `auto_labeling.pipeline.execution.pipeline`, which is the external-call seam beneath the Django view.
- `test_returns_partial_results_when_config_times_out` creates two real configs, overrides `AUTO_LABELING_TIMEOUT` to `0.01`, makes the second pipeline call sleep, and asserts:
  - the request returns quickly instead of hanging
  - the first config still saves its label
  - the response contains per-config success/error entries
- `test_returns_partial_results_when_config_fails` creates three real configs, forces the middle pipeline call to raise, and asserts:
  - the request continues to the third config
  - successful configs still save labels
  - the response includes the failed config's error details
  - an error log entry is emitted for the failed config
- Implementation:
  - `backend/auto_labeling/pipeline/execution.py`: added a `timeout` parameter to `execute_pipeline()` with default `30`, and enforced it around the pipeline call.
  - `backend/auto_labeling/views.py`: read timeout from `settings.AUTO_LABELING_TIMEOUT`, wrapped each config execution/save in `try/except`, logged failures, and returned partial per-config results.

## Results
- Red phase:
  - `test_returns_partial_results_when_config_fails` originally errored with `RuntimeError: ML service unavailable` because the view aborted the whole request.
  - `test_returns_partial_results_when_config_times_out` originally failed because both labels were saved and no timeout handling existed.
- Final verification command run:
  - `/home/sagar/doccano-fork/backend/.venv/bin/python manage.py test auto_labeling.tests`
- Final test result:
  - `Ran 22 tests in 2.339s`
  - `OK`
- What worked:
  - The endpoint now returns `201` with `{"ok": false, "results": [...]}` when one or more configs fail.
  - Successful configs still persist labels even when later configs time out or raise exceptions.
  - Per-config failures are logged with the config/project/example identifiers.

## Problems
- The exact requested verification command `poetry run python manage.py test auto_labeling.tests` could not be used because `poetry` was not available in PATH in this environment. I used the repo's existing virtualenv interpreter instead.
- The timeout implementation stops the HTTP request from waiting indefinitely, but it uses a worker thread around the pipeline call. That means the timed-out worker may still continue running in the background until the underlying library call exits. This fixes the server-freeze symptom for the request thread, but it is not a hard cancellation of the remote call.
- Test output still includes an expected logged traceback for the timeout case because the view logs per-config failures with `logger.exception(...)`.

## Advice for Next Attempt
- If a reviewer requires hard cancellation of the outbound network call rather than request-thread protection, the next step is to push timeout values down into the actual request implementations in the `auto-labeling-pipeline` package (for `requests` and `boto3` clients) instead of only wrapping the top-level pipeline call.
- If the API contract needs a different response shape, adjust the `results` payload in `AutomatedLabeling.create()` and update the two new endpoint tests together.
- Use the lower patch seam `auto_labeling.pipeline.execution.pipeline` for these tests. Patching `auto_labeling.views.execute_pipeline` would skip the timeout implementation and make the tests less trustworthy.
