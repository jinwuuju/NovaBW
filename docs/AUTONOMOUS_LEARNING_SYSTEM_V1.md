# NovaBW Autonomous Learning System v1

## Purpose

Define the first production learning system for NovaBW after the deterministic Nova-Z pre-learning baseline is frozen.

This document is the execution contract for:

- knowledge-driven TvZ/PvZ sparring
- fine-grained Zerg curriculum learning
- six-environment headless data generation
- shadow-mode calibration
- short-skill PPO
- checkpoint evaluation and promotion
- historical self-play
- league expansion

The system is intentionally Zerg-first.

Do not treat Terran and Protoss as equally developed full-game agents during v1. Their first responsibility is to expose Nova-Z to strategically diverse, reproducible TvZ/PvZ pressure.

## Hard prerequisites

Before model weights are updated, the local development repository must satisfy:

- `docs/PRE_LEARNING_BASELINE_V1.md`
- deterministic gameplay regression is green
- headless standard and pressure smoke tests complete naturally
- current deterministic Nova-Z policy is frozen and identifiable by commit/checkpoint
- telemetry can distinguish gameplay failure from runtime/teardown failure

Until those conditions are true:

- shadow games are allowed
- telemetry/calibration work is allowed
- knowledge compilation is allowed
- opponent/scenario generation is allowed
- PPO, self-play weight updates, and league learning are not allowed

## Core principle

Learning must be staged.

Do not ask one policy to learn all of StarCraft from sparse win/loss at once.

The v1 progression is:

knowledge
-> structured strategy cards
-> scenario/opponent generation
-> frozen-policy shadow runs
-> calibrated metrics
-> skill DAG curriculum
-> short-skill PPO
-> mixed-skill PPO
-> full-game policy integration
-> historical self-play
-> league training

Every arrow above has an evaluation gate.

A later stage may not hide a failure in an earlier stage.

## Replay availability

NovaBW currently assumes no professional replay corpus is available.

Replays are therefore optional future enrichment, not a dependency for Autonomous Learning System v1.

The current data hierarchy is:

1. user-provided expert strategy knowledge
2. deterministic Nova-Z reference behavior
3. synthetic OpenBW scenarios generated from strategy cards
4. self-generated trajectories from TvZ/PvZ/ZvZ sparring
5. reinforcement-learning experience
6. future replay data, if later acquired

Any existing strategy note saying "replay collection needed" should be interpreted as:

- confidence/source enrichment is desirable
- the card may need future timing calibration
- learning and sparring are not blocked

## System architecture

Data flow:

```text
Expert Strategy Markdown
        |
        v
Knowledge Compiler
        |
        v
Structured Strategy Cards
        |
        +--------------------+
        |                    |
        v                    v
Scenario Generator     Sparring Policy Generator
        |                    |
        +---------+----------+
                  |
                  v
            OpenBW Actors
          (6 stable workers)
                  |
                  v
          Compact Telemetry
                  |
          +-------+--------+
          |                |
          v                v
     Shadow Analysis   Experience Buffer
                           |
                           v
                    PyTorch/MPS Learner
                           |
                           v
                       Checkpoint
                           |
                           v
                  Immutable Evaluation
                           |
              +------------+------------+
              |                         |
           reject                    promote
                                        |
                                        v
                         Historical Checkpoint Pool
                                        |
                                        v
                                      League
```

The policy continues to consume only the common NovaBW Observation and produce only common NovaBW Actions.

No learning code may depend directly on OpenBW-specific objects.

## Knowledge compiler

The human-readable strategy knowledge base is a first-class training asset.

The compiler should transform each strategy entry into a structured record with fields such as:

- `strategy_id`
- `race`
- `matchup`
- `phase`
- `category`
- `goal`
- `preconditions`
- `steps`
- `branches`
- `tactical_rules`
- `failure_modes`
- `counter_cards`
- `map_tags`
- `source`
- `confidence`
- `timing_confidence`
- `parameter_ranges`
- `curriculum_nodes`
- `evaluation_metrics`

The compiler must preserve uncertainty.

Do not convert uncertain human knowledge into immutable game rules.

A strategy card is a prior, scenario template, opponent style, curriculum definition, and evaluation reference.

It is not the final oracle for optimal play.

## Terran sparring policy

Terran v1 covers TvZ only.

The current knowledge base contains a diverse TvZ strategy set. Each card should become a parameterized sparring family rather than one deterministic script.

Examples include:

