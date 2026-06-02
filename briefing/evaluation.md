# Evaluation

## Metrics

The evaluator reads predicted rigid transforms from JSON files in
`checkpoints/` and compares them with the ground-truth transform stored in the
dataset JSON.

Rotation error is `acos((trace(R_hat^T R_gt)-1)/2)` in degrees.  Translation
error is `||t_hat - t_gt|| / ||t_gt|| * 100`.  The evaluator also reports
root-mean-square plane-offset residuals after applying the predicted transform.
Lower is better for all three scored metrics.  The number of plane
correspondences is reported as fixed problem-scale metadata.

## Baselines and Targets

The paper reports object-registration results as curves rather than an
extractable numeric table.  The gym therefore uses a scaled synthetic analogue
of the paper's object-registration experiment, and `scoring/reference.json`
records expected behavior on this fixed synthetic instance rather than literal
paper table entries.  A successful primitive-registration solver should
recover a low-error rigid transform on the same data while remaining robust to
equivalent plane descriptions with inconsistent normal signs.

## Evaluation Protocol

Run `bash scripts/reproduce.sh` to generate the fixed synthetic dataset,
produce the included reference outputs, and write `scoring/scores.json`.  Run
`bash scripts/evaluate.sh` to rescore existing outputs.  Any method can be
evaluated by writing prediction JSON files containing a method name, rotation
matrix, and translation vector under `checkpoints/`.  The default dataset uses
13 planes, 100 sampled points per plane, Gaussian noise with sigma 0.05, and 5
percent outlier-corrupted samples during target plane fitting.
