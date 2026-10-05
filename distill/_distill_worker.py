"""Subprocess worker: run the distillation pipeline on an accepted trace, in its own process.

Isolated (like _factory_worker / _router_worker) so distill/'s flat modules never collide on
sys.path with factory/kb/router. Prints one line `DISTILL_JSON:{...}` with the report.

Generic by default: the pipeline just turns the accepted trace into a generalized skill and
verifies it with the open-task deduction. For a LABELLED benchmark task (test harness only,
DISTILL_BENCH set) it builds a BenchHook that verifies the induced skill on a HELD-OUT slice
of rows - instances the skill was never induced from - and scores them objectively. So the
skill has to GENERALIZE to the task family; memorizing the trace cannot pass the gate.

usage: python _distill_worker.py <task_id>
env:   DISTILL_ITERS(1) DISTILL_VALIDATE(1) DISTILL_STORE(1)
       DISTILL_BENCH(name) DISTILL_BENCH_N(rows the skill was induced from)
       DISTILL_BENCH_HELDOUT(unseen rows to verify on) DISTILL_BENCH_BAR(gate, e.g. 0.60)
"""
import json
import os
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                     # distill/ : pipeline, deduct, induct, ...
sys.path.insert(0, str(HERE.parent / "factory"))  # factory/ : bench_tasks (test harness only)

from pipeline import distill  # noqa: E402


class BenchHook:
    """Verify an induced skill on a HELD-OUT slice: the rows AFTER the ones it was induced
    from. Stage those rows for the frozen re-solve; score its predictions objectively vs their
    held-out GT. Higher-is-better metrics only (F1/accuracy); direction is asserted so a
    lower-is-better benchmark can't be silently mis-gated."""

    def __init__(self, name: str, seen_n: int, heldout_n: int, bar: float):
        from bench_tasks import BENCHES, build_task, load_rows
        self.cfg = BENCHES[name]
        if not self.cfg.higher_better:
            raise SystemExit(f"BenchHook: {name} is lower-is-better; objective held-out gate not supported yet")
        self.bar = bar
        rows = load_rows(name, seen_n + heldout_n)
        self.rows = rows[seen_n:seen_n + heldout_n]          # unseen: after the induced-from rows
        self.task = build_task(self.cfg, len(self.rows))     # generic task text, NO retrieve nudge
        self._gt: dict = {}

    def stage(self, ded_id: str) -> None:
        from bench_tasks import stage_input
        self._gt[ded_id] = stage_input(self.cfg, self.rows, ded_id)

    def score(self, ded_id: str):
        from bench_tasks import read_predictions
        s = self.cfg.scorer(read_predictions(ded_id), self._gt.get(ded_id, {}))
        val = float(s.get("value") or 0.0)
        note = (f"held-out {s.get('metric')}={val} over {s.get('scored_rows')} UNSEEN rows "
                f"(target >= {self.bar}); prec={s.get('avg_precision')} rec={s.get('avg_recall')}")
        return val, note


class BenchEvaluator:
    """Per-batch tool-free evaluator for the skill OPTIMIZER: stage an arbitrary list of rows and
    score the resulting predictions objectively. Never exposes GT to any LLM."""

    def __init__(self, name: str, bar: float):
        from bench_tasks import BENCHES
        self.cfg = BENCHES[name]
        self.bar = bar
        self._gt: dict = {}

    def task(self, n: int) -> str:
        from bench_tasks import build_task
        return build_task(self.cfg, n)                     # tool-agnostic (no solve hint)

    def input_text(self, rows: list) -> str:
        return "\n".join(f"- {self.cfg.input_text(r)}" for r in rows)

    def stage(self, rows: list, ded_id: str) -> None:
        from bench_tasks import stage_input
        self._gt[ded_id] = stage_input(self.cfg, rows, ded_id)

    def score(self, ded_id: str) -> dict:
        from bench_tasks import read_predictions
        return self.cfg.scorer(read_predictions(ded_id), self._gt.get(ded_id, {}))

    def produced(self, ded_id: str, n: int) -> bool:
        """True if the run wrote predictions for enough rows to count as a real eval (not a failed run)."""
        from bench_tasks import read_predictions
        return len(read_predictions(ded_id)) >= max(1, int(0.6 * n))


if __name__ == "__main__":
    task_id = sys.argv[1]
    bench = os.getenv("DISTILL_BENCH")

    # skill optimization on a benchmark family (test harness)
    if bench and os.getenv("DISTILL_OPTIMIZE", "1") != "0":
        import random
        from bench_tasks import load_rows
        from optimize import optimize_skill
        bar = float(os.getenv("DISTILL_BENCH_BAR", "0.60"))
        seed_n = int(os.getenv("DISTILL_BENCH_N", "10"))          # rows the seed trace was solved on
        opt_n = int(os.getenv("OPT_N", "15"))
        test_n = int(os.getenv("OPT_TEST_N", "15"))
        epochs = int(os.getenv("OPT_EPOCHS", "3"))
        allrows = load_rows(bench, 100000)                        # ATE_PLATFORM filter applies if set
        pool = allrows[seed_n:]                                   # exclude the seed/trained rows
        random.Random(0).shuffle(pool)                            # diverse (not clustered), reproducible
        optimize_rows, test_rows = pool[:opt_n], pool[opt_n:opt_n + test_n]
        evaluator = BenchEvaluator(bench, bar)
        report = optimize_skill(task_id, evaluator, optimize_rows, test_rows, epochs, bar)
        report["mode"] = "textgrad-optimize"
        print("DISTILL_JSON:" + json.dumps(report, default=str))
        sys.exit(0)

    # ---- single-shot distill (optimization disabled / open tasks) ----
    kwargs = {
        "iters": int(os.getenv("DISTILL_ITERS", "1")),
        "validate": os.getenv("DISTILL_VALIDATE", "1") != "0",
        "store": os.getenv("DISTILL_STORE", "1") != "0",
    }
    if bench:
        hook = BenchHook(
            bench,
            seen_n=int(os.getenv("DISTILL_BENCH_N", "10")),
            heldout_n=int(os.getenv("DISTILL_BENCH_HELDOUT", "10")),
            bar=float(os.getenv("DISTILL_BENCH_BAR", "0.60")),
        )
        kwargs["bench_hook"] = hook
        kwargs["outcome_min"] = hook.bar

    report = distill(task_id, **kwargs)
    if bench:
        report["heldout_rows"] = len(kwargs["bench_hook"].rows)
    print("DISTILL_JSON:" + json.dumps(report, default=str))