- 1 Barracks expand
- Command Center first
- 2 Barracks Academy
- BBS / early Barracks bunker pressure
- +1 bio timing
- mutalisk turret defense
- SK Terran / bio + Science Vessel
- Valkyrie support
- drop harassment
- Irradiate usage
- anti-Dark-Swarm responses
- anti-Ultralisk responses
- mechanic TvZ
- 2 Starport Wraith
- third-CC macro
- anti-Lurker positioning
- Zergling run-by defense

Each family should expose controlled variation where the game engine and control surface allow it:

- build timing jitter
- production ratios
- defensive structure count
- defensive structure placement family
- attack timing
- attack route
- worker pull amount
- expansion greed
- scouting success/failure
- transition choice
- response threshold

The purpose is not to make Terran perfectly human.

The purpose is to generate strategically meaningful, diverse, reproducible pressure for Nova-Z.

## Protoss sparring policy

Protoss v1 covers PvZ only.

The same parameterized-family design applies.

Examples include:

- Forge expand
- Nexus first
- 2 Gate Zealot
- Corsair / Dark Templar
- Corsair / Reaver
- Hydralisk timing defense
- High Templar / Storm defense
- speed Zealot + Archon
- anti-Mutalisk
- anti-Lurker
- anti-Defiler
- third-Nexus macro
- Shuttle harassment
- Dark Templar harassment
- late-game Templar/Archon/Reaver composition

Variation should cover:

- Cannon density
- wall/gap configuration where practical
- Corsair count
- tech transition
- Templar energy readiness
- Reaver/Shuttle timing
- expansion timing
- attack timing
- defensive posture
- scouting information

Again, the opponent is a training instrument first.

## ZvZ opponent policy

ZvZ must not train only against the newest Nova-Z.

The opponent pool should eventually include:

- fixed strategy-card Zerg opponents
- frozen deterministic Nova-Z
- promoted Nova-Z checkpoints
- selected historical checkpoints
- exploiters/counter-strategy checkpoints later

Historical checkpoints are immutable once admitted to the league.

Sampling must retain older opponents so that newly learned behavior cannot silently forget previously solved strategies.

## Opponent sampling

During early curriculum, sampling is skill-driven rather than uniform.

A conceptual sampling mixture is:

- 50% target curriculum opponent/scenario
- 20% nearby variants of the target
- 15% regression opponents already solved
- 10% broad random matchup coverage
- 5% stress/adversarial variants

These values are starting defaults, not permanent constants.

The curriculum scheduler may change them using measured weakness, but evaluation opponents remain fixed.

When a scenario is unsolved, increase exposure gradually rather than making the entire training distribution one failure case.

When a scenario is mastered, reduce but do not remove it.

## Difficulty ladder

Each strategy family should expose difficulty levels.

Example for BBS defense:

Level 0:
- fixed spawn/map
- fixed bunker location
- reduced worker pull
- delayed Marine timing

Level 1:
- normal timing
- fixed bunker family
- fixed scouting information

Level 2:
- multiple bunker locations
- worker pull variation
- small timing jitter

Level 3:
- BBS vs fake pressure mixture
- incomplete scouting
- transition to macro if damage fails

Level 4:
- map/start variation
- multiple follow-up transitions
- pressure mixed with economic greed

Difficulty is increased only after the previous level is statistically stable.

## Fine-grained Skill DAG

Strategy cards must be decomposed below the "build order" level.

A skill node should represent a learnable decision or control competency with:

- explicit prerequisites
- observation requirements
- legal action family
- success metrics
- failure metrics
- scenario generator
- minimum evaluation sample
- promotion threshold

Initial DAG families:

### Economy

- worker selection
- mineral saturation
- gas saturation
- worker transfer
- expansion timing
- resource reservation
- larva allocation
- supply forecasting
- production recovery after losses

### Scouting and interpretation

- route selection
- scout survival
- identify enemy expansion
- identify early production count
- detect gas/tech
- classify opening
- maintain uncertainty when evidence is incomplete
- request/re-prioritize additional scouting

### Production and tech

- Drone vs army decision
- Overlord timing
- Hatchery timing
- Lair/Hive timing
- tech-building timing
- unit composition allocation
- upgrade/research timing
- transition after scouting evidence
- recovery after cancelled or destroyed tech

### Tactical control

- target selection
- focus fire
- retreat
- regroup
- surround
- choke handling
- harassment
- detector coordination
- spell usage
- air-unit preservation
- multi-pronged control

### Strategic integration

