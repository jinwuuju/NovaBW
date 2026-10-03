# NovaBW Architecture

## Goal

NovaBW separates the StarCraft runtime from the learning policy so the same agent can operate against multiple backends.

## Core data flow

Training:

OpenBW → Observation → Policy → Action → OpenBW

Future private-game runtime:

StarCraft: Remastered → Remastered Adapter → Observation → Policy → Action → Remastered Adapter → StarCraft: Remastered

The policy layer must not depend on backend-specific objects.

## Layers

### Runtime

Responsible for reading game state and executing game commands.

Backends:

- OpenBW
- future StarCraft: Remastered private-game adapter

### Protocol

Defines backend-agnostic observations and actions.

Current prototype includes unit position/state, economy, supply, and Move actions.

Future protocol should support:

- own/enemy/neutral units
- visibility
- orders
- production
- technology
- resources
- map information
- Gather
- Train
- Build
- Attack
- UseTech

### Agent

PyTorch policies used for inference.

A long-term hierarchical design is preferred:

strategic policy → tactical/economic intent → primitive game actions

### Training

NovaBW uses a Zerg-first asymmetric curriculum. The primary policy is trained for ZvT, ZvP, and ZvZ. Terran and Protoss are initially trained only as TvZ and PvZ opponent policies so compute and expert data remain focused on improving Zerg.

Training methods will include:

- supervised behavior cloning
- offline replay learning
- PPO
- self-play
- league training
- curriculum learning

### Expert knowledge

Human strategic knowledge is not treated as a hard-coded oracle.

It serves as:

- curriculum
- behavioral prior
- high-level supervision
- strategy labels
- scenario generation
- evaluation criteria

Self-play remains free to discover strategies that differ from conventional human play.

## Artifact policy

Git stores reproducible source code, schemas, manifests, evaluation code, and documentation.

Large mutable artifacts such as model checkpoints, MPQ data, replay archives, and generated trajectories should live outside ordinary Git history.
