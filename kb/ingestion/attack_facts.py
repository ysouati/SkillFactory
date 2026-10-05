"""Map MITRE ATT&CK STIX into the generic entities/attributes/relations schema.

Per-source loader (STIX is ATT&CK-specific), but it writes into the uniform store
so the agent queries it with the same generic verbs as any other source.
"""
import json
import sys
from pathlib import Path

# Allow importing the shared kb/ runtime modules (stores) and sibling ingest.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# STIX SDO type -> our generic entity_type
_TYPE_MAP = {
    "attack-pattern": "attack-technique",
    "x-mitre-tactic": "attack-tactic",
    "intrusion-set": "attack-group",
    "malware": "attack-software",
    "tool": "attack-software",
    "course-of-action": "attack-mitigation",
    "campaign": "attack-campaign",
}


def _external_id(obj) -> str | None:
    for r in obj.get("external_references", []):
        if r.get("source_name") == "mitre-attack" and r.get("external_id"):
            return r["external_id"]
    return None


def ingest_attack_facts(json_path, db, source_id: str = "mitre-attack-enterprise") -> dict:
    bundle = json.loads(Path(json_path).read_text(encoding="utf-8"))
    objects = bundle.get("objects", [])

    stix_to_ext: dict[str, str] = {}   # STIX uuid -> external id (T####, TA####, ...)
    shortname_to_tactic: dict[str, str] = {}
    entities: list[tuple] = []
    attributes: list[tuple] = []

    # Pass 1 - entities + attributes, build id maps
    for o in objects:
        etype = _TYPE_MAP.get(o.get("type"))
        if not etype:
            continue
        if o.get("revoked") or o.get("x_mitre_deprecated"):
            continue
        ext = _external_id(o)
        if not ext:
            continue
        stix_to_ext[o["id"]] = ext
        name = o.get("name", "")
        summary = (o.get("description") or "").strip()[:400]
        entities.append((ext, etype, name, summary, source_id))

        if o.get("type") == "x-mitre-tactic":
            sn = o.get("x_mitre_shortname")
            if sn:
                shortname_to_tactic[sn] = ext
                attributes.append((ext, "shortname", sn))
        for plat in o.get("x_mitre_platforms", []) or []:
            attributes.append((ext, "platform", plat))
        if o.get("x_mitre_is_subtechnique"):
            attributes.append((ext, "is_subtechnique", "true"))

    relations: set[tuple] = set()

    # technique -> tactic, via kill_chain_phases (phase_name == tactic shortname)
    for o in objects:
        if o.get("type") != "attack-pattern":
            continue
        ext = stix_to_ext.get(o.get("id"))
        if not ext:
            continue
        for phase in o.get("kill_chain_phases", []):
            if phase.get("kill_chain_name") == "mitre-attack":
                tac = shortname_to_tactic.get(phase.get("phase_name"))
                if tac:
                    relations.add((ext, "achieves-tactic", tac))

    # Pass 2 - STIX relationship objects -> generic relations
    for o in objects:
        if o.get("type") != "relationship":
            continue
        src = stix_to_ext.get(o.get("source_ref"))
        dst = stix_to_ext.get(o.get("target_ref"))
        if not src or not dst:
            continue  # ref points to something we didn't index (e.g. data component)
        rel = o.get("relationship_type", "related")
        relations.add((src, rel, dst))

    # Bulk write (idempotent via INSERT OR REPLACE / OR IGNORE)
    db.executemany(
        "INSERT OR REPLACE INTO entities (entity_id, entity_type, name, summary, source_id) "
        "VALUES (?,?,?,?,?)",
        entities,
    )
    db.executemany(
        "INSERT OR IGNORE INTO attributes (entity_id, key, value) VALUES (?,?,?)",
        attributes,
    )
    db.executemany(
        "INSERT OR IGNORE INTO relations (src_id, rel_type, dst_id) VALUES (?,?,?)",
        list(relations),
    )
    db.commit()
    return {"entities": len(entities), "attributes": len(attributes), "relations": len(relations)}


if __name__ == "__main__":
    from stores import get_fact_db
    from ingest import CORPUS_DIR, download

    attack_json = download(
        "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
        CORPUS_DIR / "enterprise-attack.json",
    )
    db = get_fact_db()
    stats = ingest_attack_facts(attack_json, db)
    print(f"Loaded ATT&CK facts: {stats}")
    db.close()
