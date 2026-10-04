# NovaBW Pre-Learning Baseline v1

## Purpose

Freeze one fully validated deterministic Nova-Z baseline before autonomous learning begins.

This milestone exists to prevent learning infrastructure from being built on top of an unverified local working tree.

No PPO, self-play, league training, or model-weight learning may begin until this gate passes.

## Current known state

Evidence reported from the local repository:

- Standard Amateur Match evaluation: 10/10 natural completions
- Standard Amateur Match result: 0 wins / 10 losses
- Average game length: ~34831.5 frames
- No recorded major macro stalls in the standard 10-game batch
- Pressure evaluation exposed a builder-reservation stall:
  - actor 631
  - reservation frame/state 36744
  - failure frame/state 39144
- Focused Python amateur tests: 24/24 PASS
- Strategy knowledge tests: 42/42 PASS
- Previous validated gameplay core baseline: 66/66 PASS
- Most recent core rerun was interrupted after 37 PASS markers and is not a fresh full-core PASS
- Latest Amateur Match source changes were intentionally left uncommitted because the full validation gate had not passed

The above must be re-verified locally. This document is a required process specification, not a substitute for local evidence.

## Non-goals

Do not in this milestone:

- start PPO
- start self-play
- create a league
- add unrelated gameplay capabilities
- weaken assertions
- hide pressure-test failures
- merge unrelated Git histories
- change remotes
- force-push or rewrite history

## Gate A — Repository preservation

Before editing:

1. Inspect git status, branch, remotes, and recent commits.
2. Preserve all existing user/local work.
3. Record the current diff before modifications.
4. Do not reset, clean, rebase, or discard unrelated changes.
5. Keep:
   - origin = StardustDevEnvironment
   - novabw = NovaBW canonical
   unchanged during this milestone.

## Gate B — Builder-reservation defect

Reproduce the pressure-match builder reservation failure if possible using the preserved evidence and current runner.

Diagnose from exact logs and state transitions.

Required questions:

- Which Drone/actor was reserved?
- Which intended structure was associated with the reservation?
- Did the actor morph/change unit ID?
- Did the structure materialize?
- Was the builder consumed by a different valid Zerg building?
- Was the reservation timeout based on actor identity when structure identity should have been used?
- Was a dedicated gas worker selected as a builder?
- Was a stale reservation retained after death/morph/cancel?
- Did the economy scheduler retask an active builder?

Fix the root cause in the smallest generic scheduler/reservation layer possible.

Do not add a one-off exception for the observed actor ID or one scenario.

Do not weaken the existing builder-stall oracle.

## Gate C — Focused regression

After the reservation fix:

1. Build the tests target.
2. Run the focused reservation/depot-loss/amateur-match fixtures.
3. Run the active pressure opponent evaluation.
4. Require natural completion without the prior reservation stall.
5. Preserve exact logs.

If a different gameplay failure occurs, diagnose it independently rather than broadening the original fix.

## Gate D — Fresh full regression

Run a fresh, uninterrupted core regression from the current source.

The prior 66/66 result is not sufficient for this gate.

Requirements:

- full suite completes
- zero failing gameplay assertions
- no hidden/skipped regressions introduced by this milestone
- Direct / Adapter / Python coverage remains intact

Record the exact test count because the core suite may have grown beyond 66.

## Gate E — Clean rebuild / stale artifact protection

Because prior NovaBW work exposed stale compiled test-code risk:

1. Perform a clean or dependency-safe rebuild of the relevant test target.
2. Verify new/changed scenario code is present in the binary where applicable.
3. Re-run at least the critical targeted suite after the clean rebuild.

Do not rely only on an incremental build for the frozen baseline.

## Gate F — Headless full-game smoke

Run a small headless batch with:

- OPENBW_GAME_SPEED=0
- OPENBW_ENABLE_UI=0

No watch window.

Minimum:

- standard opponent smoke
- pressure opponent smoke

Record:

- natural completion rate
- wins/losses
- runtime failures
- builder/scheduler stalls
- supply permanent stalls
- production deadlocks

This is not yet a playing-strength promotion gate. 0 wins is acceptable if the integration is stable.

## Gate G — Baseline manifest

Create a reproducibility manifest containing at least:

- local Git commit
- source file hashes for critical NovaBW protocol/adapter/policy/test files
- build configuration
- Python version / venv identifier
- OpenBW environment flags
- test suite names and counts
- relevant map assets/config identifiers
- strategy knowledge schema/compiler version
- timestamp
- known limitations

Do not commit large generated logs or binaries to ordinary Git history.

## Gate H — Freeze checkpoint

Only after every required gate passes:

1. Update the experiment record.
2. Review git diff.
3. Create one clear local commit, e.g.:
   `baseline: freeze Nova-Z pre-learning v1`
4. Verify working tree is clean.
5. Record the commit SHA.

Do not push as part of this gate unless separately instructed.

## Gate I — Canonical Git migration plan

After the baseline is frozen, inspect the history relationship between:

- local development history
- novabw/main canonical documentation history

Because these histories have previously had no merge-base, do not merge them blindly.

Produce a migration plan that preserves:

- the validated local source history
- the canonical NovaBW documentation/knowledge history
- all milestone checkpoint SHAs
- no force-push unless explicitly approved

Do not execute the migration during this milestone unless separately authorized.

## Success criteria

Pre-Learning Baseline v1 is complete only when:

- pressure builder-reservation defect is fixed generically
- focused pressure evaluation completes naturally
- fresh full core regression passes
- clean/dependency-safe rebuild is validated
- headless standard + pressure smoke completes without scheduler/runtime stalls
- reproducibility manifest exists
- final checkpoint commit exists
- working tree is clean

## After this milestone

The next milestone is:

NovaBW Autonomous Learning System v1 — Shadow Mode

Order:

1. fast headless throughput benchmark
2. compact telemetry
3. deterministic failure taxonomy
4. skill DAG
5. shadow-mode 100–500+ games with frozen policy
6. metric calibration
7. curriculum scheduler
8. immutable evaluation gates
9. checkpoint league infrastructure
10. only then: short skill PPO

Do not start unrestricted full-game self-play directly from this baseline.
