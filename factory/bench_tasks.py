"""Benchmark-task support for the loop: strip the GT before feeding, and score independently.

This is NOT a loop - it's the data-prep + scoring the ONE solve/retrieve/refine loop
(solve_loop.py) uses for GT-labelled (benchmark) tasks:
  - stage_input : write a description-only input.tsv into the workspace; hold out the GT.
  - build_task  : ask the agent to PREDICT only (write predictions.json); it never sees GT.
  - scorers     : recompute the metric ourselves (F1 / accuracy / CVSS-MAE) vs the held-out GT.

Hiding the GT is the leakage bug-fix; recomputing is how Verify scores these tasks.
"""
import csv
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent.parent
WORKSPACES = ROOT / "workspaces"
CORPUS = ROOT / "benchmarks" / "data"
TSV_URL = "https://raw.githubusercontent.com/xashru/cti-bench/main/data/cti-{}.tsv"


def load_rows(name: str, n: int) -> list[dict]:
    CORPUS.mkdir(parents=True, exist_ok=True)
    p = CORPUS / f"cti-{name}.tsv"
    if not p.exists() or p.stat().st_size < 100:
        subprocess.run(["curl", "-sL", TSV_URL.format(name), "-o", str(p)], check=True, timeout=120)
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    # optional same-distribution scoping (test harness): keep one Platform if the column exists.
    plat = os.getenv("ATE_PLATFORM")
    if plat and rows and "Platform" in rows[0]:
        rows = [r for r in rows if r.get("Platform") == plat]
    return rows[:n]


# ---------------------------------------------------------------------------
# independent scorers  (preds {row_id: prediction}, gts {row_id: gt}) -> dict
# ---------------------------------------------------------------------------
_T = re.compile(r"T\d{4}")


def _tech_set(x: Any) -> set:
    s = " ".join(map(str, x)) if isinstance(x, list) else str(x)
    return {m.group(0) for m in _T.finditer(s)}


def score_ate(preds: dict, gts: dict) -> dict:
    ps, rs, fs = [], [], []
    for rid, gtv in gts.items():
        g = _tech_set(gtv)
        if not g:
            continue
        p = _tech_set(preds.get(rid, ""))
        inter = len(p & g)
        prec = inter / len(p) if p else 0.0
        rec = inter / len(g)
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        ps.append(prec); rs.append(rec); fs.append(f1)
    n = len(fs)
    return {"metric": "avg_F1", "value": round(sum(fs) / n, 3) if n else 0.0,
            "avg_precision": round(sum(ps) / n, 3) if n else 0.0,
            "avg_recall": round(sum(rs) / n, 3) if n else 0.0, "scored_rows": n}


def _mcq_letter(x: Any) -> str:
    s = str(x).strip().upper()
    if s in ("A", "B", "C", "D"):
        return s
    m = re.search(r"\b([ABCD])\b", s)
    return m.group(1) if m else ""


def score_mcq(preds: dict, gts: dict) -> dict:
    correct = n = 0
    for rid, gt in gts.items():
        n += 1
        if _mcq_letter(preds.get(rid, "")) == str(gt).strip().upper():
            correct += 1
    return {"metric": "accuracy_%", "value": round(100 * correct / n, 1) if n else 0.0,
            "correct": correct, "scored_rows": n}


_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}
_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_UI = {"N": 0.85, "R": 0.62}


def _cvss31_base(vector: str) -> float:
    m = {}
    for kv in str(vector).split("/"):
        if ":" in kv and not kv.upper().startswith("CVSS"):
            k, v = kv.split(":", 1)
            m[k] = v
    changed = m.get("S") == "C"
    pr_map = {"N": 0.85, "L": 0.68 if changed else 0.62, "H": 0.5 if changed else 0.27}
    pr = pr_map.get(m.get("PR", "N"), 0.85)
    iss = 1 - (1 - _CIA[m["C"]]) * (1 - _CIA[m["I"]]) * (1 - _CIA[m["A"]])
    impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15 if changed else 6.42 * iss
    expl = 8.22 * _AV[m["AV"]] * _AC[m["AC"]] * pr * _UI[m["UI"]]
    if impact <= 0:
        return 0.0
    return math.ceil(min((1.08 if changed else 1.0) * (impact + expl), 10.0) * 10) / 10.0


