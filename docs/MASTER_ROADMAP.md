# NovaBW Master Roadmap

## Objective

NovaBW is a Zerg-first StarCraft: Brood War AI project.

Primary progression target:

1. complete a full game reliably
2. reach strong amateur level
3. reach professional level
4. pursue superhuman play through replay learning, reinforcement learning, self-play, and league training

The first complete race is Zerg. Terran and Protoss are initially developed only as diverse TvZ/PvZ training opponents.

## Architecture

Training path:

OpenBW -> common Observation -> NovaBW Policy -> common Action -> OpenBW

Future private-game path:

StarCraft: Remastered -> Remastered Adapter -> common Observation -> same NovaBW Policy -> common Action -> Remastered Adapter -> StarCraft: Remastered

The policy must remain backend-independent.

## Current verified state

The following have been experimentally verified through actual game-state changes:

- OpenBW runtime on Apple Silicon
- common Observation / Action protocol
- OpenBW C++ adapter
- C++ <-> Python TCP bridge
- PyTorch inference on MPS
- continuous Python neural control
- accelerated headless OpenBW execution
- PPO navigation infrastructure
- resource observation
- Gather through direct BWAPI, adapter, and Python
- Drone production
- Overlord production and supply increase
- explicit Larva observation and Morph
- Spawning Pool construction
- Zergling production
- build candidates / morph action masks
- visible enemy observation respecting fog of war
- scouting through common Move
- Attack through common protocol
- verified enemy HP reduction
- autonomous economy -> tech -> production -> scouting -> combat loop
- fixed-map 10-seed robustness: 10/10
- six-map / all-start-location robustness: 19/19
- first full-game victory: won=1 against a passive Terran opponent

Current reference policy:

deterministic Python Nova-Z autonomous baseline.

This is a regression/reference policy, not the final learned policy.

## Current project phase

The project has completed the first end-to-end vertical slice of StarCraft gameplay.

The current Zerg path is:

Drone economy
-> Overlord supply
-> Spawning Pool
-> Zergling production
-> scouting
-> visible enemy acquisition
-> combat
-> game victory

This proves architecture and lifecycle completeness.

It does NOT mean Zerg gameplay is complete.

The next major phase is broad Zerg capability coverage followed by competitive full-game learning.

## Zerg capability coverage plan

Every relevant melee Zerg capability should eventually be observable, executable through the common protocol, validated deterministically, represented with legality masks/candidates, and usable by the learned policy.

### Economy and macro

Required capabilities:

- mineral gathering
- gas gathering
- ReturnCargo where useful
- worker saturation
- Drone production
- Overlord production
- supply forecasting
- expansion Hatcheries
- Extractors
- multiple-base economy
- worker transfer
- Larva allocation
- resource reservation
- production queues / morph state
- rebuilding after worker or structure losses

Current status:

- mineral gathering: verified
- Drone production: verified
- Overlord / supply: verified
- Larva control: verified
- gas / expansion / multi-base macro: not yet implemented

### Core Zerg structures

Required structure progression:

- Hatchery
- Lair
- Hive
- Extractor
- Spawning Pool
- Evolution Chamber
- Hydralisk Den
- Spire
- Greater Spire
- Queen's Nest
- Ultralisk Cavern
- Defiler Mound
- Creep Colony
- Sunken Colony
- Spore Colony
- Nydus Canal

Current status:

- starting Hatchery observation: available
- Spawning Pool build: verified
- remaining structure/tech progression: pending

### Ground units

Required unit control:

- Drone
- Zergling
- Hydralisk
- Lurker
- Ultralisk
- Defiler
- Broodling where created by tech

Current status:

- Drone: verified
- Zergling: verified
- Hydralisk / Lurker / Ultralisk / Defiler: pending

### Air units

Required unit control:

- Overlord
- Mutalisk
- Scourge
- Guardian
- Devourer
- Queen

Current status:

- Overlord production: verified
- air combat / air morph chains: pending

### Special / conditional units

Required support where relevant:

- Infested Terran
- Infested Command Center interaction if used in melee scenarios
- Eggs / Cocoons / morph intermediates as observable production states

These are lower priority than standard matchup-critical units but should not be architecturally impossible.

### Unit commands

Common action families should support, with validation/masks:

- None
- Move
- Gather
- ReturnCargo
- Train / Morph
- Build
- Attack unit
- Attack-move / spatial Attack
- Stop
- HoldPosition
- Patrol if useful
- Burrow / Unburrow
- Load / Unload
- Research
- Upgrade
- UseTech on unit
- UseTech on position

Current verified commands:

- None
- Move
- Gather
- Train
- Morph
- Build
- Attack unit

Pending:

- gas-specific economy validation
- ReturnCargo
- Attack-move
- Stop / Hold
- Burrow
- transport
- Research / Upgrade
- spell/tech usage

### Zerg upgrades and technologies

The policy must eventually support the matchup-relevant upgrade/tech system, including:

- melee attack
- missile attack
- flyer attack
- ground carapace
- flyer carapace
- Zergling speed / attack-speed upgrades
- Hydralisk speed / range
- Lurker Aspect
- Overlord speed / transport / sight
- Ultralisk armor / speed
- Burrowing
- Defiler technologies such as Consume and Plague
- Queen technologies such as Ensnare, Parasite, and Spawn Broodlings

Implementation rule:

Research and Upgrade must use common actions and legality masks rather than hard-coded build scripts.

### Tactical capabilities

Required progression:

- target selection
- focus fire
- retreat
- regroup
- concave / surround
- choke handling
- worker defense
- base defense
- harassment
- multi-pronged attack
- air-vs-ground targeting
- detector / cloaked-unit interaction
- Lurker positioning
- spell casting
- transport / drop behavior
- Nydus usage

