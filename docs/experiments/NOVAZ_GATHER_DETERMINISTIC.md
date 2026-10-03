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


## Follow-on milestone: explicit Larva morph control

Test: `NovaBW.ZergLarvaMorphDeterministic`

This milestone removes the previous dependency on Hatchery-level automatic Larva selection.

The deterministic test:

1. finds the completed starting Hatchery
2. obtains its current Larva set
3. selects one specific Larva by unit ID
4. records completed Drone count and minerals
5. calls `larva->morph(Zerg_Drone)`
6. passes only after completed Drone count actually increases

Observed result:

- Hatchery ID: 52
- selected Larva ID: 112
- initial Larva count: 3
- starting completed Drones: 4
- starting minerals: 50
- Morph accepted at frame 0
- completed Drones: 4 → 5
- minerals: 50 → 0
- completion observed at frame 337
- `NovaBW.ZergLarvaMorphDeterministic`: PASS
- runtime approximately 0.9 seconds

This proves Nova-Z can explicitly control an individual Larva rather than delegating Larva selection to Hatchery-level Train.

Next step: add explicit Larva observation and a common `Morph` action, then validate the same state transition through `OpenBWAdapter`.


## Follow-on milestone: explicit Larva morph through common Observation + OpenBWAdapter

Test: `NovaBW.ZergLarvaMorphThroughAdapter`

The common unit observation now exposes:

- `larva`
- `parentUnitId`

The common action protocol now includes:

- `ActionType::Morph`
- `unitId` as the specific Larva actor
- `unitTypeId` as the requested morph target

The adapter test selects a Larva entirely from the common Observation, verifies its parent production structure, issues a common Morph action, and passes only after the completed Drone count increases.

Observed result:

- selected Larva ID: 116
- parent unit ID: 90
- initial Larva count: 3
- starting completed Drones: 4
- starting minerals: 50
- common Morph accepted at frame 0
- completed Drones: 4 → 5
- minerals: 50 → 0
- completion observed at frame 337
- `NovaBW.ZergLarvaMorphThroughAdapter`: PASS
- runtime approximately 0.9 seconds

This validates explicit Larva control through the runtime-independent NovaBW abstraction:

common Observation → specific Larva ID → common Morph(Drone) → OpenBWAdapter → BWAPI → actual Drone completion.

Next bundled target: expose Larva/Morph through PythonBridge and extend the same production path to Zergling.


## Follow-on milestone: Python-controlled explicit Larva morph

Test: `NovaBW.PythonLarvaMorphIntegration`

`PythonBridge` was extended to serialize explicit Larva semantics:

- `larva`
- `parentUnitId`

and to parse the common `Morph` action.

A deterministic Python controller selected a specific observed Larva, reused the observed Drone type ID as the requested morph target, and returned a common `Morph` action.

Observed result:

- starting completed Drones: 4
- starting Larvae: 3
- starting minerals: 50
- selected Larva ID: 78
- parent unit ID: 64
- Drone type ID: 41
- Morph received from Python at frame 0
- Morph executed through `OpenBWAdapter`
- completed Drones: 4 → 5
- minerals: 50 → 0
- completion observed at frame 337
- `NovaBW.PythonLarvaMorphIntegration`: PASS
- runtime approximately 0.9 seconds

This validates the complete explicit Zerg production path:

OpenBW → common Observation with Larva identity/parent → Python policy selects a specific Larva → common Morph action → PythonBridge → OpenBWAdapter → BWAPI → actual completed Drone increase.

Next bundled target: add building construction for Spawning Pool and then produce Zerglings through the same explicit Larva/Morph path.


## Follow-on milestone: PythonBridge explicit Larva morph

Test: `NovaBW.PythonLarvaMorphIntegration`

PythonBridge now serializes Larva identity and parent production structure and parses the common `Morph` action.

Observed result:

- starting completed Drones: 4
- starting Larvae: 3
- starting minerals: 50
- selected Larva ID: 78
- parent unit ID: 64
- Python requested `Morph(Drone)` at frame 0
- Morph executed through OpenBWAdapter
- completed Drones: 4 → 5
- minerals: 50 → 0
- completion observed at frame 337
- `NovaBW.PythonLarvaMorphIntegration`: PASS
- runtime approximately 0.9 seconds

This completes explicit Larva selection and Morph control end-to-end through the Python policy layer.

Next scenario target: gather resources → construct Spawning Pool → verify completion → explicitly morph a Larva into Zerglings.


## Follow-on milestone: deterministic Spawning Pool to Zergling scenario

Test: `NovaBW.ZergPoolToZerglingDeterministic`

This is Nova-Z's first deterministic tech-production scenario spanning resource collection, building construction, tech completion, explicit Larva selection, and combat-unit production.

Sequence:

1. send the starting 4 Drones to minerals
2. accumulate enough minerals for both Spawning Pool and Zergling
3. find a valid build location
4. command one Drone to construct a Spawning Pool
5. verify the Spawning Pool appears
6. wait for the Spawning Pool to complete
7. explicitly select one Larva
8. morph the Larva into Zerglings
9. pass only after completed Zergling count increases

Observed result:

