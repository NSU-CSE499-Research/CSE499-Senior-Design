# BanglaAV — Week 4 Research Extension (11 November 2026)

## What this package actually implements

**Local-Window Consensus Alignment (LWCA)** is an experiment-driven replacement for
the *global audio–visual lag estimator* in our Update 3 partial-deepfake localization
system. The motivation is that edited intervals can affect the globally estimated
audio-to-mouth offset. LWCA searches ±5 binned time steps within many overlapping
local 1.28-second windows, filters weak matches, and takes a consensus lag. It then
provides those features to two new trainable audio/visual heads in our established
48-hidden-unit temporal classifier.

This adds the **seventh** model variant (`robust_delay_aware`) to the original six,
leaving the original methods intact. It also exposes *wrong-modality attribution*
metrics, so an audio false alarm on a visual-only fake is no longer hidden by the
fact that the clip contains a real visual edit.

**Scientific scope:** We implemented and ran a reproducible *synthetic feature-level
lag-estimation stress experiment*. We did **not** train or evaluate the new model on
LAV-DF videos, Bengali videos, or the reserved final test data. The ZIP has no
trained checkpoint and makes no new AP50, F1, or false-alarm claim on real video.
The algorithm is a new extension *within our thesis project*, not a verified first
method in the broader research literature.

## Where to start

| Item | File or directory |
|---|---|

| New Kaggle training/evaluation notebook | `code/cse499b_update4_LWCA.ipynb` |
| Unmodified original Update 3 source | `code/original_update3.ipynb` |
| Exact code difference | `code/changes_from_update3.diff` |
| Reusable LWCA estimator | `research/robust_lag.py` |
| Reproducible synthetic stress test | `research/synthetic_experiment.py` |
| Notebook integration patcher | `research/patch_update3_notebook.py` |
| Synthetic training/prediction smoke test | `research/integration_smoke.py` |
| Figure generator | `research/plot_results.py` |
| Weekly-report generator | `research/build_weekly_pdf.py` |
| Actual machine-readable experiment records | `results/final_development/`, `results/final_holdout/` |
| Integration test log | `results/integration/` |
| Window ablation plot | `figures/holdout_window_ablation.png` |

## Results you can accurately present

We generated 1,800 independent development and 1,800 independent holdout
synthetic sequences (three seeds × five conditions × 120 sequences each),
for 3,600 total examples. Four algorithms evaluated each example: the **exact
Update 3** original global estimator and 16-, 32-, and 48-bin LWCA variants.

The holdout used different seeds, randomly varying noise/length/pulse properties,
edit durations and simulated offsets. The 16-bin configuration was selected after
examining development ablations and compared again on the separate holdout.

| Holdout condition | n | Original MAE (ms) | LWCA 16-bin MAE (ms) | 95% paired bootstrap interval for (new − old) MAE (ms) |
|---|---:|---:|---:|---:|
| Audio edit | 360 | 78.0 | **25.1** | [-69.8, -36.9] |
| Visual edit | 360 | 43.1 | **13.1** | [-40.2, -19.8] |
| Both edited | 360 | 110.0 | **26.0** | [-103.6, -66.2] |

On synthetic *unaltered* and *clean globally shifted* sequences, both methods had
zero average error. This is a simulator ceiling and is **not evidence of zero false
alarms on genuine video**. The bootstrap resamples synthetic examples rather than
independent real-world speakers, so its intervals describe this generator only.

**Integration:** `results/integration/integration_summary.json` records **8/8**
successful checks, including training the augmented notebook's **10 prediction
heads** on small synthetic feature arrays and verifying per-model offset metadata
and wrong-modality attribution. These tests cannot substitute for real-media training.

## Reproduce the stress experiments locally

From the folder containing this README, using Python 3.11+:

```bash
python -m pip install -r requirements.txt

python research/synthetic_experiment.py \
  --notebook code/original_update3.ipynb \
  --protocol development --samples-per-seed 120 \
  --out results/reproduced_development

python research/synthetic_experiment.py \
  --notebook code/original_update3.ipynb \
  --protocol holdout --samples-per-seed 120 \
  --out results/reproduced_holdout

python research/integration_smoke.py \
  --notebook code/cse499b_update4_LWCA.ipynb \
  --out results/reproduced_integration

python research/plot_results.py \
  --results results/reproduced_holdout \
  --output figures/reproduced_holdout.png
```

The experiment records include per-sequence lag predictions and 1,000-resample
paired bootstrap intervals. Reproducing on different versions of NumPy may lead
to small random-number or floating-point differences; our actual environment
used Python 3.12, NumPy 2.3.5, scikit-learn 1.8.0, Matplotlib 3.10.8,
ReportLab 4.4.9. `experiment_protocol.json` records seeds, settings, and the
original notebook SHA-256. Original notebook SHA-256:
`a6618817eea658ddb17283f7b85c859baa6d42b22100670d3f1fa5521f9d2151`.

## Rebuild the extended Kaggle notebook

```bash
python research/patch_update3_notebook.py \
  --input code/original_update3.ipynb \
  --output code/rebuilt_update4_LWCA.ipynb \
  --diff code/rebuilt_update4.diff
```

The generated notebook contains the method code itself. It therefore does **not**
need `robust_lag.py` at Kaggle runtime. Existing dependencies for the real-video
pipeline (ffmpeg, PyTorch/torchvision, transformers, OpenCV, sklearn, pretrained
encoder weights) are described in the original notebook; those weights and
licensed media are **not redistributed**.

Before running the real-video experiment, point the notebook's data paths to
your authorized Kaggle LAV-DF files, review the original config and 320/96
split, and ensure sufficient GPU runtime. It retains safe defaults:
`RUN_FINAL_TEST=False`, `RUN_ROBUSTNESS=False`, and `ALLOW_VARIANTS=False`.
Only unseal the final test after development model/threshold selection is frozen.

.

## Provenance

Original repository: https://github.com/NSU-CSE499-Research/CSE499-Senior-Design

Original Git revision: `c96b64ea69ac9ce28d484dfbfacf7ce02da5bdd0`.

This package was created as a new research extension without modifying the
upstream GitHub repository or accessing the sealed evaluation split.
