---
title: "build fleet task bundle"
experiment: 001-research-repos
created: "2026-04-13 12:40 UTC"
---

# Final Task Bundle — 9 Tasks

## Backend + ML Service

### Task 1: FastAPI ML Service (NER + Sentiment)

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

---

### Task 2: Fix #2370 — Span Dedup in Auto-Labeling

**Bug:** `LabelCollection.save()` at `backend/auto_labeling/pipeline/labels.py:32` calls `filter_annotatable_labels()` against existing DB rows, then `bulk_create()`. No dedup within a single pipeline result. Spans have no `unique_together` constraint, and `SpanManager.can_annotate()` returns `True` when `allow_overlapping=True`. Repeated auto-label runs create duplicate span annotations.

**Fix:** Add dedup logic before `bulk_create()` — deduplicate labels within the batch by `(example, label, start_offset, end_offset)` for Spans, or add a unique constraint on the Span model.

**Files:**
- `backend/auto_labeling/pipeline/labels.py` — add dedup in `save()`
- `backend/labels/models.py` — consider adding `unique_together` on Span (check if `allow_overlapping` projects need special handling)
- `backend/auto_labeling/tests/test_views.py` — add test for duplicate prevention

**Verification:** `poetry run python manage.py test auto_labeling.tests` passes. Calling auto-label twice on the same example does not create duplicate spans.

---

### Task 3: Timeout + Error Handling for Auto-Labeling

**Problem:** `AutomatedLabeling.create()` at `views.py:154-165` calls external ML services synchronously with no timeout, no try/except, no error handling. A slow or dead service freezes the entire HTTP thread. Related GitHub issue #2345 ("server freezes").

**Fix:** Wrap each `execute_pipeline()` call in try/except with a configurable timeout (default 30s). Log failures per-config but continue to the next config. Return partial results with per-config error details in the response.

**Files:**
- `backend/auto_labeling/views.py` — wrap the config loop in `AutomatedLabeling.create()` with try/except + timeout
- `backend/auto_labeling/pipeline/execution.py` — add timeout parameter to `execute_pipeline()`
- `backend/auto_labeling/tests/test_views.py` — add tests for timeout and error scenarios

**Verification:** `poetry run python manage.py test auto_labeling.tests` passes. With ML service down, auto-labeling returns graceful error instead of hanging.

---

## Frontend

### Task 4: Auto-Label Button on Annotation Toolbar

**Current state:** Auto-labeling is behind a toggle switch (`ButtonAutoLabeling` → `FormAutoLabeling` dialog → `v-switch`). Users must open a dialog, flip a switch, then navigate examples. Not intuitive.

**Enhancement:** Add a prominent "Auto-Label" action button directly on `ToolbarLaptop` that triggers auto-labeling for the current example with one click. Keep the existing toggle for "auto-label on navigation" behavior.

**Files:**
- `frontend/components/tasks/toolbar/ToolbarLaptop.vue` — add new button that emits an `auto-label` event
- `frontend/components/tasks/toolbar/buttons/` — new `ButtonAutoLabelNow.vue` component (icon button with "Auto-Label This" tooltip)
- Task pages that mount the toolbar (`text-classification/index.vue`, `sequence-labeling/index.vue`, etc.) — handle the new event by calling `autoLabel(projectId, exampleId)`

**Key context:** Auto-label API is `POST /projects/${projectId}/auto-labeling?example=${exampleId}`. All annotation repositories already inherit `AnnotationRepository.autoLabel()` (`frontend/domain/models/tasks/annotationRepository.ts:48-55`). The composables `useTeacherList` and `useTextLabel` already have `autoLabel()` methods.

**Verification:** Button visible on toolbar. Clicking it triggers auto-labeling and annotations appear on current example.

---

### Task 5: ML Service Health Indicator on Config List

**Current state:** `ConfigList.vue` shows a table of auto-labeling configs with name and actions. No indication whether the configured ML service is actually reachable.

**Enhancement:** Add a green/red status dot next to each config in the list. On component mount, ping each config's service URL (via a new lightweight backend endpoint or the existing `testParameters` endpoint with a minimal payload) and show the result.

**Files:**
- `frontend/components/configAutoLabeling/ConfigList.vue` — add status column to `v-data-table`, call health check on mount
- `backend/auto_labeling/views.py` — add a lightweight `GET /projects/${projectId}/auto-labeling/configs/${configId}/health` endpoint that pings the configured URL and returns status (or reuse the existing `request-testing` endpoint)
- `backend/auto_labeling/urls.py` — register new endpoint

**Key context:** Each config stores `model_attrs` with a `url` field. The health check should hit the ML service's `/health` endpoint (Task 1 provides this). Timeout should be short (2-3s) to avoid blocking the UI.

**Verification:** Config list shows green dot when ML service is running, red dot when it's down.

---

### Task 6: Bulk Auto-Label Button

**Current state:** Auto-labeling works one example at a time. No way to auto-label all unlabeled examples in batch.

