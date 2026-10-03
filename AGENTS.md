# NovaBW AGENTS.md

## Mission

NovaBW is a long-term StarCraft: Brood War AI research and engineering project.

Primary objective:

- Build a strong Zerg-first agent that can eventually play complete games.
- Learn from professional human knowledge and replay data.
- Improve through imitation learning, reinforcement learning, self-play, historical checkpoints, and league training.
- Keep the runtime adapter separate from the policy.

Race priority:

- Zerg: ZvT, ZvP, ZvZ
- Terran initially: TvZ only, mainly as a training opponent
- Protoss initially: PvZ only, mainly as a training opponent

Do not spend time on unrelated Terran/Protoss matchups until the Zerg agent is mature.

## Architecture boundary

Training path:

OpenBW -> common Observation -> NovaBW policy -> common Action -> OpenBW

Future private-game path:

StarCraft: Remastered -> Remastered Adapter -> common Observation -> same NovaBW policy -> common Action -> Remastered Adapter -> StarCraft: Remastered

The policy must not depend directly on BWAPI/OpenBW/Remastered-specific objects.

## Current environment

Primary local environment:

- macOS
- Apple Silicon
- C++
- OpenBW / BWAPI
- Python
- PyTorch
- MPS where useful

Local repository:

~/NovaBW/stardust-env

Canonical repository:

jinwuuju/NovaBW

OpenBW accelerated test environment:

- OPENBW_GAME_SPEED=0
- OPENBW_ENABLE_UI=0

Run OpenBW tests from:

~/NovaBW/stardust-env/build/test

because OpenBW game data is CWD-sensitive.

## Engineering rules

For every capability:

1. Verify the exact BWAPI/OpenBW API before implementing.
2. Prefer declarative Capability Registry additions over per-capability Adapter code.
3. Implement the smallest deterministic behavior first.
4. Verify the actual in-game state changed.
5. Verify the same behavior through the common Adapter.
6. Verify PythonBridge / Python semantic control when applicable.
7. Run relevant regression tests before declaring completion.
8. Preserve a working checkpoint before large changes.
9. Diagnose failures from the exact log; do not guess.
10. Do not jump ahead to unrestricted full-game RL when lower-level control is unreliable.

Evidence examples:

- Move: unit position changes.
- Gather: minerals/gas actually increase.
- Train/Morph: the new unit actually appears and completes.
- Build: the structure actually appears and completes.
- Research/Upgrade: the technology or level is actually completed.
- Attack: target HP decreases or combat state changes.
- RL: evaluation improves beyond the baseline.

## Capability architecture

New Zerg capabilities should start in:

src/NovaBW/CapabilityRegistry.h

Prefer reuse of generic:

- Build
- Morph
- Research
- Upgrade
- Gather
- Attack

Do not add capability-specific execution branches to OpenBWAdapter unless the generic action family cannot represent the game mechanic correctly.

Canonical semantic keys are the policy-facing interface. Python policy code must not hard-code BWAPI numeric IDs.

Current pattern:

Capability Registry
-> semantic action candidates
-> common Action
-> generic OpenBWAdapter execution
-> Scenario Harness
-> Direct / Adapter / Python regression

Reusable test helpers:

src/NovaBW/ScenarioHarness.h

Regression runner:

python scripts/novabw_test.py core

Targeted suites may be used during development. Run the broader core regression before completing a milestone.

## Structured action direction

Long-term action space should be factorized:

command type
-> actor unit
-> target unit / spatial target
-> unit/building/tech/upgrade type as needed

Use masks/candidates for invalid actions. Do not expose arbitrary impossible actions.

Likely action families:

- None
- Move
- Gather
- ReturnCargo
- Train / Morph
- Build
- Attack
- Stop / Hold
- Burrow / Unburrow
- Load / Unload
- Research
- Upgrade
- UseTech

## Zerg scheduler safety

Zerg workers morph into buildings. A Drone that has accepted a Build command must not immediately be retasked by generic mineral scheduling.

Reserve builders until the intended building appears, then release the reservation.

