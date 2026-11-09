# Hardening report (iteration 11)

**Verdict.** Better results now score higher and worse ones lower, by margins
well above the test's noise, and every shortcut the red team ran (plus nine
new ones) now scores far below the reference or fails outright.  To get there
the test was rebuilt rather than patched: the old "hidden test" was a split of
the planes of one visible instance whose answer was on disk.  The reference
method is unchanged and still shows the paper's claim (much lower translation
error than a signed plane-parameter solver).  One honest caveat: on clean
correspondences, sign-aware parameter fits beat the reference's translation,
so the paper's advantage is reproduced against the sign-ambiguous parameter
family it criticises, not against every parameter solver.

All numbers below come from `bash scripts/evaluate_test.sh` run by the
harness in `redteam/hardening/` (jobs `c7e9ed27-e1b`, preempted, and
`663860ef-185`).  Per attempt: `redteam/hardening/results/<name>/` holds
the scores, the status (exit code, files the attempt changed, whether hidden
test files were touched), the log and, for honest attempts, per-instance
errors.  `results/summary.json` holds the full-precision tables.

## What was wrong and what changed

| Problem (REDTEAM.md) | Fix |
|---|---|
| Test answers visible: `data/*.json` carried `ground_truth`; the visible generator used a constant translation (seed replay) | Test instances are generated at test time inside `eval/test/` from a 128-bit seed that exists only there, with a frozen generator copy.  Every instance has its own uniform random rotation and random translation.  Solvers receive inputs only; ground truth never leaves the evaluator process.  The old data files are deleted. |
| One fixed instance, so no statistical power and no seed-noise estimate | 200 + 120 test instances; every method sees identical instances (paired comparisons). |
| Fixed data could be replaced by the method | The test never reads `data/`; edits there change only train. |
| No-argument entry point scored one of three weighted experiments | `bash scripts/evaluate_test.sh` (no arguments) runs every solver in `scripts/solvers/` and scores every weighted experiment. |
| Hidden metrics were not the paper's (noisy-normal agreement, projected translation, plane-offset residual) | Scored metrics are the paper's: rotation geodesic error (deg) and relative translation error (%) against ground truth.  `plane_offset_rmse` and the constant `num_planes` were removed. |
| Non-rigid, NaN and Inf outputs accepted (NaN gave a false perfect rotation) | A pose must be finite, have rotation entries in [-1, 1], `||R^T R - I||_F <= 1e-6` and `det R > 0`, and every instance must be answered.  Otherwise the whole run fails at the caps (100%, 180 deg) on every metric of every experiment.  Comparisons are NaN-safe; a review caught that a rotation scaled by 1e200 made `R^T R` overflow to NaN and pass. |
| Unbounded metrics | Translation error is capped at 100% per instance (a zero-translation guess); rotation is bounded by 180 deg.  A failed run therefore sits at the worst value of every metric and never outranks a solved one. |
| Method-written numbers | Only `rotation` and `translation` are read.  Every scored number is recomputed. |
| Experiments did not reach the paper's regime | Outlier ratios 5-50% with RANSAC plane fitting, as in the paper's Sec. 5.1 (`object_registration`).  Plus `object_registration_mismatched`, where 2-4 of 13 plane pairings are wrong; that is where the paper says its refinement falls short. |

The method needs no training, so the hidden test runs the solvers on the
hidden inputs.  It takes about 3.5 minutes on one CPU for the two registered
solvers (reference 105 s, baseline 82 s).

## Does a better result score higher?

The rank change ΔS = Σ_exp w · Σ_metric |c| · (ref − x) / s, with s the
population standard deviation of that metric over the attempts.  Two cohorts
are shown: the 10 honest attempts, and all 26 attempts (including failures at
the caps).  The 95% interval is a paired bootstrap over test instances (4000
resamples, honest-cohort s).  Errors are hidden-test means: T = translation
error %, R = rotation error deg.

| Attempt | object_registration T / R | mismatched T / R | ΔS honest [95% CI] | ΔS all |
|---|---|---|---|---:|
| **reference** `grassmann_refine` | 2.190 / 0.739 | 13.166 / 1.532 | 0 | 0 |
| better: inlier-set consensus, then the reference's refinement | 2.179 / 0.737 | 2.527 / 0.779 | **+0.116** [+0.080, +0.159] | +0.116 |
| better: consensus + displacement-term reweighting | 1.001 / 0.738 | 1.166 / 0.787 | **+0.146** [+0.110, +0.188] | +0.147 |
| variant: sign-aligned joint normal/offset fit (red-team "robust geometric") | 0.273 / 0.745 | 2.599 / 2.724 | +0.121 [+0.086, +0.162] | +0.132 |
| trade-off: displacement reweighting only | 1.010 / 0.741 | 20.629 / 8.388 | −0.132 [−0.193, −0.074] | −0.098 |
| ablation: reference's linear initialiser, no refinement | 1.051 / 0.751 | 39.928 / 13.879 | −0.386 [−0.442, −0.330] | −0.331 |
| weaker: reference with non-robust (linear) loss | 2.205 / 0.751 | 26.098 / 5.151 | −0.170 [−0.205, −0.137] | −0.156 |
| weaker: sign invariance removed (signed parameters) | 95.087 / 0.751 | 96.607 / 13.879 | −2.251 [−2.302, −2.198] | −2.236 |
| weaker: identity pose | 100.000 / 124.911 | 100.000 / 131.540 | −5.598 [−5.705, −5.488] | −3.892 |

