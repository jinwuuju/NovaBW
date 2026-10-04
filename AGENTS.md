# NovaBW Agent Guide

NovaBW is a Zerg-first StarCraft: Brood War AI project.

## Read first

Use these as the durable source of truth:

- `docs/ARCHITECTURE.md`
- `docs/ZERG_FIRST_SCOPE.md`
- `docs/MASTER_ROADMAP.md`
- `docs/PRE_LEARNING_BASELINE_V1.md`
- `docs/AUTONOMOUS_LEARNING_SYSTEM_V1.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/experiments/NOVAZ_GATHER_DETERMINISTIC.md`

For substantial multi-file features or refactors, follow `.agent/PLANS.md`.

## Core architecture

Training:

OpenBW -> common Observation -> NovaBW policy -> common Action -> OpenBW

Future private-game runtime:

StarCraft: Remastered -> Remastered Adapter -> common Observation -> same policy -> common Action -> Remastered Adapter -> StarCraft: Remastered

The policy must not depend directly on OpenBW/BWAPI/Remastered objects.

Race priority:

- Zerg: ZvT, ZvP, ZvZ
- Terran initially: TvZ only
- Protoss initially: PvZ only

## Local environment

Repository:

`~/NovaBW/stardust-env`

Stack:

- macOS / Apple Silicon
- C++
- OpenBW / BWAPI
- Python / PyTorch / MPS

Run OpenBW tests from `build/test` because game data is CWD-sensitive.

Accelerated environment:

- `OPENBW_GAME_SPEED=0`
- `OPENBW_ENABLE_UI=0`

Build:

`cmake --build build -j"$(sysctl -n hw.logicalcpu)"`

Core regression:

`python scripts/novabw_test.py core`

## Engineering contract

For every capability:

1. Verify uncertain BWAPI/OpenBW API details before implementation.
2. Prefer declarative capability registration.
3. Make the smallest coherent implementation.
4. Prove the actual game state changed.
5. Validate Direct -> Adapter -> Python where applicable.
6. Run targeted tests first, then core regression.
7. Diagnose exact logs; do not guess.
8. Preserve working checkpoints before large changes.
9. Do not declare completion with failing gameplay assertions.

Evidence means real state change:

- Move -> position changes
- Gather -> resources increase
- Build -> structure appears/completes
- Morph/Train -> unit appears/completes
- Research/Upgrade -> technology/level completes
- Attack -> actual damage/combat change
- RL -> evaluation improvement beyond baseline

## Capability system

Start new Zerg capabilities in:

`src/NovaBW/CapabilityRegistry.h`

Reusable test helpers:

`src/NovaBW/ScenarioHarness.h`

Prefer generic action families:

- Build
- Morph
- Research
- Upgrade
- Gather
- Attack

Do not add capability-specific Adapter branches when the generic action family already represents the mechanic correctly.

Python policies must use semantic keys, not hard-coded BWAPI numeric IDs.

Long-term action space is factorized:

command -> actor -> target/spatial target -> unit/building/tech/upgrade

Use candidates/masks for invalid actions.

## Zerg scheduler invariant

A Drone with an accepted Build command must be reserved until the intended building appears.

Do not let generic mineral scheduling overwrite an active build command.

Keep dedicated gas workers out of idle-mineral scheduling.

Use timeout/retry only when a build fails to materialize.

## Test policy

Prefer three layers:

1. deterministic direct BWAPI
2. common Adapter
3. Python semantic integration

Do not use DemoAIModule for NovaBW gameplay tests.

Known infrastructure issue:

OpenBWData/ASIO can occasionally SIGSEGV during teardown after intended gameplay state has already been reached. Inspect exact lifecycle/state before classifying this as a gameplay failure.

Avoid manual `leaveGame()` in capability modules. Use normal BWTest lifecycle.

When stale-code risk exists, pin source revisions and verify a unique marker in the rebuilt test binary.

## Current validated control surface

Validated milestones include:

- Gather / mineral income
- Drone / Overlord / Larva
- Pool / Zergling
- scouting / enemy observation / Attack
- passive-opponent full-game baseline: 19/19 multi-map
- Extractor / gas
- Lair
- Hydralisk Den / Hydralisk
- generic Research / Upgrade
- Burrowing / Muscular Augments
- Spire / Mutalisk / Scourge / Zerg Flyer Attacks
- Lurker Aspect / Lurker

Probe PPO was infrastructure validation only, not the final gameplay policy.

## Learning gate

Before any PPO, self-play, league training, or autonomous policy improvement begins, the local repository must pass `docs/PRE_LEARNING_BASELINE_V1.md`. Do not bypass this gate.

## Autonomous learning direction

After `docs/PRE_LEARNING_BASELINE_V1.md` passes, follow `docs/AUTONOMOUS_LEARNING_SYSTEM_V1.md` as the learning execution contract.

Key rules:

- user-provided strategy knowledge is a first-class training asset
- professional replays are optional future enrichment, not a v1 dependency
- TvZ/PvZ opponents begin as parameterized knowledge-driven sparring families
- skills are decomposed into a fine-grained prerequisite DAG
- use six concurrent OpenBW actors as the initial production setting until a higher concurrency is benchmark-promoted
- no checkpoint promotion from training loss alone
- every learning stage requires immutable evaluation, rolling evaluation, regression checks, and explicit promote/reject decisions
- preserve historical promoted checkpoints for later self-play/league sampling

## Near-term direction

Continue registry-based Zerg coverage:

- Queen's Nest -> Hive -> Defiler Mound -> Defiler -> Consume / Plague
- Ultralisk Cavern -> Ultralisk -> related upgrades
- remaining Zerg buildings, spells, transport, static defense, Nydus
- full Zerg control-surface regression

Then:

- structured strategy-card compilation
- synthetic scenario / sparring trajectories
- optional future replay-aligned trajectories
- behavior cloning where supervised targets exist
- curriculum RL
- self-play
- historical checkpoint opponents
- league training
- multi-map regression

Human expert knowledge is curriculum/supervision/prior/evaluation input, not immutable strategy.

## Git / repository rules

Before edits:

- inspect `git status`
- preserve unrelated user changes
- do not rewrite history

Do not commit:

- MPQ/game archives
- large replay archives
- generated trajectory corpora
- checkpoints
- build/
- virtual environments
- temporary logs / runs/

Commit source, schemas, config, manifests, evaluation code, reproducible tooling, and docs.

On milestone completion:

- targeted regression PASS
- core regression PASS
- experiment doc updated
- concise diff/status summary
- local checkpoint commit
- push only when explicitly requested or clearly delegated

## Safety

Research/local simulation/private consensual games only.

Do not implement anti-cheat bypasses, stealth injection, detection evasion, or public-ladder cheating.
