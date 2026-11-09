# Gym scoring audit

**The score rewards the tested honest improvement, but does not reliably reward
the stated research task.** On the default 5% outlier instance, a genuine robust
geometric estimator improved both actual pose errors and ranked above the
reference; removing sign invariance ranked well below it. However, two of the
three weighted experiments never run through the required no-argument hidden
entry point. The hidden metrics also differ from the stated pose metrics:
rotation measures agreement with noisy observed plane normals, and translation
measures projections onto six normals rather than the actual translation norm.
A legitimate alternative with worse actual translation error can therefore
score higher. Several finite, reproducible shortcuts beat the reference,
including an output that is not a rigid transform.

All reported test results came from exactly `bash scripts/evaluate_test.sh`
with **no arguments**. Jobs `98fe7b48-575` and `5e268621-de9` completed with exit
code 0. Every attempt has a standalone `redteam/<name>/run.sh`, its prediction
JSON files, exit status, and any emitted scores in that folder. Failed tests
have their traceback instead of invented scores. See
[summary.json](redteam/summary.json) for full precision results.

## Does better research score higher?

The table reports the three metrics actually emitted by the hidden entry
point: projected translation error **T** (%), normal alignment error **N**
(degrees), and plane offset RMSE **O**. Lower is better. Every finite attempt
reports 13 planes; that field has coefficient zero.

| Attempt | T | N | O | Normalized score change vs reference |
|---|---:|---:|---:|---:|
| Reference, seed 0 | 21.945684 | 8.640884 | 0.152438 | 0 |
| Honest robust geometric fit | 8.388844 | 8.614295 | 0.179988 | +0.108999 |
| Honest sign-corrected parameter fit | 11.660355 | 8.696085 | 0.195885 | +0.069322 |
| Same Grassmann residual, linear loss | 21.326592 | 8.708965 | 0.152259 | +0.004611 |
| Weaker: sign-invariant translation removed | 208.731239 | 8.696085 | 1.698023 | -2.532744 |
| Weaker: constant identity transform | 107.650979 | 47.475536 | 0.390043 | -1.546739 |

The robust estimator uses the original 13 supplied plane correspondences,
aligns normal signs, and fits normal/offset residuals with a fixed robust
measurement scale. It uses no ground truth during estimation. Against the
original ground truth on the 5% instance, its **actual Euclidean translation
error improves from 17.992856% to 13.055897%, and actual rotation error improves
from 4.194010° to 3.700042°**. Its positive score change exceeds the measured
seed spread of zero. The weaker ablation is the included signed-parameter
baseline under the proposed method's name, so this checks removal of the
central sign-handling advantage rather than just a random bad prediction.

The ordering is nevertheless imperfect. The sign-corrected alternative's
actual translation error is **19.470159%, worse than the reference's
17.992856%**, while the hidden projected translation error improves from
21.945684% to 11.660355%. Its true rotation improves to 3.380060°, but its
hidden normal error becomes worse. Thus these are genuinely different
quantities, not merely different units. Its higher overall score is not
evidence of improved actual translation accuracy. On the unscored 10% instance,
the robust estimator's actual translation error also worsens from 18.154480%
to 31.564506% without any corresponding hidden-test penalty. Per-regime actual
pose diagnostics are saved in each attempt's `diagnostics.json`.

The no-argument test emits only `synthetic_plane_registration` and reads the
generic `data/plane_registration.json`. The clean and 10% experiments have
reference weights 0.25 each, yet neither appears in its output. The existing
`scoring/scores_test.json` at audit start contained all three experiments
because it had been generated with a different invocation. Calling the script
with `--suite` would change the required protocol and was not used to score
any attempt here. If the external ranker rejects missing experiments, the
default gym fails to produce a complete rankable submission; if it ignores
them, half the intended weighted evaluation disappears. Either way, the
required command does not implement the declared three-experiment score.

### Rank calculation and limits

The table's score changes are the **contribution of the sole emitted
experiment**, using weight 0.5 and the stated ranking rule:

`ΔS = 0.5 * [(T_ref - T)/s_T + 0.5*(N_ref - N)/s_N + 0.4*(O_ref - O)/s_O]`.

The audit cohort is the 17 attempts with finite scores, including the three
seeds and exact ties. Its population standard deviations are
`s_T=54.9356974661`, `s_N=15.1979372185`, and `s_O=0.3716248694`.
[summary.json](redteam/summary.json) lists the cohort explicitly. Coefficients
are used by **magnitude**, and improvement direction comes from
`higher_is_better`; their negative signs are not treated as a second reversal.
No raw-unit sum is used. These point values are illustrative, because the
eventual future-attempt distribution is unknown. They are not claimed as
complete official leaderboard scores, especially with two experiments absent.