**Enhancement:** Add a "Bulk Auto-Label" button on the dataset/examples list page. When clicked, it sends auto-label requests for all selected (or all unlabeled) examples. Show a progress indicator.

**Files:**
- `frontend/pages/projects/_id/dataset/index.vue` — add "Bulk Auto-Label" button to the toolbar, wire up to new API endpoint
- `backend/auto_labeling/views.py` — add `BulkAutoLabeling` endpoint that accepts a list of example IDs and runs the pipeline for each
- `backend/auto_labeling/urls.py` — register bulk endpoint
- `backend/auto_labeling/tests/test_views.py` — add test for bulk endpoint

**Key context:** The existing `AutomatedLabeling.create()` at `views.py:154` handles one example. The bulk endpoint should loop over example IDs and call the same pipeline logic. Consider using Celery for large batches (Celery is already set up for import/export), or keep it synchronous with a progress response for small batches.

**Verification:** Select multiple examples on dataset page → click Bulk Auto-Label → all selected examples get annotations.

---

### Task 7: Auto-Label Result Toast/Feedback

**Current state:** After auto-labeling completes, the page silently reloads annotations. No feedback on what happened — how many labels were added, whether any configs failed, or if the service was unreachable.

**Enhancement:** After auto-labeling, show a Vuetify snackbar/toast with a summary: "Added 3 entities + 1 sentiment label" or "Auto-labeling failed: service unreachable". This requires the backend to return label counts in the auto-labeling response.

**Files:**
- `backend/auto_labeling/views.py` — modify `AutomatedLabeling.create()` response to include counts of labels created per task type and any errors
- `frontend/components/tasks/toolbar/ToolbarLaptop.vue` or the task pages — add snackbar component, display result summary after auto-label call returns
- Task pages (`text-classification/index.vue`, `sequence-labeling/index.vue`, etc.) — capture the auto-label response and show toast

**Key context:** Currently `AutomatedLabeling.create()` returns a generic 201 response. The response should be enriched with `{"created": {"categories": 1, "spans": 3}, "errors": []}`. The frontend `autoLabel()` in `annotationRepository.ts:48-55` posts to the endpoint — its response can be captured and displayed.

**Verification:** Auto-label an example → toast appears showing "Added 1 category, 3 spans" or error message.

---

## Infra/Tooling

### Task 8: Demo Setup Script

**Purpose:** One command to set up a complete demo environment — create project, add label types, import sample data, configure auto-labeling to point at the FastAPI ML service.

**Implementation:** Python script using Django management commands or REST API calls:
1. Create an `IntentDetectionAndSlotFilling` project (supports both Category + Span)
2. Create CategoryTypes: POSITIVE, NEGATIVE, NEUTRAL
3. Create SpanTypes: PER, ORG, LOC, DATE, MISC
4. Import 10-20 sample sentences via the data import API
5. Create two AutoLabelingConfig entries pointing at the FastAPI service:
   - Category config: `model_attrs={"url": "http://localhost:8000/annotate", "method": "POST", "body": {"text": "{{ text }}"}}`, template extracts `sentiment.label`, label_mapping maps to CategoryTypes
   - Span config: same URL, template extracts `entities[]` with `label/start_offset/end_offset`, label_mapping maps to SpanTypes

**Files:** New `scripts/setup-demo.py` (or `.sh`)

**Verification:** Run script → open doccano → project exists with sample data → click auto-label → annotations appear.

---

### Task 9: docker-compose.dev.yml

**Purpose:** One-command full-stack dev environment with the ML service included.

**Implementation:** Extend the existing `docker/docker-compose.prod.yml` with:
- Volume mounts for backend and frontend source (hot reload)
- ML service container built from `fastapi_service/Dockerfile`
- Django `runserver` instead of gunicorn
- Nuxt `yarn dev` instead of built assets
- Postgres + RabbitMQ from existing compose

**Files:** New `docker/docker-compose.dev.yml`

**Verification:** `docker-compose -f docker-compose.dev.yml up` → all services start → frontend at `localhost:3000`, backend at `localhost:8000`, ML service at `localhost:8001`.

---

## File Overlap Analysis

| Track | Files touched | Overlaps with |
|-------|--------------|---------------|
| ML Service (Task 1) | `fastapi_service/**` | None |
| Backend (Tasks 2, 3, 5-health, 6-bulk, 7-response) | `backend/auto_labeling/**` | All backend tasks share this module |
| Frontend (Tasks 4, 5-ui, 6-ui, 7-ui) | `frontend/components/**`, `frontend/pages/**` | All frontend tasks share these dirs |
| Infra (Tasks 8, 9) | `scripts/**`, `docker/**` | None |

**For worktree-fleet:** ML Service and Infra are fully independent. Backend and Frontend tasks share files within their track but not across tracks. Could split into 4 workers: `ml-service`, `backend`, `frontend`, `infra`.
