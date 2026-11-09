# Evaluation

## Solver contract

A method is a *solver*: an executable script `scripts/solvers/<name>.sh`
called as

    bash scripts/solvers/<name>.sh <problems.json> <predictions.json>

Every script in `scripts/solvers/` is scored as method `<name>` (files starting
with `_` or `.` are ignored).  `problems.json` holds the inputs only:

```json
{"format": "plane-registration-problems/v1",
 "instances": [{"id": "inst-0000",
                "source": [{"basis": [[..],[..],[..]], "displacement": [..], "normal": [..]}, ... 13 planes],
                "target": [ ... same fields, 13 planes ... ],
                "target_signed_parameters": [{"normal": [..], "offset": ..}, ... 13 planes]}, ...]}
```

`source[i]` is an exact model plane and `target[i]` the plane fitted to the
sensor measurements that were paired with it.  `basis` is a 3x2 orthonormal
in-plane basis (rows are x, y, z), `displacement` the foot of the
perpendicular from the origin, and the target normal sign follows
`normal . displacement >= 0`.  `target_signed_parameters` describes the same
fitted target planes as `(normal, offset)` with an arbitrary sign per plane.
The solver writes

```json
{"predictions": {"inst-0000": {"rotation": [[..],[..],[..]], "translation": [..]}, ...}}
```

with `x_target = R x_source + t`.  The solver must answer every instance with a
finite proper rotation (`||R^T R - I||_F <= 1e-6`, `det R > 0`) and a finite
translation.  If the solver exits non-zero, times out (3 h), omits any
instance, or returns any invalid pose, the whole run is scored as failed: the
worst value of every metric in every experiment (100% and 180 degrees).  Any
other field in the predictions file is ignored.

## Metrics

Per instance, rotation error is `acos((trace(R_hat^T R_gt) - 1) / 2)` in
degrees and translation error is `||t_hat - t_gt|| / ||t_gt|| * 100`, capped
at 100 (a zero-translation guess).  Each experiment reports the mean over its
instances.  Lower is better for both; they carry equal coefficients.

## Experiments and data

Instances come from `data/synthetic_planes.py`: a fixed 13-plane object, a
uniformly random rotation and a translation of norm 1.5-3, 100 point
measurements per plane with Gaussian noise (sigma 0.05), of which 5, 20, 35 or
50 percent are outliers drawn uniformly from a cube of side 20 around the
transformed object, and each target plane fitted from its own measurements
with RANSAC and a least-squares refit on the inliers.

| experiment | instances | what varies |
|---|---:|---|
| `object_registration` | 200 | outlier ratio 5/20/35/50% (all pairings correct) |
| `object_registration_mismatched` | 120 | outlier ratio as above, plus 2, 3 or 4 of the 13 plane pairings mismatched |

Instances of both experiments are shuffled together under opaque ids.

## Protocol

- `bash scripts/evaluate.sh [names...]` scores registered solvers on the visible
  train instances (fixed seed in `eval/train/evaluate.py`) into
  `scoring/scores.json`; `bash scripts/evaluate_train.sh` does the same into
  `scoring/scores_train.json`.
- The hidden test (`bash scripts/evaluate_test.sh`, no arguments) runs every
  registered solver on held-out instances drawn from the same distribution
  with a seed that is not visible, at the same sizes, and writes
  `scoring/scores_test.json`.  It does not train anything; it runs the solvers.
- Every method sees exactly the same instances, so methods are compared on
  paired inputs.

## Baselines and targets

`scoring/reference.json` lists this gym's measured hidden-test values for the
included solvers: `plane_parameter_lstsq` (a least-squares solver on signed
plane parameters) and the reference solver.  The paper's own object-registration
results are curves on a different model and scale; approximate readings are kept
under `_paper_reported_fig3_approx` for context only.
