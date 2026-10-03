# Probe Navigation PPO V2

## Purpose

This was a minimal end-to-end reinforcement-learning integration test for NovaBW.

It was not intended to produce a useful StarCraft strategy. Its purpose was to verify the complete loop:

OpenBW observation → C++ bridge → Python/PyTorch policy → action → OpenBW execution → reward → PPO update → checkpoint

## Environment

- Backend: OpenBW
- Runtime: accelerated headless execution
- Decision interval: 8 game frames
- Policy device: Apple Silicon MPS
- Action space: 8 movement directions
- Primary controlled unit: Protoss Probe
- Training algorithm: PPO
- Training steps: 50,000

The Probe experiment predates the Zerg-first scope. Future gameplay curricula should use Zerg units by default.

## Training result

Final checkpoint:

- PPO updates: 195
- training steps: 50,000
- cumulative successes: 1,989
- cumulative failures: 1,045
- recent success rate near the end of training: approximately 79–91%, ending at 86%
- late-training entropy: approximately 1.64–1.70

Target sampling remained approximately balanced:

- N: 318
- NE: 299
- E: 297
- SE: 301
- S: 311
- SW: 315
- W: 317
- NW: 318

## Static single-action evaluation

The final checkpoint was also evaluated as an 8-way direction classifier.

- exact first-action accuracy: 3/8 (37.5%)
- mean entropy: 1.479

Per-direction greedy predictions:

| Target | Prediction | Result |
|---|---|---|
| N | N | correct |
| NE | N | miss |
| E | E | correct |
| SE | E | miss |
| S | SW | miss |
| SW | SW | correct |
| W | SW | miss |
| NW | N | miss |

## Interpretation

The 3/8 static classification score should not be treated as the main measure of navigation performance.

The policy was trained as a sequential controller. A first action may be adjacent to the ideal compass direction and still be corrected by subsequent actions. The much higher late-training episode success rate indicates that the sequential task learned substantially better than the single-action classifier score suggests.

Entropy dropped markedly relative to the near-uniform initial policy, confirming that the learned policy became more selective.

## Conclusion

The experiment successfully validated NovaBW's reinforcement-learning infrastructure.

This curriculum is considered complete. Future work should focus on Zerg-first gameplay tasks rather than further optimizing Probe compass-direction accuracy.

Next curriculum target:

Zerg Drone → observe mineral fields → issue Gather → verify resource collection → learn economy/production control.
