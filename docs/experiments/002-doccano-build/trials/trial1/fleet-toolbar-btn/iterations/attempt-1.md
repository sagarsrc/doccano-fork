## Exploration
- The shared desktop toolbar lives in `frontend/components/tasks/toolbar/ToolbarLaptop.vue` and already contains the existing auto-labeling settings entrypoint via `ButtonAutoLabeling` and `FormAutoLabeling`.
- Task pages split into two patterns:
- Composition API pages: `text-classification`, `image-captioning`, `sequence-to-sequence`, `speech-to-text`. These already consume composables with built-in auto-label methods (`useTeacherList`, `useTextLabel`).
- Options API pages: `sequence-labeling`, `intent-detection-and-slot-filling`, `image-classification`, `object-detection`, `segmentation`. These already expose `autoLabel(...)` methods but needed an explicit refresh handler for one-click use.
- Auto-label requests ultimately go through repository/service methods already present in the codebase, so the feature only needed UI wiring and page event handling.
- Frontend unit tests are very sparse in this worktree. The only existing spec was `frontend/test/unit/components/tasks/toolbar/forms/formGuideline.spec.js`.

## Approach
- Added a new toolbar button component at `frontend/components/tasks/toolbar/buttons/ButtonAutoLabelNow.vue`.
- Updated `ToolbarLaptop.vue` to render the new button alongside the existing auto-label settings button and emit a new `auto-label` event upward.
- Wired every task page that mounts `ToolbarLaptop` to handle `@auto-label`.
- Composition API pages call their existing composable auto-label methods for the current example.
- Options API pages now expose `autoLabelCurrentExample()` methods that call the existing service/repository auto-label method and then refresh annotations for the current item.
- Tests written:
- `frontend/test/unit/components/tasks/toolbar/buttons/buttonAutoLabelNow.spec.js`
- Validates tooltip text is rendered and the new component emits `click:auto-label` on click.
- `frontend/test/unit/components/tasks/toolbar/toolbarLaptop.spec.js`
- Validates the toolbar re-emits the new `auto-label` event when the child button fires.
- `frontend/test/unit/pages/projects/_id/task-auto-label.spec.js`
- Validates the sequence-labeling page handler triggers auto-labeling and refreshes the current document annotations.

## Results
- Red phase:
```text
FAIL buttonAutoLabelNow.spec.js: component file missing
FAIL toolbarLaptop.spec.js: new button/event wiring missing
FAIL task-auto-label.spec.js: page handler missing
```
- Targeted green-phase run:
```text
Test Suites: 3 passed, 3 total
Tests:       3 passed, 3 total
```
- Full frontend Jest run:
```text
Test Suites: 4 passed, 4 total
Tests:       4 passed, 4 total
```
- What worked:
- The one-click button now exists on `ToolbarLaptop`.
- All toolbar-mounting task pages are wired to trigger auto-labeling for the current example/item.
- Options API pages refresh annotations immediately after the manual auto-label action.

## Problems
- `frontend/package.json` does not currently declare `jest`, `vue-jest`, or `jest-transform-stub`, so `yarn test` failed initially with `/bin/sh: 1: jest: Permission denied`.
- I installed test-only dependencies locally without saving manifest changes so I could complete verification.
- Running Jest with coverage enabled hit unrelated repo issues during coverage instrumentation:
```text
Failed to collect coverage from .../components/example/FormAssignment.vue
ERROR: Unexpected token (1:709)
```
- I verified with `--collectCoverage=false` to avoid that unrelated failure and keep the regression check focused on executable tests.
- The pre-existing `formGuideline.spec.js` passes but logs Vuetify unknown-element warnings; I left that unchanged because it is unrelated to this task and non-failing.

## Advice for Next Attempt
- If a reviewer asks for broader frontend coverage, add more page-handler tests on the Options API pages first; they are straightforward to test without wrestling the current `.ts` composable/Jest setup.
- If the reviewer asks for composition-page unit coverage, expect to touch Jest config/tooling because the current config does not handle the repo’s `.ts` composable imports cleanly.
- Keep verification commands on `node ./node_modules/jest/bin/jest.js --runInBand --collectCoverage=false` unless the test tooling is cleaned up separately.
- Do not commit lockfile noise from temporary npm installs; I restored `frontend/yarn.lock` after verification.
