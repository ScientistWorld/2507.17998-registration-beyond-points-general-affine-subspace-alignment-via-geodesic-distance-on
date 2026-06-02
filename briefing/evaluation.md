# Evaluation

## Metrics

The evaluator reads predicted rigid transforms from JSON files in
`checkpoints/` and compares them with the ground-truth transform stored in the
dataset JSON.

Rotation error is `acos((trace(R_hat^T R_gt)-1)/2)` in degrees.  Translation
error is `||t_hat - t_gt|| / ||t_gt|| * 100`.  Lower is better for both.  The
evaluation also reports the number of plane correspondences as a resource
constraint metric.

## Baselines and Targets

The paper reports object-registration results as curves rather than extractable
table values.  The gym therefore uses a scaled synthetic analogue of the
paper's object-registration experiment.  `scoring/reference.json` records the
expected behavior on this fixed synthetic instance: the signed
plane-parameter least-squares baseline should fail under antipodal ambiguity,
while a successful primitive-registration method should recover a low-error
rigid transform on the same data.

## Evaluation Protocol

Run `bash scripts/reproduce.sh` to generate the fixed synthetic dataset, run
the baseline and proposed method, and write `scoring/scores.json`.  Run
`bash scripts/evaluate.sh` to rescore existing outputs.  The default dataset
uses 13 planes, 100 sampled points per plane, Gaussian noise with sigma 0.05,
and 5 percent outlier-corrupted samples during target plane fitting.
