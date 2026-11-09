#!/bin/bash
set -eu
cd /home/user
python3 redteam/harness.py initialize
for case_name in reference_seed_0 reference_seed_1 reference_seed_2 \
    better_sign_corrected better_robust_geometric variant_linear_loss \
    weaker_without_sign_invariance weaker_identity \
    shortcut_visible_answers shortcut_seed_replay shortcut_nonrigid_scale shortcut_nonrigid_fit \
    shortcut_replace_fixed_data shortcut_move_baseline shortcut_unscored_regimes \
    shortcut_self_reported_fields shortcut_write_scores \
    shortcut_nan shortcut_infinity shortcut_null shortcut_empty shortcut_zero_rotation; do
    echo "Running $case_name"
    bash "redteam/$case_name/run.sh"
done
python3 redteam/harness.py summarize
