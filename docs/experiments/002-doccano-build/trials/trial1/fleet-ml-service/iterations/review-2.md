### Verdict: REJECTED

### Per-Task Status
| Task | Status | Notes |
|------|--------|-------|
| Task 1: FastAPI ML Service | FAIL | Endpoints exist and the isolated test passes, but the shipped setup falls back to incorrect NER behavior and the new test does not actually verify sentiment behavior. |

### Test Results
```text
$ /tmp/trial1-ml-review-venv/bin/python -m pytest tests/test_annotate.py -q
..                                                                       [100%]
2 passed in 5.24s

$ /tmp/trial1-ml-review-venv/bin/python backend/manage.py test --pattern='test*.py'
Traceback (most recent call last):
  File "/home/sagar/doccano-fork/worktrees/trial1-ml-service/backend/manage.py", line 15, in <module>
    execute_from_command_line(sys.argv)
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
    utility.execute()
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/__init__.py", line 436, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/commands/test.py", line 24, in run_from_argv
    super().run_from_argv(argv)
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/base.py", line 404, in run_from_argv
    parser = self.create_parser(argv[0], argv[1])
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/base.py", line 367, in create_parser
    self.add_arguments(parser)
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/core/management/commands/test.py", line 54, in add_arguments
    test_runner_class = get_runner(settings, self.test_runner)
  File "/tmp/trial1-ml-review-venv/lib/python3.10/site-packages/django/test/utils.py", line 395, in get_runner
    test_module = __import__(test_module_name, {}, {}, test_path[-1])
ModuleNotFoundError: No module named 'xmlrunner'

$ /tmp/trial1-ml-review-venv/bin/python -m pytest -q

==================================== ERRORS ====================================
_____________ ERROR collecting backend/api/tests/test_commands.py ______________
ImportError while importing test module '/home/sagar/doccano-fork/worktrees/trial1-ml-service/backend/api/tests/test_commands.py'.
...
E   ModuleNotFoundError: No module named 'api'
...
E   ModuleNotFoundError: No module named 'model_mommy'
...
E   django.core.exceptions.ImproperlyConfigured: Requested setting REST_FRAMEWORK, but settings are not configured. You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
...
=========================== short test summary info ============================
ERROR backend/api/tests/test_commands.py
ERROR backend/api/tests/test_config.py
ERROR backend/api/tests/test_middleware.py - django.core.exceptions.Improperl...
ERROR backend/auto_labeling/tests/test_views.py
ERROR backend/data_export/tests/test_catalog.py
ERROR backend/data_export/tests/test_dataset.py
ERROR backend/data_export/tests/test_formatters.py
ERROR backend/data_export/tests/test_labels.py
ERROR backend/data_export/tests/test_models.py
ERROR backend/data_export/tests/test_task.py
ERROR backend/data_export/tests/test_views.py
ERROR backend/data_import/tests/test_catalog.py
ERROR backend/data_import/tests/test_data.py
ERROR backend/data_import/tests/test_examples.py
ERROR backend/data_import/tests/test_label.py
ERROR backend/data_import/tests/test_label_types.py
ERROR backend/data_import/tests/test_labels.py
ERROR backend/data_import/tests/test_makers.py
ERROR backend/data_import/tests/test_parser.py
ERROR backend/data_import/tests/test_reader.py
ERROR backend/data_import/tests/test_tasks.py - django.core.exceptions.Improp...
ERROR backend/data_import/tests/test_views.py
ERROR backend/examples/tests/test_assignment.py
ERROR backend/examples/tests/test_comment.py
ERROR backend/examples/tests/test_example.py
ERROR backend/examples/tests/test_example_state.py
ERROR backend/examples/tests/test_filters.py
ERROR backend/examples/tests/test_models.py
ERROR backend/examples/tests/test_usecase.py
ERROR backend/label_types/tests/test_models.py
ERROR backend/label_types/tests/test_views.py - django.core.exceptions.Improp...
ERROR backend/labels/tests/test_bbox.py
ERROR backend/labels/tests/test_category.py
ERROR backend/labels/tests/test_relation.py
ERROR backend/labels/tests/test_span.py
ERROR backend/labels/tests/test_text_label.py
ERROR backend/labels/tests/test_views.py
ERROR backend/projects/tests/test_member.py
ERROR backend/projects/tests/test_project.py
ERROR backend/projects/tests/test_tag.py
ERROR backend/roles/tests/test_views.py
ERROR backend/users/tests/test_views.py - django.core.exceptions.ImproperlyCo...
!!!!!!!!!!!!!!!!!!! Interrupted: 42 errors during collection !!!!!!!!!!!!!!!!!!!
8 warnings, 42 errors in 7.86s

$ /tmp/trial1-ml-review-venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from fastapi_service.main import app
client = TestClient(app)
for text in ["This is fine.", "London is rainy.", "John met Mary."]:
    r = client.post('/annotate', json={'text': text})
    print(text)
    print(r.json())
PY
This is fine.
{'sentiment': {'label': 'NEUTRAL', 'score': 0.5}, 'entities': [{'label': 'ORG', 'start_offset': 0, 'end_offset': 4, 'text': 'This'}]}
London is rainy.
{'sentiment': {'label': 'NEUTRAL', 'score': 0.5}, 'entities': [{'label': 'ORG', 'start_offset': 0, 'end_offset': 6, 'text': 'London'}]}
John met Mary.
{'sentiment': {'label': 'NEUTRAL', 'score': 0.5}, 'entities': [{'label': 'ORG', 'start_offset': 0, 'end_offset': 4, 'text': 'John'}, {'label': 'ORG', 'start_offset': 9, 'end_offset': 13, 'text': 'Mary'}]}
```

