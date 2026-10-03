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


## Follow-on milestone: Overlord supply sequence through common Action + OpenBWAdapter

Test: `NovaBW.ZergOverlordSupplyThroughAdapter`

The OpenBWAdapter Train action was expanded to allow `Zerg_Overlord` in addition to `Zerg_Drone`.

The regression test performs the entire sequence through common actions:

1. observe completed workers and resource units through the common Observation
2. issue common Gather actions through `OpenBWAdapter` for the starting workers
3. wait until at least 100 minerals are observed
4. issue common `Train(Zerg_Overlord)`
5. verify completed Overlord count increases
6. verify `supplyTotal` increases

Observed result:

- Gather accepted for 4 workers
- Overlord Train issued at frame 369
- minerals at Train: 106
- completed Overlords: 1 → 2
- BWAPI supplyTotal: 18 → 34
- state change observed at frame 1006
- `NovaBW.ZergOverlordSupplyThroughAdapter`: PASS
- runtime approximately 1.1 seconds

This is the first validated multi-action economy sequence entirely through the common NovaBW protocol and OpenBWAdapter:

common Gather × workers → resource accumulation → common Train(Overlord) → actual supply expansion.

Next step: move this short supply-management sequence into the Python policy layer and validate it end-to-end through PythonBridge.


## Follow-on milestone: Python-controlled Overlord supply sequence

Test: `NovaBW.PythonOverlordSupplyIntegration`

The common unit observation was extended with semantic production fields:

- `supplyProvider`
- `producesLarva`

These allow Python policy code to identify Zerg production structures and existing supply providers without hardcoding BWAPI unit type IDs.

A deterministic Python supply controller then performed the full sequence:

1. observe the starting Zerg economy
2. issue one Gather action to each of the 4 completed Drones
3. wait while minerals accumulate
4. detect minerals >= 100
5. identify a larva-producing structure from `producesLarva`
6. infer the Overlord unit type from the observed non-building supply provider
7. send `Train(Overlord)`
8. verify the resulting supply expansion

Observed Python-side behavior:

- frame 0: minerals 50, supply 8/18
- four Gather actions issued to four distinct workers
- minerals rose over time: 50 → 58 → 66 → ... → 106
- Overlord Train issued from Python at frame 384 with minerals 106
- minerals dropped to 6 after the production cost was applied
- supply remained 8/18 during morphing
- supply changed to 8/34 at frame 1024

Final integration result:

- `NovaBW.PythonOverlordSupplyIntegration`: PASS
- Gather actions received and executed
- Train action received and executed
- completed Overlord increase observed
- supply increase observed
- 1 test run, 1 test passed
- runtime approximately 1.1 seconds

This is Nova-Z's first validated Python-controlled multi-step economy objective:

Python policy → Gather multiple workers → wait on resource state → Train supply provider → verify actual supply expansion.

Next curriculum target: explicit Larva management.


## Follow-on milestone: Python-controlled Overlord supply management

Test: `NovaBW.PythonOverlordSupplyIntegration`

The common unit observation was extended with semantic production fields:

- `supplyProvider`
- `producesLarva`

The deterministic Python controller performed the whole supply objective:

1. identify four completed workers from the common Observation
2. send one common Gather action for each worker
3. observe mineral stockpile increasing over time
4. wait until minerals reached at least 100
5. identify a larva-producing structure from `producesLarva`
6. infer the Overlord unit type from the observed non-building supply provider
7. send `Train(Overlord)`
8. observe the production cost
9. verify actual supply expansion

Observed behavior:

- initial state: minerals 50, supply 8/18
- four worker Gather actions issued from Python
- mineral stockpile increased through repeated worker returns
- frame 384: minerals 106
- Python issued Train Overlord
- after the command: minerals 6
- frame 1024: supply changed from 8/18 to 8/34
- final test: `NovaBW.PythonOverlordSupplyIntegration` PASS
- 1 test run, 1 test passed
- runtime approximately 1.1 seconds

This is the first validated Python-controlled multi-step economy objective in Nova-Z:

Python policy → multiple Gather actions → resource-state waiting → Train supply provider → actual supply expansion.

Next curriculum target: explicit Larva management.
