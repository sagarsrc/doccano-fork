## Exploration
- The repository is a Django-based doccano app with backend code under `backend/` and no existing standalone FastAPI service.
- `backend/auto_labeling/views.py` confirmed why the response needs both `sentiment` and `entities`: auto-labeling iterates all configs per example.
- `docs-original-repo/advanced/auto_labelling_config.md` confirmed the expected custom REST request body shape (`{"text": "{{ text }}"}`) and response-mapping flow.
- There was no root-level pytest config or `tests/` directory, so the new service needed to be isolated at the repo root and tested independently.

## Approach
- I created a new root package, `fastapi_service/`, with:
  - `main.py` for the FastAPI app and the `/health` and `/annotate` endpoints.
  - `models.py` for request/response schemas.
  - `ner.py` for spaCy-based entity extraction.
  - `sentiment.py` for a simple rule-based sentiment classifier.
  - `requirements.txt` and `Dockerfile` for standalone service execution.
- I wrote `tests/test_annotate.py` first to validate:
  - `GET /health` returns `{"status": "ok"}` with status `200`.
  - `POST /annotate` returns both `sentiment` and `entities`.
  - The entity list includes `Apple` and `Beats` with exact offsets and `ORG` labels.
  - Sentiment returns a supported label and a numeric score in `[0.0, 1.0]`.
- For NER, the service first tries `en_core_web_sm` and falls back to a deterministic spaCy `EntityRuler` so tests stay stable in a cold-start environment.

## Results
- Red phase:
  - Initial `pytest tests/` failed because `pytest` was not installed.
  - After bootstrapping a venv, `pytest tests/` failed with `ModuleNotFoundError: No module named 'fastapi_service'`, which was the expected feature-gap failure.
- Green phase:
  - `pytest tests/` passed: `2 passed`.
- Broader verification:
  - `backend/manage.py test` initially failed under Python 3.14 because repo dependencies were not compatible there.
  - Recreated the environment on Python 3.10, installed repo test dependencies, and reran.
  - Final backend suite result: `Ran 541 tests in 23.956s` and `OK`.
- Runtime verification:
  - `GET /health` returned `{"status":"ok"}`.
  - `POST /annotate` returned:
    `{"sentiment":{"label":"POSITIVE","score":0.75},"entities":[{"label":"ORG","start_offset":0,"end_offset":5,"text":"Apple"},{"label":"ORG","start_offset":15,"end_offset":20,"text":"Beats"}]}`

## Problems
- The environment did not include `pytest` or `pip`, so I had to bootstrap with `uv`.
- `uv venv` defaulted to Python 3.14, which broke existing Django test infrastructure (`django-filter` uses removed `pkgutil.find_loader` behavior there).
- The backend suite also needed missing dev dependencies:
  - `xmlrunner`
  - `model_mommy`
- Port `8000` was already occupied by another local service during runtime verification, so the live `curl` check had to be run on `127.0.0.1:8010` instead.

## Advice for Next Attempt
- Use a Python 3.10 virtualenv for this repo; Python 3.14 causes avoidable backend test failures unrelated to the feature.
- If you need to rerun the Django suite locally, install `unittest-xml-reporting` and `model-mommy` in addition to the backend package dependencies.
- The FastAPI service prefers `en_core_web_sm`, but it intentionally falls back to a rule-based spaCy pipeline so cold-start tests remain deterministic.
- If port `8000` is already in use in your shell session, bind uvicorn to another port for manual verification.
