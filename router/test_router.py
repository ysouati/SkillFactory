from pathlib import Path

from embeddings import embed_batch
from router import Router
from skills import load_skills
from vector_store import upsert_skill


TEST_CASES = [
    ("extract the key findings from this scientific paper", "pdf-summarize"),
    ("Summerize this paper for me", "pdf-summarize"),
    ("help me tidy up this messy spreadsheet with lots of typos in the addresses", "csv-clean"),
    ("I need a 3-statement financial model for a SaaS startup", "excel-financial-model"),
    ("here's a call recording -- give me the decisions and TODOs", "meeting-notes-structurer"),
    ("what's the severity of CVE-2024-3094 for a Python web app", "cve-triage"),
    ("this security advisory just landed, should we patch immediately", "cve-triage"),
    ("someone reported this suspicious email in our help desk, can you check it", "phishing-email-analysis"),
    ("this message says it's from my bank but the link looks fishy", "phishing-email-analysis"),
    ("I see hundreds of failed SSH logins in auth.log -- is this an attack", "security-log-analysis"),
    ("translate this contract from English to Mandarin", None),
    ("help me schedule a series of tweets for next week", None),
    ("convert this Word document to plain text", None),
    ("write me a firewall configuration policy for our office network", None),
]


def sync_skills(router: Router) -> None:
    """Upsert any seed skills not yet present in the vector store."""
    seed_path = Path(__file__).parent.parent / "skills" / "seed_skills.json"
    skills = load_skills(seed_path)
    existing_ids = {s.skill_id for s in router.list_skills()}
    missing = [s for s in skills if s.id not in existing_ids]
    if not missing:
        return
    vecs = embed_batch([s.description for s in missing])
    for skill, vec in zip(missing, vecs):
        upsert_skill(router.store, skill.id, skill.name, skill.description, vec)
    print(f"Synced {len(missing)} new skill(s) into the index (total: {len(skills)}).\n")


def main() -> None:
    router = Router()
    sync_skills(router)

    passed = 0
    print(f"{'result':<7} {'expected':<28} {'got':<28} score  task")
    print("-" * 110)
    for task, expected in TEST_CASES:
        decision = router.route(task)
        got = decision.matched_skill_id if decision.action == "use_skill" else "<build>"
        expected_str = expected if expected else "<build>"
        ok = (got == expected_str) or (expected is None and decision.action == "build")
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"{status:<7} {expected_str:<28} {got:<28} {decision.top_score:.3f}  {task[:60]}")

    print("-" * 110)
    print(f"\n{passed}/{len(TEST_CASES)} passed")

    print("\n--- Detailed reasoning ---")
    for task, expected in TEST_CASES:
        decision = router.route(task)
        print(f"\ntask: {task!r}")
        print(f"  action={decision.action}  matched={decision.matched_skill_id}")
        if decision.early_exit_reason:
            print(f"  early exit: {decision.early_exit_reason}")
        if decision.judgment:
            print(f"  reason: {decision.judgment.reason}")

    router.close()


if __name__ == "__main__":
    main()