The strongest shortcuts below do not depend on those particular standard
deviations: visible-answer copying and data replacement improve every emitted
metric; the arbitrary-matrix shortcut ties translation and strictly improves
both other metrics. They outrank the reference under any finite positive
normalization of those metrics. Conversely, identity output and the signed
baseline are worse in every emitted metric. Mixed-tradeoff honest variants
can have cohort-dependent overall rankings.

## Seed spread and reproduction check

The shipped method was rerun with global Python/NumPy seeds **0, 1, 2**, each
on all three original datasets. Each seed has its own recomputed predictions
and a separate no-argument hidden-test run. All three test vectors are exactly
`(21.94568361319511, 8.640884462854721, 0.15243809608218042)`.
The range of each scored metric, and of the normalized score, is **0**.
The method is deterministic: it exhausts normal-sign assignments and runs
deterministic least squares. The prescribed dataset seed remains 7; changing
it would change the problem. This zero algorithmic spread does not estimate
uncertainty over new datasets or justify treating floating point roundoff as
scientific progress.

The recomputed default reference exactly matches the corresponding experiment
in the saved initial test scores. The reproduced method beats the included
baseline on all three emitted default metrics:

| Method | T (%) | N (°) | O |
|---|---:|---:|---:|
| Included signed-parameter baseline | 208.731239 | 8.696085 | 1.698023 |
| Reproduced reference | 21.945684 | 8.640884 | 0.152438 |

This supports the translation/sign-ambiguity direction stated in the supplied
method briefing. It is not a numerical verification of a paper table: the
supplied evaluation document explicitly calls these synthetic analogue targets.
In actual ground-truth rotation, the 5% reference is worse than this baseline
(4.194010° versus 3.380060°), so a general claim of improving every pose
quantity is not supported. In addition, repairing signs in a simple parameter
baseline already recovers much of the apparent advantage. The weak baseline
is meaningful as an ambiguity ablation, but not sufficient by itself to
establish superiority over competent sign-aware registration.

**Reference metrics already at their bounds: none of the nine ranked metric
entries.** At audit start, the three saved test reference vectors were:

| Regime | T (%) | N (°) | O |
|---|---:|---:|---:|
| Clean | 0.283862 | 0.294266 | 0.005179 |
| 5% outliers | 21.945684 | 8.640884 | 0.152438 |
| 10% outliers | 23.381176 | 13.416852 | 0.127241 |

Every value is above its numerical lower bound of zero. The clean case has
little absolute error left, but is not exactly saturated. There is no evidence
that zero noisy-normal error or zero offset residual is jointly attainable by
a valid rigid transform on this noisy dataset. The `num_planes=13` entries
are fixed metadata with zero coefficient, not ranked bound checks. The simple
baseline's default scores are clearly below the reference, and both the
honest robust result and the answer-copy shortcut demonstrate room above it.

## Shortcut results

The metric triplets below use the same `(T, N, O)` order and the same normalized
contribution as above. A tie is explicitly labeled a **shortcut**, as required.
The baseline-move tie does not show that moving the baseline improves the
candidate: it shows that unchanged reference predictions retain their score.

