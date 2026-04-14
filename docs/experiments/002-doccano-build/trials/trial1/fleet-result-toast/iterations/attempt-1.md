#### Exploration
- No prior attempt notes existed in the output directory.
- Backend auto-labeling lives in [backend/auto_labeling/views.py](/home/sagar/doccano-fork/worktrees/trial1-result-toast/backend/auto_labeling/views.py) and currently looped through configs, saved labels, and always returned `{"ok": true}`.
- Persisted label creation happens through [backend/auto_labeling/pipeline/labels.py](/home/sagar/doccano-fork/worktrees/trial1-result-toast/backend/auto_labeling/pipeline/labels.py), where duplicate filtering already happens before `bulk_create`; that was the right place to derive real created counts.
- Frontend auto-label requests flow through [frontend/domain/models/tasks/annotationRepository.ts](/home/sagar/doccano-fork/worktrees/trial1-result-toast/frontend/domain/models/tasks/annotationRepository.ts), but the response was discarded.
- Task pages each handled auto-labeling separately. Some Composition API pages were also calling `autoLabel()`/refresh helpers without `projectId`, which would have made the new toast path unreliable.

#### Approach
- Backend:
  - Extended `LabelCollection.save()` to return the actual number of persisted labels after duplicate filtering.
  - Changed `AutomatedLabeling.create()` to aggregate `created` counts by task type bucket and collect per-config errors instead of aborting the whole request.
- Frontend:
  - Made repository/service auto-label calls return the backend payload.
  - Added shared formatter logic in [frontend/utils/autoLabeling.js](/home/sagar/doccano-fork/worktrees/trial1-result-toast/frontend/utils/autoLabeling.js) and a shared snackbar component in [frontend/components/tasks/autoLabeling/AutoLabelingSnackbar.vue](/home/sagar/doccano-fork/worktrees/trial1-result-toast/frontend/components/tasks/autoLabeling/AutoLabelingSnackbar.vue).
  - Wired toast display into the task pages that invoke auto-labeling: text classification, sequence labeling, intent/slot, seq2seq, speech-to-text, image captioning, image classification, object detection, and segmentation.
  - Fixed the Composition API pages that were invoking `autoLabel()` with the wrong argument list.
- Tests written:
  - Backend: extended [backend/auto_labeling/tests/test_views.py](/home/sagar/doccano-fork/worktrees/trial1-result-toast/backend/auto_labeling/tests/test_views.py) to assert created-count payloads and partial-failure error collection.
  - Frontend: added [frontend/test/unit/pages/projects/sequenceLabeling.spec.js](/home/sagar/doccano-fork/worktrees/trial1-result-toast/frontend/test/unit/pages/projects/sequenceLabeling.spec.js) to verify success and failure snackbar messages on a real page component workflow.

#### Results
- Code changes completed and committed in `4b30d587` (`Add auto-labeling result summaries`).
- Structural verification passed:
  - `git diff --check` returned no whitespace/errors.
- Test execution was blocked by missing local tooling in this environment:
  - `python3 -m pytest backend/auto_labeling/tests/test_views.py`
    - `/usr/bin/python3: No module named pytest`
  - `python3` also does not have `django` or `rest_framework` installed.
  - `yarn test --runInBand ...`
    - `/bin/sh: 1: jest: Permission denied`
  - `node ./node_modules/jest/bin/jest.js ...`
    - `Cannot find module '/home/sagar/doccano-fork/worktrees/trial1-result-toast/frontend/node_modules/jest/bin/jest.js'`

#### Problems
- Full backend verification could not run because the worktree has no Python environment with project dependencies installed.
- Full frontend verification could not run because this worktree has no local Jest installation/executable, and the shared parent `node_modules` did not contain a runnable `jest/bin/jest.js`.
- I did not install dependencies into the worktree because that would have turned this attempt into environment provisioning rather than product work.

#### Advice for Next Attempt
- First, provision a runnable backend env for this worktree or point the worktree at an existing venv with Django/DRF/pytest installed.
- Then install or link frontend test dependencies for this worktree and run:
  - `python3 -m pytest backend/auto_labeling/tests/test_views.py`
  - `node <path-to-jest> --config frontend/jest.config.js --runInBand frontend/test/unit/pages/projects/sequenceLabeling.spec.js`
- After tooling is available, verify the backend response shape carefully:
  - success with multiple config types
  - partial success where one config fails
  - zero-created cases, which currently show `No labels were added`
- Manual smoke test should focus on one text task first:
  - enable auto-labeling on sequence labeling or text classification
  - confirm the snackbar shows a success summary on created labels
  - confirm a failed config shows `Auto-labeling failed: ...`
