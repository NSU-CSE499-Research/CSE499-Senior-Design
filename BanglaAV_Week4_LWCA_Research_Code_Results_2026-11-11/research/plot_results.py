#!/usr/bin/env python3
"""Plot measured synthetic holdout lag error. No synthetic result is real-media accuracy."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    with (args.results / "lag_summary.csv").open(newline="", encoding="utf-8") as file:
        values = {(row["condition"], row["method"]): float(row["mae_ms"])
                  for row in csv.DictReader(file)}
    conditions = ["audio_edit", "visual_edit", "dual_edit"]
    methods = [("original_global", "Global baseline", "#677c90"),
               ("robust_consensus", "LWCA (16 bins)", "#127b8e"),
               ("lwca_32bin", "LWCA (32 bins)", "#ba853d"),
               ("lwca_48bin", "LWCA (48 bins)", "#a6a9af")]
    positions = np.arange(len(conditions))
    fig, ax = plt.subplots(figsize=(8.6, 3.8), dpi=170)
    fig.patch.set_facecolor("white")
    width = .18
    for i, (method, label, color) in enumerate(methods):
        height = [values[c, method] for c in conditions]
        x = positions + (i - 1.5) * width
        ax.bar(x, height, width, color=color, label=label)
        for px, py in zip(x, height):
            ax.text(px, py + 2, f"{py:.1f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(positions, ["Audio-only edit", "Visual-only edit", "Both streams edited"])
    ax.set_ylabel("Mean absolute lag error (ms)")
    ax.set_ylim(0, 130)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linewidth=.5, alpha=.3)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, 1.19), ncol=4, frameon=False, fontsize=8)
    fig.text(.5, .012, "Holdout: synthetic feature sequences; 360 independent cases per edit condition",
             ha="center", fontsize=8, color="#526070")
    fig.subplots_adjust(top=.82, bottom=.18, left=.095, right=.99)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=200)
    print("Wrote:", args.output)


if __name__ == "__main__":
    main()
