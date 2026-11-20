# Project instructions

## Project conventions

- Read `SPEC.md` and `PLAN.md` before implementing a feature.
- Use only the Python standard library. Keep code, tests, and output aligned with the spec.
- In `src/`, do not use `dict`, `set`, or Python's built-in `hash()`; use the project's
  explicit hash-table implementations or lists instead.
- Add or update focused tests before changing implementation behavior. Do not weaken or
  remove tests to make an implementation pass.
- Validate changes with `make test`. Keep errors explicit and avoid broad exception handling.

## Git workflow

- `main` is the stable branch and `develop` is the integration branch.
- Start each issue on `feature/<issue-number>-<short-name>`, branched from `develop`.
- Keep each issue's changes on its feature branch. Commit with
  `Step N: concise description (#N)`, then push the feature branch.
- When the step is complete and verified, fast-forward merge the feature branch into
  `develop` and push `develop`.
- Leave an issue open if any acceptance criterion or external action remains incomplete;
  otherwise close it after merging.