- opening choice
- opponent opening recognition
- safe greed
- all-in recognition
- transition choice
- economic vs military allocation
- timing-attack selection
- expansion denial
- recovery after damage
- map-aware adaptation
- long-horizon matchup plan

## Example decomposition: 3 Hatchery Mutalisk vs Terran

Do not represent this as one skill.

Possible DAG:

1. acquire scouting evidence
2. classify non-BBS opening
3. keep Drone production active
4. select third-Hatchery timing
5. reserve Lair resources
6. reserve Spire resources
7. preserve larvae before Spire completion
8. morph first Mutalisk group
9. choose harassment target from visible information
10. avoid high-cost turret dive
11. preserve damaged Mutalisks
12. detect +1 bio timing
13. decide Sunken/Zergling/Lurker defensive allocation
14. resume Drone production after harassment
15. choose continued Mutalisk vs ground transition
16. expand/rebuild economy

Each node can be evaluated separately before full sequence evaluation.

## Knowledge as prior, not command

Expert knowledge can influence learning through:

- scenario frequency
- high-level labels
- action priors
- auxiliary losses
- curriculum order
- negative/failure examples
- evaluation metrics

Do not force the learned policy to execute the expert action when the action is legal but empirically inferior.

The learning system must preserve the ability to discover non-human strategies.

## Shadow mode

Shadow mode uses the frozen deterministic Nova-Z policy.

No model weights change.

Its jobs are:

- benchmark throughput
- validate parallel stability
- calibrate telemetry
- discover failure taxonomy
- generate baseline distributions
- validate opponent/scenario diversity
- establish immutable evaluation sets

### Production parallelism

Use 6 concurrent OpenBW actors as the initial production setting because it is the current validated stable parallelism.

Environment flags:

- `OPENBW_GAME_SPEED=0`
- `OPENBW_ENABLE_UI=0`

Eight or more actors are experimental until they outperform 6 actors on completed-games-per-hour without increasing gameplay/runtime failure rate.

A concurrency increase is a benchmark promotion, not a guess.

### Shadow phases

Shadow-50:
- smoke of runner, telemetry, seed handling, and opponent selection

Shadow-100:
- failure taxonomy calibration

Shadow-500:
- first required statistical baseline

Shadow-2000:
- optional pre-PPO stress run when resources permit

Do not proceed from a shadow phase if telemetry cannot explain meaningful failures.

## Compact telemetry

Record per game at minimum:

- run id
- game id
- actor id
- random seed
- map id
- start positions
- matchup
- opponent strategy card
- opponent parameters/difficulty
- Nova-Z policy/checkpoint id
- terminal result
- natural completion flag
- frame count
- wall-clock duration
- minerals/gas over time at compact intervals
- supply used/total
- worker counts
- base counts
- tech milestones
- unit composition snapshots
- key strategy classifications
- invalid-action counts
- action-mask failures
- scheduler/reservation failures
- permanent supply stalls
- production deadlocks
- no-progress windows
- crash/teardown classification
- triggered failure-mode labels

Large raw traces may remain outside Git.

Git should contain schemas, summarizers, manifests, and compact experiment records.

## Failure taxonomy

At minimum classify:

- compile/API failure
- protocol serialization failure
- candidate/mask failure
- adapter action failure
- scheduler/reservation failure
- economy stall
- supply stall
- production deadlock
- scouting/visibility failure
- tactical control failure
- strategy-classification failure
- actual loss with valid gameplay
- timeout/no-progress
- OpenBW runtime failure
- known teardown failure after valid completion

Unknown failures are first-class.

Do not silently put an unknown failure into the closest known bucket.

## Metric calibration

Before PPO, verify that metrics correlate with actual desirable game behavior.

Examples:

Economy:
- mineral income
- gas income
- worker saturation
- idle-worker time
- larva waste
- supply-block duration

Production:
- resource float
- production idle time
- tech completion
- army value
- recovery time after production loss

Scouting:
- opening-classification accuracy
- time to first relevant evidence
- false-positive rate
- uncertainty calibration

Combat:
- damage dealt/taken
- unit-value trade
- worker damage
- army preservation
- retreat survival
- objective completion

Full game:
- win/loss
- natural completion
- game length
- base/resource advantage
- strategic diversity

No single shaped metric may replace win/loss evaluation.

## Evaluation architecture

Training and evaluation distributions must be separate.

### Immutable evaluation set

For each promoted skill/checkpoint, preserve:

- fixed seeds
- fixed maps
- fixed start locations where applicable
- fixed opponent card versions
- fixed opponent parameter sets
- fixed previous checkpoints

