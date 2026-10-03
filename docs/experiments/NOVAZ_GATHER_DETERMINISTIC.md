# Nova-Z Deterministic Gather Milestone

## Purpose

This experiment validates the first Nova-Z economy control primitive across progressively wider layers of the system.

The success criterion is always an actual in-game state change, not merely successful command submission.

## Environment

- Backend: OpenBW / BWAPI
- Test harness: StardustDevEnvironment `BWTest`
- Player race: Zerg
- Opponent race: Terran
- Map: `maps/sscai/(4)Python.scx`
- Random seed: 12345
- Runtime: accelerated headless execution

## Milestone 1: direct BWAPI Gather validation

Test: `NovaBW.ZergGatherDeterministic`

The test:

1. Finds one completed `Zerg_Drone`.
2. Finds a nearby mineral field.
3. Records `self()->minerals()` and `self()->gatheredMinerals()`.
4. Issues one `Drone::gather(mineral)`.
5. Passes only if owned mineral count increases.

Observed result:

- Drone ID: 83
- Drone position: (3856, 1376)
- Mineral field ID: 74
- Mineral position: (4000, 1328)
- Gather issued: frame 0
- Minerals: 50 → 58
- Gathered minerals: 50 → 58
- Delta: +8
- First verified increase: frame 162
- Result: PASS

## Milestone 2: common protocol + OpenBWAdapter

Test: `NovaBW.ZergGatherThroughAdapter`

The common protocol was extended with:

- `Observation.resourceUnits`
- resource-unit ID, type, position and remaining resources
- mineral/geyser flags
- `ActionType::Gather`
- `Action.targetUnitId`

`OpenBWAdapter::observe()` exposes resource units.

`OpenBWAdapter::execute()` accepts a common Gather action, validates a completed worker and mineral-field target, and issues BWAPI Gather.

The test selects the Drone and mineral from the common Observation, constructs a common Gather Action, executes through `OpenBWAdapter`, and passes only after mineral stockpile increases.

Result:

- resource observation path: PASS
- common Gather action path: PASS
- OpenBWAdapter execution: PASS
- actual mineral-income state change: PASS

## Milestone 3: PythonBridge end-to-end Gather

Test: `NovaBW.PythonGatherIntegration`

`PythonBridge` was extended to serialize `resourceUnits` and parse:

- `actionType = "Gather"`
- `unitId`
- `targetUnitId`

A dedicated deterministic Python server, `python/gather_test_server.py`, receives the common Observation, selects a completed worker and nearby mineral field, and sends exactly one Gather action. Later observations return None so the original Gather command is not overwritten.

Observed Python-side behavior included:

- observation received at frame 0
- minerals = 50
- own units = 9
- resource units serialized successfully
- Drone and mineral selected in Python
- `Gather(unitId, targetUnitId)` sent back to C++

The C++ integration test completed successfully:

- `NovaBW.PythonGatherIntegration`: PASS
- 1 test run
- 1 test passed
- runtime approximately 1.1 seconds

This validates the complete path:

OpenBW
→ common Observation
→ PythonBridge
→ Python policy layer
→ common Gather Action
→ PythonBridge
→ OpenBWAdapter
→ BWAPI
→ actual mineral collection

## Interpretation

Nova-Z now has deterministic Gather evidence at three layers:

1. direct BWAPI control
2. common protocol + OpenBWAdapter
3. full C++ ↔ Python policy loop

The milestone does not rely on PPO, reward shaping, worker-order heuristics, or command-return values alone.

## Conclusion

Nova-Z Gather is complete as a deterministic end-to-end control primitive.

Next curriculum target:

Drone production.

Implementation order:

1. verify exact BWAPI/OpenBW Zerg production API
2. deterministic C++ production test
3. verify an actual new Drone appears
4. add common Train/Morph action representation
5. validate through OpenBWAdapter
6. expose through PythonBridge
7. only then connect to a learning policy


## Follow-on milestone: deterministic Drone production

Test: `NovaBW.ZergDroneProductionDeterministic`

