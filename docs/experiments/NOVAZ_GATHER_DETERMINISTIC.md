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

## Deterministic test behavior

The test module:

1. Finds one existing, completed `Zerg_Drone`.
2. Finds a nearby mineral field.
3. Records `self()->minerals()` and `self()->gatheredMinerals()`.
4. Issues exactly one `Drone::gather(mineral)` command.
5. Waits for an actual mineral return.
6. Passes only if owned mineral count increases.
7. Also verifies cumulative gathered minerals increased.

Existing Probe/Python bridge tests remain separate from this test.

## Observed result

Relevant runtime output:

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

GoogleTest result:

- `NovaBW.ZergGatherDeterministic`: PASS
- 1 test run
- 1 test passed
- Runtime: approximately 1.1 seconds

## Interpretation

This proves that the first Nova-Z economy action can cause the intended game-state transition in OpenBW.

The milestone does not rely on:

- a successful `gather()` return value alone
- worker order-state heuristics
- PythonBridge
- PPO
- reward shaping

The evidence is the actual increase in player mineral stockpile from 50 to 58, together with the increase in cumulative gathered minerals.

## Conclusion

Nova-Z deterministic Gather validation is complete.

Next implementation target:

1. Add player resource observations such as minerals and gas to the common Observation.
2. Add neutral/resource unit observations, including mineral fields.
3. Add `ActionType::Gather` to the common Action protocol.
4. Implement and validate Gather execution in `OpenBWAdapter`.
5. Only after deterministic C++ validation, expose the new observation/action fields through PythonBridge.

This preserves the project rule:

deterministic game-state validation first → protocol exposure second → learning integration last.
