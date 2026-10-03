# Codex Workflow for NovaBW

## Role split

Use ChatGPT for:

- architecture decisions
- RL/self-play design
- research planning
- replay/expert-knowledge methodology
- milestone prioritization
- experiment interpretation

Use Codex for:

- reading the local repository
- editing C++/Python
- building
- running OpenBW tests
- reading exact logs
- debugging
- targeted and core regression
- refactoring
- Git diff/status/checkpoints

The durable project rules are in the repository root `AGENTS.md`.

## Recommended local entry point

Repository:

`~/NovaBW/stardust-env`

Open that exact folder in Codex Desktop, or start Codex CLI from that directory.

## Development loop

For a normal NovaBW implementation task, Codex should:

1. Read `AGENTS.md`.
2. Inspect `git status` and relevant source/tests.
3. Verify any BWAPI API that is materially uncertain.
4. Make the smallest coherent implementation.
5. Build the tests target.
6. Run a targeted test first.
7. Diagnose the exact failure if it fails.
8. Repeat until the targeted test passes.
9. Run `python scripts/novabw_test.py core`.
10. Update experiment documentation.
11. Show a concise diff/status summary.
12. Create a local checkpoint commit only after tests pass.
13. Push only according to the repository/publishing instruction from the user.

## Commands Codex should know

Build:

`cmake --build build -j"$(sysctl -n hw.logicalcpu)"`

Core regression:

`python scripts/novabw_test.py core`

Tests must run from `build/test` when invoked directly.

OpenBW environment:

`OPENBW_GAME_SPEED=0`
`OPENBW_ENABLE_UI=0`

## Failure handling

Do not hide or work around a failing gameplay assertion.

Classify failures into:

- compile/API error
- candidate/mask error
- Adapter execution error
- Python serialization/policy error
- scheduler/reservation error
- actual gameplay-state failure
- known OpenBW teardown infrastructure issue

Always cite the exact failing log line/state in the task summary.

## Capability additions

Prefer editing `src/NovaBW/CapabilityRegistry.h`.

Use semantic keys such as:

- `zerg_lurker`
- `lurker_aspect`
- `zerg_spire`

Python policy code should not depend on BWAPI numeric IDs.

Avoid adding per-capability execution logic if generic Build/Morph/Research/Upgrade already represents the mechanic.

## Session handoff

At the end of a Codex task, return:

- files changed
- behavior added/fixed
- tests run
- exact PASS/FAIL
- any known infrastructure issue
- git commit SHA if committed
- suggested next milestone

Copy that summary back into the NovaBW ChatGPT project when architectural follow-up or prioritization is needed.