After Gather was validated end-to-end, the next economy primitive was tested directly through BWAPI before protocol exposure.

Observed result:

- completed Hatchery selected: ID 69
- starting completed Drone count: 4
- starting minerals: 50
- `Hatchery::train(Zerg_Drone)` accepted at frame 0
- completed Drone count: 4 → 5
- minerals: 50 → 0
- production completion observed at frame 337
- `NovaBW.ZergDroneProductionDeterministic`: PASS
- runtime approximately 0.9 seconds

This establishes the deterministic runtime baseline for Drone production. The next step is to represent production through the common Action protocol and validate the same state transition through `OpenBWAdapter`.


## Follow-on milestone: Drone production through common Action + OpenBWAdapter

Test: `NovaBW.ZergDroneProductionThroughAdapter`

The common Action protocol was extended with:

- `ActionType::Train`
- `Action.unitTypeId`

The initial adapter implementation deliberately constrains Train to completed larva-producing Zerg structures requesting `Zerg_Drone`.

Observed result:

- Hatchery ID: 71
- starting completed Drone count: 4
- starting minerals: 50
- common Train action accepted at frame 0
- completed Drone count: 4 → 5
- minerals: 50 → 0
- production completion observed at frame 337
- `NovaBW.ZergDroneProductionThroughAdapter`: PASS
- runtime approximately 0.9 seconds

This validates the path:

common Observation → common Train Action → OpenBWAdapter → BWAPI → actual completed Drone increase.

Next step: expose `Train` and `unitTypeId` through PythonBridge and validate the same production state change end-to-end from Python.


## Follow-on milestone: PythonBridge end-to-end Drone production

Test: `NovaBW.PythonDroneProductionIntegration`

`PythonBridge` was extended to parse:

- `actionType = "Train"`
- `unitTypeId`

A dedicated deterministic Python server, `python/train_drone_test_server.py`, receives the common Observation, derives the Drone type ID from observed units, selects the starting Hatchery as producer, and sends one Train action.

Observed Python-side behavior:

- frame 0: minerals = 50, own units = 9
- Train sent from Python with producer ID and Drone unit type ID
- frame 8: minerals = 0, confirming the production cost was applied
- frame 336: own units = 10, confirming a new unit appeared

Final integration result:

- `NovaBW.PythonDroneProductionIntegration`: PASS
- 1 test run
- 1 test passed
- runtime approximately 1.0 second

This validates the complete production path:

OpenBW → common Observation → PythonBridge → Python → common Train Action → PythonBridge → OpenBWAdapter → BWAPI → actual completed Drone increase.

At this point Nova-Z has two end-to-end Python-controlled economy primitives:

1. Gather minerals
2. Produce a Drone

Next curriculum target: Overlord production and supply management, validated by an actual increase in completed Overlord count and total supply.


## Follow-on milestone: deterministic Overlord supply expansion

Test: `NovaBW.ZergOverlordSupplyDeterministic`

This test extends the economy curriculum beyond a single isolated production action. It performs a short deterministic sequence:

1. issue mineral gathering to the starting Drones
2. wait until at least 100 minerals are available
3. issue Overlord production
4. verify a completed Overlord appears
5. verify total supply increases

Observed result:

- gathering issued to 4 Drones
- Overlord Train issued at frame 359
- minerals at Train: 106
- starting completed Overlords: 1
- starting BWAPI supplyTotal: 18
- completed Overlords: 1 → 2
- BWAPI supplyTotal: 18 → 34
- completion/state change observed at frame 996
- `NovaBW.ZergOverlordSupplyDeterministic`: PASS
- runtime approximately 1.1 seconds

BWAPI represents supply in half-supply units, so the observed 18 → 34 corresponds to the in-game displayed supply capacity increasing from 9 → 17. The Overlord definition reports 16 BWAPI supply units provided, matching the observed delta.

This is the first Nova-Z deterministic multi-step economy sequence:

Gather → accumulate resources → produce supply provider → verify actual supply expansion.

Next step: permit `Zerg_Overlord` through the common Train action and validate the same sequence through `OpenBWAdapter`.
