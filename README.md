# NovaBW

NovaBW is a Zerg-first StarCraft: Brood War AI research project focused on:

- OpenBW-based fast simulation
- C++ runtime adapters
- Python/PyTorch policies
- reinforcement learning and self-play
- imitation learning from expert replays
- structured strategic knowledge from professional players
- a future StarCraft: Remastered private-game runtime adapter

## Current status

The current prototype can:

- read OpenBW game state through a common observation protocol
- send observations from C++ to Python over a local socket
- run a PyTorch policy on Apple Silicon via MPS
- return actions to C++
- execute those actions in OpenBW
- run continuous control at accelerated OpenBW speed
- train a PPO probe-navigation task

The initial PPO curriculum has reached a strong learning signal on the 8-direction navigation task. This task is used as an integration test for the complete observation → policy → action → reward → update loop.

## Project principles

1. The policy should not depend on whether the backing runtime is OpenBW or StarCraft: Remastered.
2. Expert human knowledge is treated as curriculum and prior knowledge, not as immutable rules.
3. Training code, runtime code, strategic knowledge, and datasets remain separate.
4. Large binary artifacts such as checkpoints and replay corpora should not be committed directly to Git.
5. Training is Zerg-first: the primary agent learns ZvT, ZvP, and ZvZ; Terran and Protoss initially exist only as TvZ and PvZ training opponents.

## Planned structure

- `agent/` — neural policies and inference code
- `training/` — PPO, imitation learning, self-play, evaluation
- `runtime/` — OpenBW and future Remastered adapters
- `protocol/` — common observation/action schemas
- `strategy/` — expert strategic knowledge
- `datasets/` — dataset manifests and processing code
- `tools/` — conversion and analysis utilities
- `docs/` — architecture and research notes

## Training roadmap

1. Primitive continuous control
2. Navigation curriculum
3. Worker gathering and production actions
4. Build-order imitation learning
5. Zerg full-game policy across ZvT, ZvP, and ZvZ
6. TvZ/PvZ opponent policies and Zerg-focused self-play
7. League/checkpoint training
8. Multi-map generalization
9. Expand Terran and Protoss beyond their Zerg-facing matchups
10. Private-game Remastered integration

## Expert knowledge

Professional strategies, build orders, tactical rules, scouting heuristics, and matchup knowledge will first be collected as readable Markdown. They will then be transformed into structured machine-readable strategy records and, where possible, aligned with replay-derived trajectories for imitation learning.

See `strategy/templates/pro_strategy.md` for the authoring format and `docs/ZERG_FIRST_SCOPE.md` for the initial matchup scope.

## Repository policy

Model checkpoints, MPQ files, large replay archives, generated trajectories, and local virtual environments are excluded from Git. Reproducible code, schemas, manifests, configuration, and documentation belong in this repository.
