"""Consensus-based lag estimation for the BanglaAV temporal localization pilot.

This is a research prototype, not a claim of novel state-of-the-art performance.
It uses multiple local correlation estimates so an edited part of the clip
cannot necessarily dominate the clip-wide offset estimate.

The input contract matches the Update-03 notebook: f['ap'] is the binned
log-energy sequence and f['vp'] is binned lower-face motion. The output tuple
has the same shape as its original alignment() function.
"""

from __future__ import annotations

import numpy as np


def unit(x):
    x = np.asarray(x, dtype=np.float32)
    return np.clip((x - x.mean()) / max(1e-5, float(x.std())), -6, 6).astype("f")


def _corr(a, b):
    """Pearson correlation, with constant windows counted as uninformative."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    aa = a - a.mean()
    bb = b - b.mean()
    den = float(np.sqrt(np.dot(aa, aa) * np.dot(bb, bb)))
    if den < 1e-8:
        return 0.0
    return float(np.dot(aa, bb) / den)


def robust_alignment(f, window_bins=16, hop_bins=8, max_lag=5,
                     min_corr=.24, min_consensus=.50):
    """Estimate clip-wide lag using agreement across overlapping local windows.

    1. Derive audio energy changes and face-motion activity.
    2. Estimate the best cross-correlation lag in each local window.
    3. Exclude low-correlation windows (no reliable speech-motion match).
    4. Select the most frequently supported lag; reject low-consensus shifts.

    A positive returned lag means audio activity occurs later than mouth motion.
    The method does not inspect ground-truth annotations or model predictions.
    """
    ap = unit(np.abs(np.diff(f["ap"], prepend=f["ap"][0])))
    vp = unit(f["vp"])
    n = len(ap)
    m = min(int(max_lag), (n - 8) // 2)
    if m < 1 or ap.std() < 1e-6 or vp.std() < 1e-6:
        return 0, 0., ap, vp

    valid = np.arange(m, n - m)
    win = min(int(window_bins), len(valid))
    if win < 12:
        return 0, 0., ap, vp
    hop = max(1, int(hop_bins))
    starts = list(range(0, len(valid) - win + 1, hop))
    if starts[-1] != len(valid) - win:
        starts.append(len(valid) - win)

    votes = []
    lags = range(-m, m + 1)
    for start in starts:
        t = valid[start:start + win]
        v = vp[t]
        if float(np.std(v)) < .10:
            continue
        scores = {k: _corr(ap[t + k], v) for k in lags}
        candidate = max(scores, key=lambda k: (scores[k], -abs(k)))
        top = float(scores[candidate])
        if top >= min_corr:
            votes.append((int(candidate), top, scores[0]))

    if not votes:
        return 0, 0., ap, vp
    counts = {k: sum(1 for observed, _, _ in votes if observed == k) for k in lags}
    best = max(counts, key=lambda k: (counts[k], -abs(k)))
    supporters = [x for x in votes if x[0] == best]
    agreement = len(supporters) / len(votes)
    strength = float(np.median([x[1] for x in supporters]))
    confidence = max(0., min(1., agreement * max(0., strength)))
    if best != 0 and agreement < min_consensus:
        best = 0
    # Avoid declaring an offset when its advantage over no lag is marginal.
    if best != 0 and float(np.median([x[1] - x[2] for x in supporters])) < .04:
        best = 0
    return int(best), confidence, ap, vp


def lag_diagnostics(f):
    """Human-readable diagnostics for external experiment logging."""
    lag, conf, _, _ = robust_alignment(f)
    return {"lag_bins": int(lag), "lag_s": round(float(lag) * .08, 5),
            "consensus_confidence": round(float(conf), 6)}