Do not train on the entire immutable evaluation set.

### Rolling evaluation set

Also maintain a rolling set drawn from new variants to detect overfitting.

### Regression set

Keep previously solved scenarios.

A new checkpoint must not gain one skill by catastrophically losing an earlier one.

## Mandatory intermediate gates

### Gate 0 — Pre-learning baseline

Pass `docs/PRE_LEARNING_BASELINE_V1.md`.

Failure:
- no weight learning allowed

### Gate 1 — Knowledge compilation

Requirements:
- all active strategy cards parse
- IDs are unique
- branch syntax is valid
- counter references resolve
- uncertainty/confidence preserved
- replay absence does not block compilation

Failure:
- fix compiler/knowledge record before opponent generation

### Gate 2 — Sparring determinism

Requirements:
- every active T/P opponent family can be instantiated from a seed
- identical seed/config reproduces the intended high-level style
- variation changes only declared parameters
- illegal actions are masked/rejected

Failure:
- do not use the opponent for learning

### Gate 3 — Parallel shadow stability

Minimum:
- 500 frozen-policy games at production concurrency
- natural-completion rate meets the defined target
- zero unexplained scheduler/production deadlocks
- runtime failures are classified
- throughput is recorded

Initial production target:
- 6 concurrent actors

Failure:
- stabilize runtime before PPO

### Gate 4 — Metric validity

Requirements:
- shaped metrics are directionally consistent with real game-state improvement
- failure labels match inspected examples
- win/loss remains separately measured
- no reward component can be trivially exploited in calibration scenarios

Failure:
- revise telemetry/reward, rerun shadow calibration

### Gate 5 — First short-skill PPO

Train exactly one narrow skill family.

Requirements:
- fixed training budget
- fixed baseline
- immutable evaluation
- multiple seeds
- improvement beyond baseline confidence threshold
- no major regression in prerequisite skills

Failure:
- reject checkpoint and diagnose learning/reward/action-space issue

### Gate 6 — Mixed-skill curriculum

Combine a small DAG neighborhood.

Requirements:
- retain performance on constituent skills
- improve integrated scenario completion
- no collapse into one repeated strategy
- action entropy/diversity remains plausible

Failure:
- reduce curriculum breadth or rebalance sampling

### Gate 7 — Full-game learned integration

Requirements:
- learned decisions can participate in complete games
- deterministic fallback/reference remains available for diagnosis
- full-game performance exceeds the frozen reference on predefined evaluation
- no new systemic stalls/deadlocks

Failure:
- isolate the learned module and return to the previous promoted checkpoint

### Gate 8 — Historical self-play

Requirements:
- checkpoint pool contains multiple promoted generations
- sampling includes old and recent policies
- exploitability against historical strategies does not increase sharply
- ZvZ strategy diversity is monitored

Failure:
- rebalance historical sampling / add regression opponents

### Gate 9 — TvZ/PvZ learned-opponent expansion

Only after scripted/parameterized sparring is stable.

Requirements:
- learned T/P opponents increase useful strategic diversity
- they do not replace fixed regression opponents
- T/P compute remains subordinate to Zerg-first objectives

### Gate 10 — League v1

Requirements:
- promoted Nova-Z checkpoints
- historical opponents
- fixed scripted knowledge opponents
- exploiters/counter-strategy policies where useful
- multi-map evaluation
- reproducible match manifests

## Promotion rules

A checkpoint is promoted only from evaluation evidence, never from training loss alone.

Every promotion record should contain:

- parent checkpoint
- training configuration
- training seeds/ranges
- curriculum nodes
- opponent mixture
- total environment steps
- wall-clock time
- evaluation suite version
- evaluation results
- regressions
- failure taxonomy counts
- decision: promote/reject
- rationale
- resulting checkpoint id

Rejected checkpoints may be kept outside Git for analysis, but must not silently become training parents.

## Stop conditions

Stop a learning run early when any of the following occurs:

- systemic invalid-action spike
- scheduler/reservation regression
- permanent production deadlock rate exceeds baseline tolerance
- reward increases while immutable evaluation decreases materially
- policy collapses to one action/strategy
- NaN/Inf or optimizer instability
- throughput drops enough to invalidate the experiment budget
- evaluation regression crosses a defined rollback threshold

Stopping is a successful safety mechanism, not an experiment failure.

## Checkpoint policy

Keep:

- frozen deterministic Nova-Z baseline
- every promoted learned checkpoint
- selected milestone checkpoints
- league anchors