- The two genuinely better methods (each better on both experiments, or tied
  on one and better on the other) rank above the reference, with intervals
  far from zero.  The combined method ranks above either of its parts.
  Every weaker variant ranks below.
- Paired evidence per metric:
  - Consensus vs reference, mismatched translation: −10.6 points [−14.8, −7.1].
  - Consensus vs reference, `object_registration` translation: −0.011 [−0.030, 0.0].  This is a tie, as it should be: with no wrong pairings it accepts all planes.
  - Reweighting vs reference, `object_registration` translation: −1.18 [−1.40, −0.98].
- A method better on one experiment and much worse on the other (reweighting
  only, the linear initialiser) ranks below the reference.  Those are
  trade-offs, not better methods.
- **Before** (REDTEAM.md, old gym, only the 5% instance emitted): robust
  geometric +0.109, sign-corrected +0.069, linear loss +0.005, signed
  parameters −2.533, identity −1.547.  The sign-corrected variant ranked above
  the reference while its true translation error was *worse* (19.5% vs 18.0%);
  the old metric did not measure pose error.  Now every number is pose error
  against ground truth.

**Train vs test** (same generator and sizes, different seeds).  Honest
methods score alike on both:

| Method | T train / test | R train / test | mismatched T train / test |
|---|---|---|---|
| reference | 2.212 / 2.190 | 0.685 / 0.739 | 13.06 / 13.17 |
| consensus | 2.210 / 2.179 | 0.699 / 0.737 | 2.21 / 2.53 |
| joint fit | 0.265 / 0.273 | 0.684 / 0.745 | 3.26 / 2.60 |

Mismatched-experiment rotation is noisier: the reference's mean is 2.96 on
train vs 1.53 on test, from a few large failures among 120 instances.  Paired
comparisons on identical instances are unaffected.

**Seed noise.** The reference is deterministic: an exhaustive sign search
followed by deterministic least squares, with fixed instances, so reruns give
identical scores.  The red team measured zero spread across global seeds, and
this job's reference reproduced the earlier run's numbers to the last digit.
The relevant noise is instance sampling.  The paper's effect (reference vs
signed-parameter baseline, translation) is +92.9 points [90.7, 94.8] on
`object_registration` and +83.4 [79.1, 87.3] on mismatched pairings, orders of
magnitude above it.

## Shortcuts: fix, and score before → after

All shortcuts ran through the unchanged no-argument entry point.  ΔS is in
the all-attempt cohort; the reference is 0.

| Shortcut | Before | Fix | After |
|---|---|---|---|
| Copy visible `ground_truth` / replay the visible seed | +0.208 (both), all metrics improved | No test answers or test seed outside `eval/test/`; random pose per instance | Found 0/320 answers; identity fallback, −3.89 |
| Unrestricted 3x3 map (non-rigid) | +0.064 | SO(3) validation, run fails | Failed (`||R^T R - I|| = 0.029`), −4.56 |
| Scale the rotation by 1.001 | +9e-6 | SO(3) validation | Failed, −4.56 |
| Scale the rotation by 1e200 (new; overflow made the naive check NaN) | n/a | Entry bound in [-1, 1] and NaN-safe checks | Failed, −4.56 |
| Reflection, det −1 (new) | n/a | det > 0 | Failed, −4.56 |
| Replace fixed data (targets := sources, truth := identity) | +0.424, all errors 0 | Test generates its own instances in memory before any solver runs; never reads `data/` | Edits to `data/` and even `eval/test/hidden_instances.py` had no effect on the scored instances; −3.69 |
| Fail the unscored regimes / answer only half | 0 (tie) | All experiments scored by the no-argument run; instances shuffled under opaque ids | Reference on half, identity on half: −1.95 |
| NaN / Inf rotation | No finite score; a false 0 normal error was emitted | Non-finite pose fails the run | Failed, −4.56 |
| null / empty / zero rotation, missing instance, solver crash | Unrankable (traceback) or n/a | Every such case is a scored failure, not an evaluator crash | Failed, −4.56 each |
| Self-reported error/success fields | Ignored (−1.547) | Still ignored | −3.89 (identity pose) |
| Write fake `scores_*.json` during the run | Ignored | The evaluator writes scores last, from its own computation | −3.89 (fake values overwritten) |
| Move the baseline | 0 (tie) | Not re-run: scores are absolute pose errors, and each solver is scored only on its own predictions | Cannot change any other method's score |

