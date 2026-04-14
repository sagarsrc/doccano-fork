#### Exploration
- I inspected `backend/auto_labeling/pipeline/labels.py`, `backend/labels/models.py`, `backend/labels/managers.py`, and `backend/auto_labeling/tests/test_views.py`.
- `LabelCollection.save()` transforms labels, filters them with `filter_annotatable_labels()`, then calls `bulk_create()` with no intra-batch deduplication.
- `SpanManager.can_annotate()` returns `True` immediately when `project.allow_overlapping=True`, so exact duplicate spans are not blocked against existing rows in that mode.
- Existing span model validation blocks overlaps only when overlapping is disabled. There is no `unique_together` on `Span`.
- Existing auto-labeling tests already hit the real endpoint with patched pipeline output, so I followed that pattern.

#### Approach
- I chose a save-path fix in `backend/auto_labeling/pipeline/labels.py` instead of a new DB constraint.
- Reason: the manager already scopes visibility differently for collaborative vs non-collaborative projects through `get_labels()`, so save-time dedup can block exact duplicates without changing broader span semantics.
- I added two endpoint tests in `backend/auto_labeling/tests/test_views.py`:
- `test_deduplicates_duplicate_spans_in_single_pipeline_result`: patches the pipeline to return the same span twice in one response and asserts only one row is created.
- `test_does_not_create_duplicate_spans_across_auto_label_runs`: enables overlapping, calls the auto-label endpoint twice for the same example, and asserts the span count stays at one.
- Implementation detail: `Spans.deduplicate()` now builds a set of existing exact span keys from `Span.objects.get_labels(...)`, then removes duplicates both against existing scoped rows and within the current batch before `filter_annotatable_labels()` and `bulk_create()`.

#### Results
- Static verification passed:
- `python3 -m py_compile backend/auto_labeling/pipeline/labels.py backend/auto_labeling/tests/test_views.py`
- Runtime verification could not be completed in this environment.
- Attempted test commands:
- `poetry run python manage.py test auto_labeling.tests.test_views.TestAutomatedSpanLabeling`
- Result: `/bin/bash: line 1: poetry: command not found`
- `python3 manage.py test auto_labeling.tests.test_views.TestAutomatedSpanLabeling`
- Result: `ModuleNotFoundError: No module named 'django'`

#### Problems
- The backend environment is not provisioned in this workspace.
- `poetry` is not installed or not on `PATH`.
- System Python has no `pip`, and `python3 -m ensurepip --user` fails because `ensurepip` is disabled on this Debian/Ubuntu install.
- Because Django dependencies are unavailable, I could not run the red/green/full test cycle the protocol asks for.

#### Advice for Next Attempt
- First priority should be restoring a runnable backend environment so the endpoint tests can actually be executed.
- If you get Poetry or a virtualenv working, run:
- `poetry run python manage.py test auto_labeling.tests.test_views.TestAutomatedSpanLabeling`
- `poetry run python manage.py test auto_labeling.tests`
- Re-check collaborative span behavior under `allow_overlapping=True`; the current fix uses `get_labels()` scope, so exact duplicates are suppressed per the same visibility rules as other annotation checks.
- I intentionally did not add a `Span` DB uniqueness constraint because that would need more careful validation against overlapping and collaboration semantics plus a migration.
