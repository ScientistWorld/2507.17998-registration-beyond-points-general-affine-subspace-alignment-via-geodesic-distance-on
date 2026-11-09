# Registration beyond Points: General Affine Subspace Alignment via Geodesic Distance on Grassmann Manifold

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

<!-- hardening-note -->
> [!NOTE]
> **Red-teamed and hardened.** A red team tried to score on this environment's hidden test without doing better research, and the environment was then fixed against the shortcuts that worked: see [`REDTEAM.md`](REDTEAM.md) and [`HARDENING.md`](HARDENING.md). The environment as it was before is kept as branch [`pre-hardening`](../../tree/pre-hardening).

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2507.17998"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2507.17998-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2507.17998](https://arxiv.org/abs/2507.17998) |
|:---|:---|
| **Domain** | Computer Vision / Geometric Registration |
| **TL;DR** | The paper turns affine Grassmannian distances between lines and planes into an explicit rigid-transform objective for registration. |

## Summary

The paper studies rigid registration from higher-order primitives such as 3D
lines and planes.  Its core contribution is an explicit affine Grassmannian
cost in terms of rotation and translation, avoiding the sign ambiguity of
common vector parameterizations.  The authors apply this cost directly and
inside Branch-and-Bound solvers for plane registration, RGB-D odometry,
Perspective-n-Line, and localization.

## Problem

Estimate rigid 3D transformations between geometric primitives such as lines
and planes.  The benchmark asks whether a solver can recover rotation and
translation from paired affine features when the features are noisy and their
common vector parameterizations may have arbitrary signs.

## The paper's method

The paper derives an optimizable registration cost for affine subspaces by
embedding lines and planes into a higher-dimensional Grassmann manifold and
expressing zero geodesic distance through basis projection residuals.

## Key results of the paper

- On Replica RGB-D odometry, the proposed Refine and BnB variants report the
- On real chessboard PnL, BnB reports 0.25 degree rotation error and Refine
- The text reports robustness on synthetic PnL up to 80 percent outliers.

## Run it

```bash
pip install sciworld
sw research 2507.17998 --mode innovate --agent claude-code
sw evaluate 2507.17998
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

