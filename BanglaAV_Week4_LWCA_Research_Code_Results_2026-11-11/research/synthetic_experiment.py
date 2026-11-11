#!/usr/bin/env python3
"""Paired, reproducible stress experiment on synthetic audio/mouth-motion features.

It tests a narrow subproblem: lag-estimator accuracy under localized feature
corruption. It is NOT a LAV-DF, Bengali, or deepfake-localization benchmark.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from robust_lag import robust_alignment


SEEDS = (17, 29, 43)
HOLDOUT_SEEDS = (101, 211, 307)
CONDITIONS = ("genuine_aligned", "clean_shifted", "audio_edit",
              "visual_edit", "dual_edit")
STEP = .08


def original_alignment(notebook_path):
    """Load the precise baseline function and unit() from the team's notebook."""
    nb = json.loads(notebook_path.read_text())
    names = {"unit", "alignment"}
    found = {}
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        s = cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])
        for node in ast.parse(s).body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                found[node.name] = node
    if names != found.keys():
        raise ValueError("The reference alignment functions were not found in Update 3.")
    ns = {"np": np}
    for name in ("unit", "alignment"):
        mod = ast.fix_missing_locations(ast.Module(body=[found[name]], type_ignores=[]))
        exec(compile(mod, "<submitted_update3>", "exec"), ns)
    return ns["alignment"]


def shifted(x, lag):
    """Shift with edge-value padding, never circular wrapping."""
    x = np.asarray(x)
    n = len(x)
    t = np.arange(n) - lag
    return x[np.clip(t, 0, n - 1)]