### Issues Found
1. [MAJOR] The shipped local dependency set does not install the spaCy model, so a normal `pip install -r fastapi_service/requirements.txt` run does not use real spaCy NER at all.
   - File: fastapi_service/requirements.txt
   - Line: 3
   - Why it's wrong: `requirements.txt` only installs `spacy`, not `en_core_web_sm`. In that state `get_nlp()` falls back to the heuristic branch in `fastapi_service/ner.py`, so the service does not satisfy the promised "spaCy for NER" behavior unless the user happens to build the Docker image.
   - How to fix: Make the model installation part of the reproducible setup for the standalone service. Either add the model as an installable dependency or fail startup with a clear error if the model is missing instead of silently degrading.

2. [MAJOR] The fallback NER implementation is actively wrong and emits false `ORG` entities for ordinary capitalized tokens.
   - File: fastapi_service/ner.py
   - Line: 20
   - Why it's wrong: The regex `^[A-Z][A-Za-z0-9&.-]+$` marks almost any capitalized token as an organization. I reproduced incorrect outputs for `"This is fine."`, `"London is rainy."`, and `"John met Mary."`, where `This`, `London`, `John`, and `Mary` were all returned as `ORG`. That is not a harmless approximation; it is bad data that would create wrong doccano labels.
   - How to fix: Remove this regex fallback, replace it with a much narrower fallback that only matches explicitly enumerated entities, or refuse requests until the real spaCy model is available.

3. [MAJOR] The new test does not verify sentiment behavior, so a broken implementation would still pass.
   - File: tests/test_annotate.py
   - Line: 23
   - Why it's wrong: The test only checks that the label is one of `POSITIVE`, `NEGATIVE`, or `NEUTRAL` and that the score is a float in `[0, 1]`. An implementation that always returns `{"label": "NEUTRAL", "score": 0.5}` would still pass this test. That violates the review rule against tests that only check types/existence rather than behavior.
   - How to fix: Add at least one positive and one negative sentiment assertion with expected labels for concrete texts, and make those assertions exact enough that an always-neutral implementation fails.

### What the Next Builder Must Do (if REJECTED)
1. Make the standalone service install or require a real spaCy English model as part of its normal setup, not only inside the Docker image.
2. Remove or replace the current capitalized-word fallback in `fastapi_service/ner.py` so the service does not emit bogus `ORG` spans when the model is unavailable.
3. Rewrite `tests/test_annotate.py` so it validates sentiment behavior with concrete expected labels for known positive and negative inputs.
4. Re-run the FastAPI service tests after those fixes and include a reproducible command for running the service in a correctly provisioned environment.

### What Was Done Well
The response shape matches the task, the FastAPI surface area is minimal, and the health endpoint is implemented cleanly. The Dockerfile also shows the right intent by downloading `en_core_web_sm`; that part should be preserved once the non-Docker setup is made consistent.
