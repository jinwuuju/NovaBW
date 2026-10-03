# First Codex Task: NovaBW Local Repository Audit

Use this as the first task after opening `~/NovaBW/stardust-env` in Codex.

Read `AGENTS.md` first.

Goal: establish a clean, trustworthy local baseline before starting the next Zerg capability bundle.

Tasks:

1. Inspect `git status`, branch, remotes, and recent commits.
2. Do not discard or overwrite any uncommitted user work.
3. Inspect the current local versions of:
   - `src/NovaBW/CapabilityRegistry.h`
   - `src/NovaBW/ScenarioHarness.h`
   - `scripts/novabw_test.py`
   - Spire and Lurker test files/policies
4. Confirm the local source reflects the milestones already validated:
   - Hydra & Research v1
   - Spire Air v2
   - Lurker v1
5. Build the `tests` target.
6. Run the relevant Lurker targeted regression first.
7. Run `python scripts/novabw_test.py core`.
8. If anything fails, diagnose and fix from the exact log; do not guess.
9. If all tests pass, update any missing experiment record needed to reflect Lurker v1 completion.
10. Show the final diff and git status.
11. Create a local checkpoint commit named clearly for the validated baseline. Do not force-push or rewrite history.
12. Report:
    - exact tests run
    - exact results
    - files changed
    - commit SHA
    - whether the working tree is clean
    - any known OpenBW teardown issue observed

Do not begin Hive/Defiler in this first task. The purpose is to establish the baseline and hand back a verified checkpoint.