def simulate(rng, condition, n=125, protocol="development"):
    """Controlled 10-second feature trace with known global delay and edits.

    The visual event process and audio energy increments share a latent pulse
    sequence. A local edit changes 25-35% of one or both streams to an
    alternative lag, producing a challenging timing-conflict stress case.
    """
    if protocol not in ("development", "holdout"):
        raise ValueError(protocol)
    if protocol == "holdout":
        n=int(rng.integers(105,161))
        pulse_rate=float(rng.uniform(.10,.27))
        audio_noise=float(rng.uniform(.06,.16))
        video_noise=float(rng.uniform(.06,.15))
        lag_options=(-5,-4,-3,-2,-1,1,2,3,4,5)
    else:
        pulse_rate=.20
        audio_noise=.06
        video_noise=.055
        lag_options=(-4,-3,-2,2,3,4)
    steps = rng.choice([-1., 1.], size=n).astype(np.float32)
    impulses = (rng.random(n) < pulse_rate).astype(np.float32)
    increments = steps * impulses * rng.uniform(.55, 1.4, size=n)
    base_energy = np.cumsum(increments).astype(np.float32)
    mouth = np.abs(increments).astype(np.float32)
    lag = 0 if condition == "genuine_aligned" else int(rng.choice(lag_options))
    audio = shifted(base_energy, lag)
    video = mouth.copy()

    # Independent, moderate measurement error; the edit is a separate factor.
    audio += rng.normal(0., audio_noise, n).astype(np.float32)
    video = np.maximum(0., video + rng.normal(0., video_noise, n)).astype(np.float32)
    start, length = 0, 0
    if condition in ("audio_edit", "visual_edit", "dual_edit"):
        length = (int(rng.integers(15, min(47,n//2))) if protocol=="holdout"
                  else int(rng.integers(30,46)))
        start = int(rng.integers(10, n - length - 10))
        alternatives = [k for k in (-5, -4, -3, -2, 0, 2, 3, 4, 5) if k != lag]
        wrong = int(rng.choice(alternatives))
        if condition in ("audio_edit", "dual_edit"):
            replacement = shifted(base_energy, wrong)
            audio[start:start + length] = replacement[start:start + length] * float(rng.uniform(1.1, 2.3) if protocol=="holdout" else rng.uniform(1.5,2.5))
        if condition in ("visual_edit", "dual_edit"):
            wrong_vis = shifted(mouth, int(rng.choice([-5, -3, 3, 5])))
            video[start:start + length] = wrong_vis[start:start + length] * float(rng.uniform(1.1, 2.3) if protocol=="holdout" else rng.uniform(1.5,2.5))
    return {"ap": audio, "vp": video}, lag, (start, start + length)


def summarize(rows, condition, method):
    filtered = [r for r in rows if r["condition"] == condition and r["method"] == method]
    errors = np.array([r["absolute_error_bins"] for r in filtered], float)
    return {"condition": condition, "method": method, "n": len(filtered),
            "exact_accuracy": round(float(np.mean(errors == 0)), 6),
            "mae_ms": round(float(np.mean(errors) * STEP * 1000), 3),
            "false_shift_rate": round(float(np.mean([r["estimated_lag"] != 0 for r in filtered])), 6)
            if condition == "genuine_aligned" else ""}


def bootstrap_paired(rows, condition, nboot=1000):
    """Fixed-seed paired bootstrap for robust-minus-original absolute lag error."""
    grouped = defaultdict(dict)
    for row in rows:
        if row["condition"] == condition:
            grouped[(row["seed"], row["sample"])][row["method"]] = row["absolute_error_bins"]
    data = np.array([[r["robust_consensus"], r["original_global"]]
                     for r in grouped.values()
                     if {"robust_consensus", "original_global"}.issubset(r)], float)
    if len(data) < 2:
        raise RuntimeError("Incomplete paired outputs")
    delta = (data[:, 0] - data[:, 1]) * STEP * 1000
    rng = np.random.default_rng(911)
    boot = [float(delta[rng.integers(0, len(delta), size=len(delta))].mean())
            for _ in range(nboot)]
    return {"condition": condition, "n_pairs": len(data),
            "mae_delta_robust_minus_original_ms": round(float(delta.mean()), 3),
            "bootstrap_low_ms": round(float(np.quantile(boot, .025)), 3),
            "bootstrap_high_ms": round(float(np.quantile(boot, .975)), 3)}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples-per-seed", type=int, default=120)
    parser.add_argument("--protocol", choices=("development","holdout"), default="development")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    baseline = original_alignment(args.notebook)
    seeds=SEEDS if args.protocol=="development" else HOLDOUT_SEEDS
    methods = (
        ("original_global", baseline),
        ("robust_consensus", robust_alignment),
        ("lwca_32bin", lambda x: robust_alignment(x, window_bins=32, hop_bins=12)),
        ("lwca_48bin", lambda x: robust_alignment(x, window_bins=48, hop_bins=18)),
    )
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        for condition in CONDITIONS:
            for sample in range(args.samples_per_seed):
                f, truth, edit = simulate(rng, condition, protocol=args.protocol)
                for name, method in methods:
                    found, conf, _, _ = method(f)
                    rows.append(dict(seed=seed, sample=sample, condition=condition,
                                     method=name, true_lag=truth, estimated_lag=int(found),
                                     confidence=round(float(conf), 6),
                                     absolute_error_bins=abs(int(found) - truth),
                                     edit_start_bin=edit[0], edit_end_bin=edit[1]))
        print(f"Completed seed {seed}", flush=True)
    summaries = [summarize(rows, c, m) for c in CONDITIONS for m,_ in methods]
    differences = [bootstrap_paired(rows, c) for c in CONDITIONS]
    write_csv(args.out / "per_clip_lag_estimates.csv", rows)
    write_csv(args.out / "lag_summary.csv", summaries)
    write_csv(args.out / "paired_bootstrap.csv", differences)
    provenance = dict(
        experiment="Controlled synthetic feature-level lag estimation under localized corruption",
        note="This is not an empirical LAV-DF/Bangla deepfake benchmark.",
        seeds=list(seeds), samples_per_seed_per_condition=args.samples_per_seed,
        n_simulated_examples=args.samples_per_seed * len(CONDITIONS) * len(seeds),
        generator_protocol=args.protocol,
        conditions=list(CONDITIONS), time_bin_ms=80,
        edit_duration_bins=("15-46" if args.protocol=="holdout" else "30-45"),
        max_tested_lag_bins=5 if args.protocol=="holdout" else 4,
        original_notebook_sha256=hashlib.sha256(args.notebook.read_bytes()).hexdigest(),
        methods=[name for name,_ in methods],
        ablations="16-, 32-, and 48-bin local windows; 16-bin model integrated into Kaggle notebook",
        bootstrap_resamples=1000, bootstrap_unit="individual synthetic sequence",
    )
    (args.out / "experiment_protocol.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print("Experiment complete:", provenance["n_simulated_examples"], "synthetic examples")
    for row in differences:
        print(row)


if __name__ == "__main__":
    main()
