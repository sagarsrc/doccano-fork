#### Exploration
- Found an existing REST-based bootstrap script in `tools/setup-demo.py` that already handled login, project creation, label creation, and dataset upload through doccano’s API.
- Traced the backend endpoints used by that flow: `projects`, `category-types`, `span-types`, `upload`, `examples`, and `auto-labeling/configs`.
- Verified the auto-labeling config schema from the installed `auto-labeling-pipeline` package. `Custom REST Request` requires `url`, `method`, `params`, `headers`, and `body`.
- Confirmed the relevant project type is `IntentDetectionAndSlotFillingProject`, and that importing JSONL with `cats: []` and `entities: []` creates examples without pre-existing annotations.
- Checked the repo’s test conventions. The backend suite runs with `manage.py test`, so I used a real Django live-server integration test instead of introducing a separate pytest setup that does not exist here.

#### Approach
- Added `backend/auto_labeling/tests/test_setup_demo_script.py` as an end-to-end integration test.
- The test starts a live Django server, creates a real staff `admin/password` user, runs the new script against real HTTP endpoints, and asserts:
- A project named `Intent Detection and Slot Filling Demo` is created with project type `IntentDetectionAndSlotFilling`.
- Category types are exactly `POSITIVE`, `NEGATIVE`, `NEUTRAL`.
- Span types are exactly `PER`, `ORG`, `LOC`, `DATE`, `MISC`.
- Twelve sample examples are imported.
- Two auto-labeling configs are created with `Custom REST Request`, the expected `model_attrs`, the sentiment template, the span template, and the expected label mappings.
- Implemented `scripts/setup-demo.py` by adapting the existing `tools/setup-demo.py` flow and extending it to:
- Generate a temporary JSONL file with 12 unlabeled demo sentences.
- Upload/import that dataset via the existing filepond + import API.
- Create both required auto-labeling configs that point at `http://localhost:8000/annotate`.

#### Results
- Red phase:
- `manage.py test auto_labeling.tests.test_setup_demo_script --pattern='test*.py'`
- Failed as expected with `FileNotFoundError` because `scripts/setup-demo.py` did not exist yet.
- First implementation issue:
- The script initially waited on Celery task readiness and timed out under eager-task test execution because eager results were not stored.
- Adjusted the import wait logic to poll the examples count instead, which reflects actual completion for this workflow.
- Green phase:
- `manage.py test auto_labeling.tests.test_setup_demo_script --pattern='test*.py'`
- Passed.
- Regression suite:
- `manage.py test --pattern='test*.py'`
- Passed: `Ran 542 tests in 45.251s`, `OK`.

#### Problems
- `scripts/` is ignored by this repo’s `.gitignore`, so `scripts/setup-demo.py` must be force-added when committing.
- The backend test run emits existing staticfiles warnings because `backend/client/dist/static` and `backend/staticfiles/` do not exist in this worktree. These warnings predated the change and did not affect test outcomes.
- The first version of the script used `/v1/tasks/status/<task_id>` as the import completion signal. In tests with `CELERY_TASK_ALWAYS_EAGER=True`, Celery warns that results are not stored unless eager result storage is enabled, so that readiness check was unreliable.

#### Advice for Next Attempt
- Keep the import-completion check based on `/projects/<id>/examples` count unless the environment is changed to store eager Celery results.
- If the script path must remain `scripts/setup-demo.py`, remember to `git add -f scripts/setup-demo.py` because of the ignore rule.
- If manual verification is needed, start doccano, start the FastAPI ML service on `http://localhost:8000/annotate`, run `scripts/setup-demo.py`, then open the created project and use auto-labeling on an example to confirm both category and span annotations appear.