- Gather accepted for 4 Drones
- Spawning Pool build issued at frame 1137
- builder unit ID: 46
- build tile: (110, 42)
- minerals at build: 250
- build command accepted
- Spawning Pool appeared at frame 1267
- Spawning Pool completed at frame 2475
- Larva ID 131 selected
- Zergling morph accepted at frame 2475
- completed Zerglings: 0 → 2
- final state change observed at frame 2932
- `NovaBW.ZergPoolToZerglingDeterministic`: PASS
- runtime approximately 1.5 seconds

This validates the first full Nova-Z tech sequence:

Gather → accumulate resources → construct prerequisite tech building → wait for completion → explicitly morph Larva → produce combat units.

Next bundled target: add a common `Build` action, permit `Morph(Zergling)`, validate the same scenario through `OpenBWAdapter`, then expose it through PythonBridge.


## Follow-on milestone: Pool-to-Zergling through common actions + OpenBWAdapter

Test: `NovaBW.ZergPoolToZerglingThroughAdapter`

The common action protocol now includes:

- `ActionType::Build`
- `targetTileX`
- `targetTileY`

The explicit Larva Morph path was expanded to allow `Zerg_Zergling`.

The complete tech scenario was then executed through common actions:

1. common Gather for the 4 starting Drones
2. wait for sufficient minerals
3. common Build(Spawning Pool)
4. verify the Pool appears
5. wait for Pool completion
6. common Morph(Zergling) on a specific observed Larva
7. verify completed Zergling count increases

Observed result:

- Gather accepted for 4 workers
- common Build issued at frame 1238
- builder unit ID: 106
- build tile: (116, 46)
- minerals at build: 250
- Build accepted
- Pool appeared at frame 1317
- Pool completed at frame 2525
- Larva ID 39 selected
- common Morph(Zergling) accepted at frame 2525
- completed Zerglings: 0 → 2
- final state change observed at frame 2982
- `NovaBW.ZergPoolToZerglingThroughAdapter`: PASS
- runtime approximately 1.4 seconds

This validates the first full Zerg tech sequence entirely through the NovaBW common action layer and OpenBWAdapter:

Gather → Build prerequisite tech → wait for completion → explicit Larva Morph → combat-unit production.

Next target: expose Build through PythonBridge. Before giving Python spatial Build control, add runtime-independent build-location candidates to the common Observation so the Python policy does not depend on BWAPI/OpenBW-specific build-location APIs.


## Follow-on milestone: Python-controlled Pool-to-Zergling tech path

Test: `NovaBW.PythonPoolToZerglingIntegration`

The common observation/action interface was extended with:

- build candidates for currently valid construction targets
- morph options that act as an initial action mask
- PythonBridge parsing for `Build`
- `targetTileX` / `targetTileY`

The Python controller then completed the entire first tech-production objective:

1. issue Gather to four starting workers
2. accumulate minerals
3. select a valid common Build candidate
4. issue Build(Spawning Pool)
5. wait for the Pool to appear and complete
6. observe a valid combat morph option only after prerequisites are satisfied
7. issue Morph(Zergling) on a specific Larva
8. verify completed Zergling count increases

Final integration result:

- Gather executed for 4 workers
- Build action received and executed
- Spawning Pool observed and completed
- Morph action received and executed
- completed Zerglings: 0 → 2
- final PASS observed near frame 5994
- `NovaBW.PythonPoolToZerglingIntegration`: PASS
- 1 test run, 1 test passed
- runtime approximately 9.5 seconds

This validates the first Python-controlled Nova-Z tech path:

Python policy → resource collection → prerequisite construction → prerequisite waiting → explicit Larva morph → combat-unit production.

Note: the PASS log was emitted on several final frames because the test printed success whenever the already-satisfied condition was re-observed. This is harmless test-log duplication and should be guarded to print only once in a future cleanup.

Next curriculum target: enemy observation and Attack, with success defined by an actual enemy hit-point reduction or unit death.


## Follow-on milestone: scouting and Attack through common Observation + OpenBWAdapter

Test: `NovaBW.ZergScoutAndAttackThroughAdapter`

The common Observation was extended with visible enemy units, and the common action protocol was extended with `Attack`.

The test uses one starting Drone as a scout, visits the map's possible start locations through common Move actions, waits until an enemy becomes visible through the common `enemyUnits` observation, then issues a common Attack action and passes only after actual enemy health decreases.

Observed result:

- scout unit ID: 111
- possible scout targets: 3
- 13 Move actions accepted
- visible enemy first selected at frame 3054
- target unit ID: 113
- target starting health: 1500
- Attack accepted
- actual enemy health: 1500 → 1496
- damage observed at frame 3130
- `NovaBW.ZergScoutAndAttackThroughAdapter`: PASS
- runtime approximately 6.1 seconds

This validates the first combat state transition through the runtime-independent common protocol:

common Move → fog-respecting visible enemy observation → common Attack → OpenBWAdapter → actual enemy damage.

Next bundled target: Python-controlled combat using produced Zerglings: Gather → Build Spawning Pool → Morph Zerglings → scout/search → Attack visible enemy → verify actual damage.
