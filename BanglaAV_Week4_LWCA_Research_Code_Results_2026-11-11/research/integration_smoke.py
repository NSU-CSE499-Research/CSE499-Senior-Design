#!/usr/bin/env python3
"""Verify the augmented Kaggle notebook's new model really trains and predicts.

This executes the notebook's actual function definitions on tiny synthetic
feature arrays. It does not access LAV-DF or make detection-accuracy claims.
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
from sklearn.metrics import average_precision_score, roc_auc_score


NAMES = (
    "uid", "merge_spans", "collect_labels", "unit", "alignment", "_corr",
    "robust_alignment", "design", "fit_windows", "sigmoid", "score",
    "fit_head", "trained_heads", "head_scores", "small_f", "tiou", "runs",
    "proposals", "greedy", "t_counts", "div", "f1", "temporal_ap",
    "describe", "report", "per_clip_counts", "paired_gaps",
)


def get_namespace(path):
    notebook = json.loads(path.read_text())
    definitions = {}
    models = None
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code": continue
        s = cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])
        tree = ast.parse(s)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in NAMES:
                definitions[node.name] = node
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MODELS" for t in node.targets):
                models = ast.literal_eval(node.value)
    if set(NAMES) - definitions.keys() or models is None:
        raise AssertionError("Augmented notebook is missing model definitions")
    ns = dict(np=np, json=json, hashlib=hashlib, defaultdict=defaultdict,
              average_precision_score=average_precision_score, roc_auc_score=roc_auc_score,
              STEP=.08, TAPS=(-2, 0, 2), EPOCHS=4, HIDDEN=48,
              USE_SHIFT_CONSISTENCY=False, DATA_SEED=2026, MAX_FIT_WINDOWS=400,
              MODELS=models)
    for name in NAMES:
        part=ast.fix_missing_locations(ast.Module(body=[definitions[name]], type_ignores=[]))
        exec(compile(part, "<patched_notebook_definition>", "exec"), ns)
    return ns, notebook


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--notebook", type=Path, required=True)
    arg.add_argument("--out", type=Path, required=True)
    args=arg.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    ns, notebook = get_namespace(args.notebook)
    checks=[]

    def check(title, callable_):
        try:
            detail=callable_()
            checks.append(dict(check=title, status="PASS", detail=str(detail or "ok")))
        except Exception as exc:
            checks.append(dict(check=title, status="FAIL", detail=f"{type(exc).__name__}: {exc}"))

    def registry():
        assert ns["MODELS"]["robust_delay_aware"] == {"a":"robust_a","v":"robust_v"}
        assert len(ns["MODELS"]) == 7
    check("Seven-model registry includes robust audio/visual heads", registry)

    rng=np.random.default_rng(65)
    cache_data={}
    def make_features(key):
        n=80
        pulses=(rng.random(n)<.19).astype(np.float32)
        signed=pulses*rng.choice([-1.,1.],size=n)
        ap=np.cumsum(signed).astype(np.float32)
        vp=np.maximum(0., np.abs(signed)+rng.normal(0,.03,n)).astype(np.float32)
        A=rng.normal(0,1,(n,5)).astype(np.float32)
        V=rng.normal(0,1,(n,4)).astype(np.float32)
        f=dict(A=A,V=V,ap=ap,vp=vp,edges=np.arange(n+1)*.08,
               face=np.array(-1.,np.float32))
        cache_data[key]=f
        return f

    class Cache:
        def get(self,row,src):
            return cache_data[row["file"]]

    def row(i,split):
        kind=("real","audio","visual","both")[i%4]
        a=[[1.52,2.32]] if kind in ("audio","both") else []
        v=[[3.04,3.84]] if kind in ("visual","both") else []
        key=f"{split}-{i}"
        make_features(key)
        return dict(file=key,a=a,v=v,label=int(bool(a or v)),kind=kind,
                    group=key,speaker=f"speaker_{key}",group_verified=True)

    train=[row(i,"train") for i in range(16)]
    dev=[row(i,"dev") for i in range(8)]
    sample=cache_data[dev[0]["file"]]

    def design():
        raw=ns["design"](sample,"delay")
        robust=ns["design"](sample,"robust_delay")
        assert raw.shape==robust.shape and np.isfinite(robust).all()
        return f"matched design matrices of shape {robust.shape}"
    check("Robust and original delay-feature dimensions match", design)

    trained={}
    def train_models():
        heads,history=ns["trained_heads"](train,dev,Cache(),None,17)
        assert "robust_a" in heads and "robust_v" in heads
        assert len(heads)==10
        trained["heads"]=heads
        return f"trained {len(heads)} heads for {len(ns['MODELS'])} methods on synthetic arrays"
    check("Train all methods including two LWCA heads", train_models)

    def head_scores():
        heads=trained["heads"]
        scores=ns["head_scores"](sample,heads)
        assert set(scores)==set(heads)
        assert all(len(x)==80 and np.isfinite(x).all() for x in scores.values())
        trained["scores"]=scores
    if "heads" in trained:
        check("Generate finite robust audio and visual predictions", head_scores)

    def result_attribution():
        f=ns["small_f"](sample)
        meta={"robust_a":.5,"robust_v":.5}
        d=ns["describe"](dev[0],f,trained["scores"],"robust_delay_aware",ns["MODELS"],meta)
        assert d["estimated_audio_lag_s"]==f["robust_lag"]
        assert d["alignment_confidence"]==f["robust_alignment_confidence"]
        return "prediction metadata uses LWCA lag, not the old global lag"
    if "scores" in trained:
        check("Expose the correct per-model estimated lag",result_attribution)

    def audit_metrics():
        # Synthetic prediction is intentionally an incorrect audio alarm on a visual fake.
        truth=dict(file="attribution-test",a=[],v=[[.8,1.2]],kind="visual",label=1)
        f=dict(edges=np.arange(21)*.08,face=-1.,lag=0.,alignment_confidence=0.,
               robust_lag=0.,robust_alignment_confidence=0.)
        scores={"robust_a":np.full(20,.2),"robust_v":np.full(20,.2)}
        scores["robust_a"][10:15]=.99
        scores["robust_v"][10:15]=.99
        d=ns["describe"](truth,f,scores,"robust_delay_aware",ns["MODELS"],
                         {"robust_a":.9,"robust_v":.9})
        outcome=ns["report"]([d])
        assert outcome["audio_alarm_on_visual_only_clips"]==1
        assert outcome["visual_only_clips_with_audio_head"]==1
        return "cross-modal false attribution counted when clip-level alert is correct"
    check("Count audio alarms on visual-only fake clips",audit_metrics)

    def pair_ci():
        def fake_counts(i):
            return (f"speaker{i}",f"group{i}",True,np.array([0.,1.,1.,1.,0.]))
        pairs={m:{f"clip{i}":fake_counts(i) for i in range(4)}
               for m in ("late_fusion","raw_fusion","delay_aware","robust_delay_aware")}
        data=ns["paired_gaps"](pairs,nrep=20)
        assert len(data)==8 and any("robust_delay_aware" in x["contrast"] for x in data)
    check("Produce new paired-source comparison rows",pair_ci)

    def no_test():
        s=notebook["cells"][1]["source"]
        assert "RUN_FINAL_TEST = False" in s and "RUN_ROBUSTNESS = False" in s
        assert "ALLOW_VARIANTS = False" in s
    check("Do not accidentally enable final test or media variants",no_test)

    with (args.out/"integration_checks.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(checks[0]));writer.writeheader();writer.writerows(checks)
    passed=sum(c["status"]=="PASS" for c in checks)
    status=dict(passed=passed,total=len(checks),failed=len(checks)-passed,
                notebook_sha256=hashlib.sha256(args.notebook.read_bytes()).hexdigest(),
                method_count=len(ns["MODELS"]),
                note="Integration smoke checks only; no LAV-DF training or final evaluation")
    (args.out/"integration_summary.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
    print(f"Integrated notebook: {passed}/{len(checks)} checks passed")
    for c in checks:
        if c["status"]=="FAIL": print("FAIL:",c["check"],c["detail"])
    if passed!=len(checks): raise SystemExit(1)


if __name__=="__main__":
    main()
