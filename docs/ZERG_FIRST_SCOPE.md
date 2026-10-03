# Zerg-First Training Scope

## Primary race

NovaBW is developed as a Zerg-first agent.

The first complete full-game agent is Zerg. Training priority is therefore:

- ZvT
- ZvP
- ZvZ

NovaBW does not initially attempt to build complete Terran and Protoss agents.

## Asymmetric opponent curriculum

Terran and Protoss are initially trained only where they improve the Zerg agent.

| Agent race | Initial matchup coverage | Role |
|---|---|---|
| Zerg | ZvT, ZvP, ZvZ | Primary NovaBW agent |
| Terran | TvZ only | Zerg training opponent / sparring policy |
| Protoss | PvZ only | Zerg training opponent / sparring policy |

Terran-vs-Protoss, Terran-vs-Terran, and Protoss-vs-Protoss are deferred until the Zerg-first system is mature.

## Training intent

This structure concentrates compute, replay curation, strategic knowledge, evaluation, and self-play on matchups that directly improve the primary Zerg agent.

Opponent policies must still be diverse. TvZ and PvZ should contain multiple strategic styles rather than a single fixed build-order bot.

## Expert data priority

1. Zerg strategic knowledge across ZvT, ZvP, and ZvZ
2. Zerg professional replay trajectories
3. Terran knowledge specifically for TvZ
4. Protoss knowledge specifically for PvZ
5. Opponent replay diversity for TvZ and PvZ
6. Other matchups later

## Agent design implication

Race identity should be explicit in observations and training configuration, while reusable lower-level representations may be shared.

A likely long-term structure is:

- shared game-state encoder
- race-conditioned policy components
- Zerg primary strategic policy
- Terran TvZ opponent policy
- Protoss PvZ opponent policy
- matchup-specific strategy heads where useful

The architecture must not assume equal or simultaneous training across all three races.

## Expansion criteria

Expand Terran and Protoss beyond their Zerg-facing matchups only after the Zerg agent has:

- stable economy and production control
- reliable ZvT, ZvP, and ZvZ full-game play
- multi-map generalization
- stable self-play / league training
- expert replay ingestion
- robust matchup evaluation

At that point, TvT, TvP, PvT, and PvP can be added without changing the core runtime/protocol architecture.
