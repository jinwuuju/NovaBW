# Nova-Z Deterministic Gather Milestone

## Purpose

This experiment is the first Nova-Z economy milestone.

Its purpose is to verify, deterministically and without reinforcement learning or Python policy control, that NovaBW can:

OpenBW game state → select a completed Zerg Drone → select a mineral field → issue Gather → observe an actual increase in owned minerals

The success criterion is an in-game state change, not merely successful command submission.

## Environment

- Backend: OpenBW / BWAPI
- Test harness: StardustDevEnvironment `BWTest`
- Test: `NovaBW.ZergGatherDeterministic`
- Player race: Zerg
- Opponent race: Terran
- Map: `maps/sscai/(4)Python.scx`
- Random seed: 12345
- Frame limit: 3,000
- Time limit: 60 seconds
- Runtime: accelerated headless execution
- Python policy: not used
- Reinforcement learning: not used

The OpenBW test executable was run from the directory containing the required legacy StarCraft MPQ assets.

## Milestone 1: direct BWAPI Gather validation

The deterministic test module:

1. Finds one existing, completed `Zerg_Drone`.
2. Finds a nearby mineral field.
3. Records `self()->minerals()` and `self()->gatheredMinerals()`.
4. Issues exactly one `Drone::gather(mineral)` command.
5. Waits for an actual mineral return.
6. Passes only if owned mineral count increases.
7. Also verifies cumulative gathered minerals increased.

Observed result:

- Drone ID: 83
- Drone position: (3856, 1376)
- Mineral field ID: 74
- Mineral position: (4000, 1328)
- Gather command issued: frame 0
- Starting minerals: 50
- Ending minerals: 58
- Starting gathered minerals: 50
- Ending gathered minerals: 58
- Mineral delta: +8
- First verified increase: frame 162
- `NovaBW.ZergGatherDeterministic`: PASS

This proves the intended game-state transition directly through BWAPI.

## Milestone 2: common protocol and OpenBWAdapter Gather validation

The common protocol was extended with:

- `Observation.resourceUnits`
- resource-unit ID, type, position, remaining resources, mineral/geyser flags
- `ActionType::Gather`
- `Action.targetUnitId`

`OpenBWAdapter::observe()` now exposes accessible mineral fields and geysers as common resource observations.

`OpenBWAdapter::execute()` now supports the first constrained Gather action:

common actor unit ID + common target unit ID → validate completed worker and mineral field → BWAPI `gather()`

A second deterministic regression test, `NovaBW.ZergGatherThroughAdapter`, was added. It deliberately chooses the Drone and mineral from the common Observation, constructs a common Gather Action, executes it through `OpenBWAdapter`, and passes only after the observed player mineral count increases.

Result:

- `NovaBW.ZergGatherThroughAdapter`: PASS
- resource observation path validated
- common Gather action path validated
- OpenBWAdapter execution path validated
- actual mineral-income state change validated
- PythonBridge still not involved

## Interpretation

Nova-Z now has two independent levels of deterministic Gather evidence:

1. Direct BWAPI control proves the game runtime can execute Gather and produce mineral income.
2. The common NovaBW protocol plus OpenBWAdapter proves the runtime-independent Observation/Action abstraction can represent and execute the same behavior.

The milestone does not rely on:

- a successful `gather()` return value alone
- worker order-state heuristics
- PythonBridge
- PPO
- reward shaping

## Conclusion

Nova-Z deterministic Gather and OpenBWAdapter Gather validation are complete.

Next implementation target:

1. Extend PythonBridge observation serialization with player resources and resource units.
2. Extend PythonBridge action parsing with `Gather` and `targetUnitId`.
3. Add a deterministic PythonBridge Gather integration test.
4. Verify the same end-to-end path:
   OpenBW observation → C++ bridge → Python → common Gather action → C++ adapter → actual mineral increase.
5. Only after that validation, introduce learning for worker gathering/economy control.

Project rule remains:

deterministic game-state validation first → protocol exposure second → learning integration last.