## Shortcuts left

- **Reading `eval/test/` at test time.**  The hidden test runs the solver in
  the same filesystem, so a solver that imports
  `eval/test/hidden_instances.py` and the seed in `eval/test/evaluate.py` can
  regenerate the answers.  No small fix closes this: chmod tricks are
  reversible by the same user, and a test-time random seed would make results
  irreproducible.  The grader must check that solver code never opens
  `eval/`.  It was not run, since it trivially scores 0 error.
- **Sabotage.**  A solver can delete other solvers, kill the evaluator, or leave
  a background process that edits `scoring/` afterwards.  None of these
  raises its own score (absolute metrics); the last is excluded by the task's
  scope (fresh container).
- **Compute.**  There is no per-instance budget, only a 3-hour suite timeout.
  More search (for example exhaustive correspondence search) is legitimate
  method work here: the objective a solver can compute is not the scored
  error.

## Reference score before → after

- **Before** (old hidden test, 5% instance only; projected translation %,
  normal error deg, offset RMSE): 21.95 / 8.64 / 0.152.  True pose error on
  that instance: 17.99% / 4.19 deg.
- **After** (hidden test):
  - `object_registration`: 2.190% / 0.739 deg.
  - `object_registration_mismatched`: 13.166% / 1.532 deg.
- Signed-parameter baseline: 95.09% / 0.751 deg and 96.61% / 13.88 deg.
- The reference's errors grow with the outlier ratio, as in the paper's
  Fig. 3:

| Outlier ratio | Translation % | Rotation deg |
|---:|---:|---:|
| 5% | 1.06 | 0.36 |
| 20% | 1.85 | 0.59 |
| 35% | 2.76 | 0.83 |
| 50% | 3.09 | 1.17 |

## Headroom check

- **Bounds.** The reference sits at the bound of no scored metric (all
  bounds are 0).  `object_registration_mismatched` was added as the experiment
  where the paper's own method falls short.  The paper says refinement depends
  on the initial solver filtering outlier correspondences, and reports Refine
  failing on the mismatch-heavy Room1 sequence.
- **Mismatched experiment.** An inlier-set-maximisation front end (the idea of
  the paper's BnB) cuts the error from 13.17% / 1.53 deg to 2.53% / 0.78 deg.
- **`object_registration` translation.** Simple variants already beat the
  reference: displacement reweighting gives 1.01%, a sign-aligned joint fit
  0.27%.  The reference's embedded displacement residual weights each plane's
  offset error by about 1/(1 + |c|²), downweighting planes far from the
  origin.  This is real headroom; no variant reaches the bound.
- **`object_registration` rotation.** This is the least movable metric: every
  normal-based estimator lands within 0.737-0.751 deg.  It is a constraint
  metric (the quantity the paper's refinement trades away), and it still
  separates methods.  The reference is 0.012 deg [0.003, 0.020] better than
  the parameter solvers.
- **Baseline.** The simple baseline scores clearly below the reference on a
  scale with room above: 95% vs 2.2% translation error, against a best
  variant at 0.27%.

## Weights and coefficients (changed)

- **Rotation coefficient 0.5 → 1.0** (translation stays 1.0, primary).  The
  paper evaluates both errors side by side and presents its refinement as
  *trading* rotation for translation.  A rotation weight of half the
  translation weight would reward exactly that trade.
- **Experiment weights 0.6 / 0.4** (was clean 0.25 / 5% 0.5 / 10% 0.25).  The
  object-registration analogue is the paper's experiment.  Robustness to
  outlier correspondences is the paper's second contribution (BnB) and the
  gym's headroom experiment.
- **Coefficient signs.** Coefficients are positive.  The direction comes only
  from `higher_is_better: false`.

## What could not be fixed, stated plainly

- **Strength of the paper's claim.**  It is reproduced against
  sign-ambiguous parameter solvers (the paper's LinEq family): 95% vs 2.2%.
  It is *not* reproduced against sign-aware parameter solvers.  The
  reference's own linear initialiser (1.05%) and a sign-aligned joint fit
  (0.27%) both beat it in translation on correct correspondences.  The
  refinement's value in this gym is robustness: the initialiser alone scores
  39.9% on mismatched pairings vs 13.2% for the reference.
- **Rotation direction.**  The paper reports Refine's rotation slightly worse
  than LinEq's.  Here it is slightly better (0.739 vs 0.751).
- **Scale.**  The Space Station model and the paper's 500 sets per ratio are
  not reproduced.  The paper's Fig. 3 curves are on a different object and
  scale, so approximate readings are kept under `_paper_reported_fig3_approx`
  in `scoring/reference.json`, not as targets.
- **Scope of the reference.**  It implements the paper's Refine path; the BnB
  solver is not implemented.
- **Normalisation.**  ΔS uses this audit's cohort standard deviations.  The
  real spread of future attempts is unknown, but the orderings above hold for
  both cohorts shown.