def score_vsp(preds: dict, gts: dict) -> dict:
    errs = []
    for rid, gtvec in gts.items():
        try:
            gt_score = _cvss31_base(gtvec)
        except Exception:
            continue
        mt = re.search(r"\d+(?:\.\d+)?", str(preds.get(rid, "")))
        pv = float(mt.group(0)) if mt else 0.0
        errs.append(abs(pv - gt_score))
    n = len(errs)
    return {"metric": "MAE", "value": round(sum(errs) / n, 3) if n else None, "scored_rows": n}


# ---------------------------------------------------------------------------
# per-task config
# ---------------------------------------------------------------------------
@dataclass
class Bench:
    name: str
    input_text: Callable[[dict], str]   # row -> description the agent sees (NO gt)
    gt_value: Callable[[dict], Any]     # row -> held-out gt
    instruction: str                    # what to predict + format (system-agnostic)
    scorer: Callable[[dict, dict], dict]
    higher_better: bool                 # True for F1/accuracy, False for MAE
    solve_hint: str = ""                # solve-only nudge (e.g. "use KB tools"); omitted for deduction


BENCHES = {
    "ate": Bench(
        "ate", lambda r: r["Description"], lambda r: r["GT"],
        "For each row, extract the set of MITRE ATT&CK technique IDs (format T####) that the "
        "description indicates. Your prediction for a row is a list of technique-ID strings.",
        score_ate, True,
        solve_hint="You have KB tools (kb_get, kb_related, search_docs) for ATT&CK - use them."),
    "mcq": Bench(
        "mcq",
        lambda r: f"{r['Question']} | A) {r['Option A']} | B) {r['Option B']} | C) {r['Option C']} | D) {r['Option D']}",
        lambda r: r["GT"],
        "Each row is a multiple-choice question with options A-D in the description. Your "
        "prediction for a row is the single correct option letter (A, B, C, or D).",
        score_mcq, True),
    "vsp": Bench(
        "vsp", lambda r: r["Description"], lambda r: r["GT"],
        "For each row, predict the CVSS v3.1 base score (a number 0.0-10.0) for the vulnerability. "
        "Your prediction for a row is that number.",
        score_vsp, True),  # scored as MAE; direction handled by the loop via higher_better=False below
}
BENCHES["vsp"].higher_better = False


# ---------------------------------------------------------------------------
# stage (strip GT) + task prompt + read predictions
# ---------------------------------------------------------------------------
def stage_input(cfg: Bench, rows: list[dict], task_id: str) -> dict:
    """Write description-only input.tsv into the workspace; return the held-out GT (never staged)."""
    ws = WORKSPACES / task_id
    ws.mkdir(parents=True, exist_ok=True)
    with open(ws / "input.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["row_id", "description"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, cfg.input_text(r).replace("\t", " ").replace("\n", " ")])
    return {i: cfg.gt_value(r) for i, r in enumerate(rows, 1)}


def build_task(cfg: Bench, n: int, solving: bool = False) -> str:
    hint = f" {cfg.solve_hint}" if (solving and cfg.solve_hint) else ""
    return (
        f"You are given a file `input.tsv` in your workspace with columns row_id and description "
        f"({n} rows). {cfg.instruction} There is NO ground truth available to you anywhere - do not "
        f"look for one, download one, or score yourself; only predict from each description. Write "
        f'predictions to `predictions.json` in your workspace as a JSON list of '
        f'{{"row_id": <int>, "prediction": <your prediction>}} objects (one per row). Then call '
        f"final_answer with a one-line summary.{hint}"
    )


def read_predictions(task_id: str) -> dict:
    import json
    p = WORKSPACES / task_id / "predictions.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for item in (data if isinstance(data, list) else []):
        try:
            out[int(item["row_id"])] = item.get("prediction")
        except Exception:
            pass
    return out


def meets(cfg: Bench, value, bar: float) -> bool:
    if value is None:
        return False
    return value >= bar if cfg.higher_better else value <= bar