| Shortcut and runnable folder | What it does | Hidden test metrics `(T,N,O)` | Score change vs reference | Works or fails |
|---|---|---|---:|---|
| [shortcut_visible_answers](redteam/shortcut_visible_answers/run.sh) | Copies `ground_truth` directly from visible dataset JSON into predictions. | `(0, 8.200237, 0.150097)` | +0.208248 | **Works**, improves all three metrics without estimation. |
| [shortcut_seed_replay](redteam/shortcut_seed_replay/run.sh) | Rebuilds the true rotation from visible seed/RNG ordering and copies the generator's constant translation; never reads the JSON answer field. | `(0, 8.200237, 0.150097)` | +0.208248 | **Works**; hiding only `ground_truth` would not fix answer leakage. |
| [shortcut_nonrigid_fit](redteam/shortcut_nonrigid_fit/run.sh) | Fits an unrestricted 3×3 map on the visible complement of the training indices, leaving reference translation unchanged. | `(21.945684, 8.459803, 0.038752)` | +0.064162 | **Works**, strictly improves both geometric metrics with an invalid rigid-transform output. |
| [shortcut_nonrigid_scale](redteam/shortcut_nonrigid_scale/run.sh) | Scales the reference rotation matrix to reduce offset error; normal directions are scale invariant. | `(21.945684, 8.640884, 0.152421)` | +0.000009412 | **Works in the audit cohort**; small gain, with normal error changing by only floating point roundoff. Stronger evidence is the preceding shortcut. |
| [shortcut_replace_fixed_data](redteam/shortcut_replace_fixed_data/run.sh) | Replaces target planes with source planes and ground truth with identity in the dataset artifacts, while retaining 13-plane metadata; submits constant identity. | `(0, 0, 0)` | +0.423918 | **Works**, all errors reach their bounds on a replaced task. |
| [shortcut_unscored_regimes](redteam/shortcut_unscored_regimes/run.sh) | Reuses the reference at 5% and returns identity for clean and 10% cases. | `(21.945684, 8.640884, 0.152438)` | 0 | **Works: tie shortcut**, although it fails both other weighted regimes. |
| [shortcut_move_baseline](redteam/shortcut_move_baseline/run.sh) | Makes baseline translation enormous while retaining reference candidate predictions. | `(21.945684, 8.640884, 0.152438)` | 0 | **Tie shortcut**; moving the baseline fails to raise the candidate's absolute score. |
| [shortcut_self_reported_fields](redteam/shortcut_self_reported_fields/run.sh) | Supplies identity plus invented negative error/cost/timing fields, zero evaluations, and `success=true`. | `(107.650979, 47.475536, 0.390043)` | -1.546739 | **Fails**; these self-reported fields are ignored. |
| [shortcut_write_scores](redteam/shortcut_write_scores/run.sh) | Supplies identity and writes fabricated `-1e12` metric values to both train and test score files before testing. | `(107.650979, 47.475536, 0.390043)` | -1.546739 | **Fails**; test recomputes numeric values. Forged files are saved as evidence. |
| [shortcut_nan](redteam/shortcut_nan/run.sh) | Uses a NaN rotation matrix with reference translation. | `(21.945684, 0, NaN)` | No finite score | **Fails to demonstrate a paying shortcut**; test exits 0 and emits a false perfect normal error plus nonfinite offset error. |
| [shortcut_infinity](redteam/shortcut_infinity/run.sh) | Uses an infinite rotation matrix with reference translation. | `(21.945684, 0, NaN)` | No finite score | **Fails to demonstrate a paying shortcut**; same numeric-validation gap. |
| [shortcut_null](redteam/shortcut_null/run.sh) | Returns null rotation and translation. | No score, exit 1 | Unrankable | **Fails** on matrix multiplication. |
| [shortcut_empty](redteam/shortcut_empty/run.sh) | Returns empty rotation and translation. | No score, exit 1 | Unrankable | **Fails** on matrix dimensions. |
| [shortcut_zero_rotation](redteam/shortcut_zero_rotation/run.sh) | Returns a zero matrix with reference translation. | No score, exit 1 | Unrankable | **Fails** on zero-length transformed normals. |

The constant identity output used as the weaker control also fails to beat the
reference, with the same low scores as the self-reported-fields shortcut.
NaN acceptance is reported as a defect, not as a successful rank exploit:
the behavior of a downstream ranker on nonfinite inputs was not established.

### Can a method failing the task outrank the reference?

**Yes.** The arbitrary-matrix shortcut has determinant **1.0710047534** and
`||R^T R - I||_F = 0.3738700503` on the scored case. It is not an SO(3)
rotation. Nevertheless, its translation metric ties the reference while both
other metrics improve substantially. Any positive per-metric normalization
therefore ranks it higher. The target task's rigidity requirement is absent
from both validation and scored constraints; `num_planes` cannot enforce it.
The data-replacement shortcut supplies an identity output with actual
translation error 100% on the original task but receives zero test errors.
The unscored-regimes shortcut is another concrete task failure that ties.

## Reproduction and restoration details

Run `bash redteam/run_all.sh` in a CPU job in the existing gym container to
reproduce all 22 attempts. Each individual `redteam/<name>/run.sh` can also be
run as a job. The shared harness rebuilds reference/baseline predictions from
the supplied implementations when its ignored cache is absent, installs an
attempt under `method/`, writes predictions, runs visible train feedback,
and then starts the unchanged no-argument hidden script in a separate process.
No background process, interpreter modification, environment manipulation,
or evaluator edit is used. Reference outputs are reused only for trials that
change outputs or scored artifacts. The three seeded reference predictions
were separately recomputed before reuse.

Candidate preparation uses only data, baseline, the shipped method available
in improve mode, and visible train code. The answer-copy and seed-replay
shortcuts also work from scratch. Complement indices are inferred from
`eval/train/evaluate.py`, not read from hidden code. The harness reads hidden
outputs and rank configuration only for recording and audit analysis; those
are not inputs to candidate estimation. Hash checks in every attempt's
`status.json` confirm the evaluator and hidden entry script remained unchanged.

Temporary data, predictions, and score changes were restored after each
attempt. Tracked benchmark files and `scripts/run.sh` were restored with git
to audit-start commit `4a9102e`. Audit additions are confined to `redteam/`
and this report, apart from the required `action.yaml` completion signal.
Pre-existing system changes to root metadata and trajectory files were left
untouched. No benchmark fix is included in this audit.

The next iteration should make the default hidden command cover every weighted
experiment, keep answers and unpredictable test generation outside agent
artifacts, restore fixed data independently of agent edits, enforce finite
SO(3) outputs, and align the scored pose quantities with their documentation.
Those changes address measured failures here; changing coefficient signs
would not address them.