Use retry/timeouts only when a previously accepted construction fails to materialize.

Keep dedicated gas workers out of idle-mineral scheduling.

This rule is already required by the Hydra/Research and later Python integration tests.

## Testing rules

Prefer three layers for new control-surface capabilities:

1. deterministic direct BWAPI test
2. common Adapter test
3. Python semantic integration test

Capability bundles may implement all three in one pass, but verification must remain layered and fail-fast.

Do not use DemoAIModule for NovaBW gameplay tests.

Keep existing working regressions.

Known test-infrastructure issue:

OpenBWData/ASIO can occasionally SIGSEGV during opponent teardown after a game has already reached the intended state. Do not classify a capability as failed solely from this known teardown signature without checking the gameplay-state assertions and exact lifecycle. Avoid manual leaveGame() from capability test modules; use the normal BWTest lifecycle.

When stale-code risk exists, pin source revisions and verify a unique marker is present in the rebuilt test binary.

## Current validated milestones

Infrastructure:

- OpenBW on Apple Silicon
- common Observation/Action protocol
- OpenBWAdapter
- C++ <-> Python TCP bridge
- PyTorch/MPS inference
- continuous neural control
- accelerated headless execution
- Probe PPO navigation infrastructure validation

Nova-Z:

- mineral observation and Gather
- actual mineral-income verification
- Drone production
- Overlord / supply management
- Larva morph
- Spawning Pool -> Zergling
- visible enemy observation
- scouting
- Attack with actual damage
- Python combat vertical slice
- autonomous rule baseline
- full-game passive-opponent baseline: 19/19 multi-map wins
- Extractor / gas gathering
- Hatchery -> Lair
- Hydralisk Den
- Hydralisk
- generic Research
- generic Upgrade
- Burrowing
- Muscular Augments
- Spire
- Mutalisk
- Scourge
- Zerg Flyer Attacks
- Lurker Aspect
- Lurker

The Probe PPO experiment validated infrastructure only. It is not part of the final Zerg gameplay policy.

## Next development direction

Near-term capability work should continue using the registry architecture.

Likely next bundles:

- Queen's Nest -> Hive -> Defiler Mound -> Defiler -> Consume / Plague
- Ultralisk Cavern -> Ultralisk -> speed/armor upgrades
- remaining Zerg buildings, upgrades, spells, transport, static defense, and Nydus
- full Zerg control-surface regression

After the major Zerg control surface is reliable:

- replay-aligned trajectories
- behavior cloning
- curriculum RL
- self-play
- historical checkpoint opponents
- league training
- multi-map regression

Do not train only against the latest copy of the same policy.

## Human expert knowledge

Professional strategy knowledge is useful as:

- curriculum
- supervision
- behavioral prior
- scenario definition
- strategic label
- evaluation knowledge

Do not hard-code human expert strategy as immutable rules.

Keep source attribution, player, year/era, matchup, map, patch/version, and confidence when importing expert knowledge.

## Repository policy

Do not commit:

- MPQ/game archives
- large replay archives
- generated trajectory corpora
- PyTorch checkpoints
- build directories
- virtual environments
- temporary logs
- runs/

Commit:

- source code
- schemas
- configuration
- dataset manifests
- evaluation code
- reproducible tooling
- architecture docs
- strategy templates
- experiment records

## Git workflow

Before significant changes:

- inspect git status
- understand any existing uncommitted user changes
- do not discard unrelated local work

During implementation:

- make coherent, reviewable changes
- build and test locally
- fix exact failures
- avoid regex-based source rewriting when normal source edits are possible

On milestone completion:

- run the relevant targeted regression
- run core regression
- summarize the observed evidence
- update experiment documentation
- create a local Git checkpoint/commit
- push only when explicitly requested or when the user has clearly delegated repository publishing for that task

Never rewrite or force-push history unless explicitly requested.

## Safety boundary

Development is for research, local simulation, and consensual/private games.

Transparent adapters for private/custom StarCraft: Remastered games are acceptable.

Do not implement:

- anti-cheat bypasses
- stealth injection
- detection evasion
- public-ladder cheating