### Strategic capabilities

Required progression:

- opening selection
- build-order execution
- scouting interpretation
- opponent build recognition
- conditional transitions
- expansion timing
- economic vs military allocation
- tech switching
- all-in recognition
- recovery after damage
- map-specific adaptation
- matchup-specific strategy
- opponent modeling
- long-horizon planning

## Development phases

### Phase 0 - infrastructure validation

Status: complete.

Validated OpenBW, protocol separation, Python bridge, PyTorch/MPS, headless speed, and PPO infrastructure.

### Phase 1 - end-to-end Zerg vertical slice

Status: complete.

Validated economy -> supply -> Pool -> Zergling -> scouting -> combat -> actual victory.

Evidence:

- fixed-map multi-seed: 10/10
- multi-map/all-start locations: 19/19
- first full-game passive-opponent victory: verified

### Phase 2 - complete Zerg control surface

Status: next.

Goal:

Make all important Zerg units, structures, upgrades, technologies, and command families available through the common protocol and validate them in deterministic scenarios.

Priority order:

1. gas economy and Extractor
2. Hatchery expansion / multi-base economy
3. Lair / Hive tech progression
4. Hydralisk / Hydralisk Den
5. research and upgrades
6. Lurker
7. Mutalisk / Scourge / Spire
8. Queen
9. Ultralisk
10. Defiler
11. Guardian / Devourer / Greater Spire
12. static defense
13. Burrow
14. transport / Nydus / advanced special capabilities

Not every item requires a permanently separate micro-test. Related abilities should now be bundled into larger deterministic scenarios while retaining explicit evidence of actual game-state change.

### Phase 3 - Full Game v1 rule baseline

Goal:

A complete deterministic Zerg controller able to finish games using the broader Zerg tech tree.

Capabilities:

- continuous economy
- gas
- expansions
- production recovery
- multiple unit compositions
- upgrades
- tech transitions
- defense
- repeated attacks
- win/loss handling

The rule baseline is a regression oracle and curriculum generator, not the intended final intelligence.

### Phase 4 - active opponent ladder

Goal:

Measure actual playing strength.

Progression:

- passive opponent
- trivial scripted opponent
- weak active opponent
- diverse scripted opponents
- existing Brood War bots where integration is practical
- matchup-specific TvZ / PvZ / ZvZ sparring policies

Evaluation must measure actual wins, not only damage or training loss.

### Phase 5 - expert-data pipeline

Goal:

Turn professional human knowledge into training data.

Pipeline:

human-readable strategy Markdown
-> structured strategy records / JSONL
-> replay-aligned trajectories
-> state/action examples
-> behavior cloning / supervised learning

Metadata should preserve player, matchup, map, year/era, patch/version, source, and confidence.

### Phase 6 - learned policy integration

Goal:

Replace rule decisions incrementally while keeping the verified runtime and action masks.

Likely progression:

- action-selection imitation
- economy decisions
- production decisions
- build/tech transitions
- scouting decisions
- tactical combat decisions
- strategic policy

A hierarchical/factorized policy is preferred:

command type
-> actor
-> target unit / spatial target
-> unit type / building / tech

### Phase 7 - reinforcement learning

Methods:

- PPO
- curriculum learning
- scenario training
- reward shaping only where needed
- sparse game-outcome evaluation
- offline-to-online transitions

Do not begin with unrestricted full-game PPO from scratch.

### Phase 8 - self-play and league

Goal:

Move from competent play to strong play.

Use:

- historical Nova-Z checkpoints
- multiple opponent generations
- diverse TvZ / PvZ policies
- exploiters / counter-strategy policies
- map diversity
- matchup diversity
- regression opponents

Do not train only against the latest copy of the same policy.

### Phase 9 - strong amateur

Evidence should include:

- reliable ZvT / ZvP / ZvZ complete games
- robust multi-map play
- multiple viable openings
- scouting-driven adaptation
- stable macro under pressure
- competent tactics
- high win rate against strong amateur-level reference opponents

### Phase 10 - professional level

Requirements include:

- professional replay ingestion
- matchup specialization
- broad strategic diversity
- strong tactical control
- robust opponent modeling
- long-running historical league
- multi-map / multi-style evaluation
- sustained performance against professional-caliber reference play

### Phase 11 - superhuman research

Goal:

Use expert knowledge as a starting prior rather than a ceiling.

Focus:

- large-scale diverse self-play
- strategy discovery
- non-human but legal play styles
- exploitation resistance
- league diversity
- continual evaluation against historical and external opponents
- discovery of novel openings, transitions, and tactical patterns

## Evaluation ladder

Every major release should be evaluated across:

- deterministic regression scenarios
- multiple random seeds
- all start locations
- multiple maps
- ZvT / ZvP / ZvZ
- fixed historical opponents
- current league opponents
- historical Nova-Z checkpoints
- expert replay-derived scenarios
- full-game win/loss

Training loss alone is never an acceptance criterion.

## Current exact position

NovaBW is currently at the boundary between Phase 1 and Phase 2.

Phase 1 is complete:

end-to-end Zerg gameplay from economy to actual victory has been proven.

Phase 2 has not yet been completed:

the full Zerg control surface — gas, expansions, Lair/Hive, all major units, upgrades, spellcasters, air tech, static defense, transport, and advanced commands — still needs systematic coverage.

The immediate engineering target should therefore be:

complete the Zerg control surface while preserving the stable Full Game v0 baseline.

After that, Full Game v1 should use the larger Zerg toolkit before serious competitive RL/self-play begins.
