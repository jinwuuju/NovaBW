# Nova-Z Overnight Learning Run v1 — 7 Hours

## Objective

Run the first long unattended Nova-Z learning session for up to seven wall-clock hours while preserving the Autonomous Learning System v1 safety and evaluation gates.

## Preconditions

- Core regression must pass from the exact local working tree used for the run.
- The learning entry point and telemetry/trainer modules must exist.
- OpenBW runs headless with `OPENBW_GAME_SPEED=0` and `OPENBW_ENABLE_UI=0`.
- The run records the current Git HEAD, dirty-tree status/diff, learning configuration, CLI help, and logs.
- The Mac must remain powered and awake; unattended execution must not depend on the ChatGPT session remaining open.

## Runtime policy

Target wall-clock duration: 7 hours.

Initial production parallelism: 6 OpenBW actors unless the current learning configuration explicitly defines the validated production value.

The run supervisor should:

1. start the current NovaBW learning entry point in learning mode
2. keep the machine awake while the learner is active
3. write unbuffered logs to a timestamped run directory
4. preserve the exact source/config state used for the run
5. allow the learner's internal evaluation and stop conditions to operate
6. at seven hours, send a graceful interrupt so checkpoints/telemetry can flush
7. escalate to terminate/kill only if graceful shutdown fails

## Do not bypass safety gates

The run may stop before seven hours when the learning system detects:

- NaN/Inf or optimizer instability
- systemic invalid-action/mask failure
- scheduler/reservation regression
- permanent production deadlock
- catastrophic immutable-evaluation regression
- explicit checkpoint rejection/stop condition
- unrecoverable runtime failure

An early safety stop is preferable to continuing corrupted learning.

## Artifacts to preserve outside normal Git history

- learner stdout/stderr
- run manifest
- source diff/status snapshot
- config snapshot
- telemetry
- generated trajectories
- model checkpoints
- promotion/rejection records

Do not commit large run artifacts or checkpoint binaries.

## Morning review

Review, in order:

1. total wall-clock runtime
2. completed games / environment steps
3. actor throughput
4. matchup/opponent-card coverage
5. failure-taxonomy counts
6. rejected/promoted checkpoints
7. immutable evaluation change versus parent
8. rolling evaluation
9. regression evaluation
10. strategy diversity / collapse indicators
11. final checkpoint hash/id
12. any early-stop reason

The next training run must not be configured until this review decides whether the overnight result is promoted, rejected, or requires a targeted diagnostic run.