Do not commit checkpoint binaries to normal Git history.

Git stores:

- checkpoint metadata
- hash
- parent relation
- training/evaluation manifest
- promotion decision

## Experiment cadence

For every learning milestone:

1. define hypothesis
2. define training budget
3. freeze evaluation set
4. run baseline evaluation
5. run training
6. run immutable evaluation
7. run rolling evaluation
8. run regression evaluation
9. inspect failure taxonomy
10. promote or reject
11. record result
12. only then change the next variable

Avoid changing reward, architecture, opponent distribution, and action space simultaneously.

Prefer one controlled change per experiment.

## Recommended first curriculum

After Gate 0 through Gate 4 pass:

### Curriculum A — macro reliability

1. Drone vs Overlord
2. supply forecasting
3. larva allocation
4. mineral/gas worker allocation
5. resource reservation
6. production recovery
7. expansion timing

### Curriculum B — scouting interpretation

1. preserve scout
2. observe enemy production/expansion
3. classify coarse opening
4. classify threat level
5. request additional scouting
6. transition based on evidence

### Curriculum C — matchup response

TvZ:
- early bunker pressure defense
- greedy Terran punishment
- bio timing defense
- Mutalisk harassment survival/value
- Lurker transition
- Vessel/Scourge interaction
- late-game Defiler response

PvZ:
- Forge-expand macro
- early Zealot defense
- Corsair/Overlord management
- Hydralisk timing
- Storm avoidance
- Shuttle/Reaver response
- late-game Hive composition

ZvZ:
- 9 Pool defense/offense
- 12 Hatchery greed
- Zergling count decisions
- Mutalisk/Scourge control
- historical checkpoint robustness

### Curriculum D — full-game integration

Only after A–C are individually stable.

## Opponent-strength feedback loop

Opponent difficulty should adapt from training performance, but evaluation difficulty must remain fixed.

A training opponent may increase difficulty when:

- recent success is high across multiple seeds
- failure taxonomy shows no hidden mechanical defect
- prerequisite skills remain stable

A training opponent may decrease difficulty when:

- success is near zero for a sustained window
- the policy receives little useful variation in outcomes
- failures occur before the target skill can be exercised

Do not lower immutable evaluation difficulty to make progress appear better.

## Strategic diversity checks

Monitor at least:

- opening distribution
- tech-path distribution
- expansion timing distribution
- unit-composition distribution
- attack timing distribution
- opponent-card coverage
- action entropy at relevant decision nodes

A stronger checkpoint that only works by collapsing into one brittle opening should not automatically replace a broader stable checkpoint.

## Human review checkpoints

Automated evaluation is primary, but periodic human review should occur at:

- end of Shadow-100
- end of Shadow-500
- first promoted short-skill PPO
- first mixed-skill promotion
- first full-game learned checkpoint
- first historical self-play promotion
- first league promotion

Human review should inspect representative successful, failed, and surprising games or compact traces.

The purpose is to validate that metrics still mean what the system thinks they mean.

## What the user needs to do

During the build-out phase:

- run local commands when local OpenBW access is required
- return exact logs/results when requested
- add or correct strategy knowledge when desired
- approve major objective changes

The user should not manually curate every training game.

The target operating model is:

start run
-> system generates games
-> system summarizes telemetry
-> system trains
-> system evaluates
-> system promotes or rejects
-> user reviews milestone report

## Immediate implementation order

After the pre-learning baseline is frozen:

1. define structured strategy-card schema
2. compile current knowledge Markdown
3. validate card/counter references
4. implement compact telemetry schema
5. implement deterministic failure taxonomy
6. implement six-actor shadow runner
7. implement T/P strategy-family parameterization
8. implement Skill DAG schema
9. implement immutable evaluation manifests
10. run Shadow-50
11. run Shadow-100 and inspect
12. run Shadow-500
13. calibrate metrics/reward
14. implement checkpoint metadata store
15. run first narrow PPO only after Gate 4 passes

## v1 success definition

Autonomous Learning System v1 is successful when:

- expert knowledge compiles into reproducible training artifacts
- TvZ/PvZ sparring is strategically diverse and parameterized
- six-actor shadow execution is stable
- telemetry and failure taxonomy explain outcomes
- at least one narrow Nova-Z skill improves by immutable evaluation
- the improvement survives regression evaluation
- a checkpoint is promoted with a reproducible manifest
- historical checkpoint infrastructure is ready for later self-play

This milestone does not require professional-level play.

It requires a correct, reproducible mechanism for becoming stronger.
