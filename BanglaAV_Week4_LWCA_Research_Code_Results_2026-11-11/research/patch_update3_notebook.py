#!/usr/bin/env python3
"""Integrate LWCA into the team's actual Update 3 Kaggle notebook.

Generates a new notebook copy and leaves the original file untouched. The new
model is trained and evaluated beside the six existing baselines if the user
runs the generated notebook with permitted LAV-DF media on Kaggle.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path


def read_source(cell):
    value = cell["source"]
    return value if isinstance(value, str) else "".join(value)


def change_once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f"{label}: expected exactly one occurrence, found {text.count(old)}")
    return text.replace(old, new, 1)


def extract(module_path, names):
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            found[node.name] = ast.get_source_segment(text, node)
    if set(found) != set(names):
        raise ValueError("Missing methods in robust_lag.py")
    return "\n\n".join(found[name] for name in names)


PAIRED_CI_FUNCTION = '''def paired_gaps(summaries,nrep=400):
    """Paired differences in FPR and segment F1, including the new LWCA model."""
    comparisons=(("delay_aware","late_fusion"),
                 ("robust_delay_aware","delay_aware"),
                 ("robust_delay_aware","raw_fusion"),
                 ("robust_delay_aware","late_fusion"))
    out=[]
    for proposed,reference in comparisons:
        if proposed not in summaries or reference not in summaries: continue
        left,right=summaries[proposed],summaries[reference]
        if left.keys()!=right.keys() or not left: raise ValueError("Paired comparison clip IDs differ")
        contrast=proposed+" minus "+reference
        if all(left[k][0] for k in left): level=0; group_type="speaker"
        elif all(left[k][2] for k in left): level=1; group_type="source"
        else:
            out.extend(dict(metric=m,delta=None,lo=None,hi=None,cluster_type="IDs incomplete",
                            contrast=contrast) for m in ("genuine_FPR","any_segment_F1@50"))
            continue
        groups=defaultdict(lambda:np.zeros((2,5)))
        for k in left:
            groups[left[k][level]][0]+=left[k][3]
            groups[left[k][level]][1]+=right[k][3]
        a=np.array(list(groups.values()))
        rng=np.random.default_rng(601)
        for metric in ("genuine_FPR","any_segment_F1@50"):
            def difference(counts):
                vals=[]
                for fp,n,tp,sfp,fn in counts:
                    vals.append(div(fp,n) if metric=="genuine_FPR" else (f1(tp,sfp,fn) if tp+fn else np.nan))
                return vals[0]-vals[1]
            full=difference(a.sum(0)); boot=[]
            if len(a)>=2:
                for _ in range(nrep):
                    x=difference(a[rng.integers(len(a),size=len(a))].sum(0))
                    if np.isfinite(x): boot.append(x)
            out.append(dict(metric=metric,delta=full,
                            lo=float(np.quantile(boot,.025)) if boot else None,
                            hi=float(np.quantile(boot,.975)) if boot else None,
                            clusters=len(a),cluster_type=group_type,
                            valid_replicates=len(boot),contrast=contrast))
    return out'''


def patch_notebook(original, module_path):
    result = json.loads(json.dumps(original))
    cells = result["cells"]
    original_sources = [read_source(c) for c in cells]

    # Original model settings remain safe: no real test or unauthorized media variants.
    settings_id = next(i for i,s in enumerate(original_sources) if 'CODE_VERSION = "nsu-lav-1.0"' in s)
    code = original_sources[settings_id]
    code = change_once(code, 'CODE_VERSION = "nsu-lav-1.0"',
                       'CODE_VERSION = "nsu-lav-1.1-lwca"', "code version")
    code = change_once(code, 'EVAL_MODEL = "delay_aware"',
                       'EVAL_MODEL = "robust_delay_aware"', "default model")
    cells[settings_id]["source"] = code

    model_id = next(i for i,s in enumerate(original_sources) if "TAPS=(-2,0,2)" in s)
    code = original_sources[model_id]
    insert = extract(module_path, ("_corr", "robust_alignment"))
    code = change_once(code, "def design(f,kind):", insert + "\n\ndef design(f,kind):", "insert method")
    code = change_once(code, "lag,conf,ap,vp=alignment(f)",
                       'lag,conf,ap,vp=(robust_alignment(f) if kind=="robust_delay" else alignment(f))',
                       "choose alignment")
    code = change_once(code, 'elif kind=="delay":',
                       'elif kind in ("delay","robust_delay"):', "new design branch")
    code = change_once(code,
        '"delay_aware":{"a":"delay_a","v":"delay_v"}}',
        '"delay_aware":{"a":"delay_a","v":"delay_v"},\n'
        '        "robust_delay_aware":{"a":"robust_a","v":"robust_v"}}',
        "new model registry")
    code = change_once(code, 'kind="delay" if typ=="delay0" else typ',
                       'kind="robust_delay" if typ=="robust" else ("delay" if typ=="delay0" else typ)',
                       "training routing")
    code = change_once(code, 'typ="delay" if typ=="delay0" else typ',
                       'typ="robust_delay" if typ=="robust" else ("delay" if typ=="delay0" else typ)',
                       "inference routing")
    code = change_once(code, 'penalty=.5 if typ=="delay" and USE_SHIFT_CONSISTENCY else 0.',
                       'penalty=.5 if typ in ("delay","robust") and USE_SHIFT_CONSISTENCY else 0.',
                       "consistency supervision for new method")
    cells[model_id]["source"] = code

    metric_id = next(i for i,s in enumerate(original_sources) if "def small_f(f):" in s)
    code = original_sources[metric_id]
    code = change_once(code,
        'def small_f(f):\n    lag,confidence,_,_=alignment(f)\n'
        '    return {"edges":f["edges"],"face":float(f["face"]),"lag":lag*STEP,"alignment_confidence":confidence}',
        'def small_f(f):\n'
        '    lag,confidence,_,_=alignment(f)\n'
        '    rlag,rconfidence,_,_=robust_alignment(f)\n'
        '    return {"edges":f["edges"],"face":float(f["face"]),"lag":lag*STEP,\n'
        '            "alignment_confidence":confidence,"robust_lag":rlag*STEP,\n'
        '            "robust_alignment_confidence":rconfidence}',
        "per-model lag metadata")
    code = change_once(code, '"estimated_audio_lag_s":float(f["lag"])',
        '"estimated_audio_lag_s":float(f["robust_lag"] if model=="robust_delay_aware" else f["lag"])',
        "reported offset")
    code = change_once(code, '"alignment_confidence":float(f["alignment_confidence"])',
        '"alignment_confidence":float(f["robust_alignment_confidence"] if model=="robust_delay_aware" else f["alignment_confidence"])',
        "reported confidence")
    code = change_once(code, '    return out\n\ndef cluster_ci(dets,seed=903,nrep=400):',
        '    # Cross-modal attribution errors are hidden by any-stream interval metrics.\n'
        '    visual_only=[d for d in dets if d["kind"]=="visual" and "a" in d["pred"]]\n'
        '    audio_only=[d for d in dets if d["kind"]=="audio" and "v" in d["pred"]]\n'
        '    out["audio_alarm_on_visual_only_clips"]=sum(bool(d["pred"]["a"]) for d in visual_only)\n'
        '    out["visual_only_clips_with_audio_head"]=len(visual_only)\n'
        '    out["visual_alarm_on_audio_only_clips"]=sum(bool(d["pred"]["v"]) for d in audio_only)\n'
        '    out["audio_only_clips_with_visual_head"]=len(audio_only)\n'
        '    out["audio_spurious_on_visual_rate"]=div(out["audio_alarm_on_visual_only_clips"],len(visual_only))\n'
        '    out["visual_spurious_on_audio_rate"]=div(out["visual_alarm_on_audio_only_clips"],len(audio_only))\n'
        '    return out\n\ndef cluster_ci(dets,seed=903,nrep=400):',
        "per-modality spurious-alarm audit")
    cells[metric_id]["source"] = code

    export_id = next(i for i,s in enumerate(original_sources) if "def save_eval(directory" in s)
    code = original_sources[export_id]
    code = change_once(code, 'if model in ("late_fusion","delay_aware"):',
                       'if model in ("late_fusion","delay_aware","raw_fusion","robust_delay_aware"):',
                       "pair collection")
    cells[export_id]["source"] = code

    paired_id = next(i for i,s in enumerate(original_sources) if "def paired_gaps(summaries" in s)
    code = original_sources[paired_id]
    tree = ast.parse(code)
    old_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "paired_gaps")
    old_method = ast.get_source_segment(code, old_node)
    code = change_once(code, old_method, PAIRED_CI_FUNCTION, "generalized paired CI")
    cells[paired_id]["source"] = code

    # Old outputs belong only to the original version: clear them from the new notebook.
    for cell in cells:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
            ast.parse(read_source(cell))
    result["metadata"]["banglaav_extension"] = {
        "name": "Local-Window Consensus Alignment", "version": "1.1-lwca",
        "experimental_status": "needs actual LAV-DF training and evaluation",
    }
    diff=[]
    for i,(before,after) in enumerate(zip(original_sources,[read_source(c) for c in cells])):
        if before != after:
            diff += list(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                                              fromfile=f"cell_{i}_original",tofile=f"cell_{i}_lwca"))
    return result, "".join(diff)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diff", type=Path, required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.diff.parent.mkdir(parents=True,exist_ok=True)
    original=json.loads(args.input.read_text(encoding="utf-8"))
    result,diff=patch_notebook(original,Path(__file__).with_name("robust_lag.py"))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    args.diff.write_text(diff,encoding="utf-8")
    print("Generated augmented notebook:",args.output)
    print("Original SHA-256:",hashlib.sha256(args.input.read_bytes()).hexdigest())
    print("Output SHA-256:",hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__=="__main__":
    main()
