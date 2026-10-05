"""Load the MITRE CWE catalog into the fact store (entities + hierarchy) and the
prose store (definitions). This is reference knowledge (weakness taxonomy), NOT
CVE->CWE answers - the benchmark ground truth is never loaded.
"""
import io
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Allow importing the shared kb/ runtime modules (stores) and sibling ingest/loaders
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import CORPUS_DIR, ingest_units
from loaders import SourceUnit
from stores import ensure_prose_collection, get_fact_db, get_vector_client

CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"
SOURCE_ID = "cwe-catalog"


def download_cwe() -> Path:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    xml_path = CORPUS_DIR / "cwec_latest.xml"
    if xml_path.exists() and xml_path.stat().st_size > 0:
        return xml_path
    zip_path = CORPUS_DIR / "cwec_latest.xml.zip"
    subprocess.run(["curl", "-sL", CWE_URL, "-o", str(zip_path)], check=True, timeout=120)
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.endswith(".xml"))
        xml_path.write_bytes(z.read(name))
    return xml_path


def parse_cwe(xml_path: Path) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    ns = {"c": root.tag[root.tag.find("{") + 1 : root.tag.find("}")]}
    out: list[dict] = []
    for w in root.findall("c:Weaknesses/c:Weakness", ns):
        wid = w.get("ID")
        desc_el = w.find("c:Description", ns)
        ext_el = w.find("c:Extended_Description", ns)
        desc = "".join(desc_el.itertext()).strip() if desc_el is not None else ""
        ext = "".join(ext_el.itertext()).strip() if ext_el is not None else ""
        parents = [
            rw.get("CWE_ID")
            for rw in w.findall("c:Related_Weaknesses/c:Related_Weakness", ns)
            if rw.get("Nature") == "ChildOf"
        ]
        out.append({
            "id": wid,
            "name": w.get("Name", ""),
            "abstraction": w.get("Abstraction", ""),
            "status": w.get("Status", ""),
            "description": desc,
            "extended": ext,
            "parents": parents,
        })
    return out


def ingest_cwe_facts(db, weaknesses: list[dict]) -> dict:
    entities, attributes, relations = [], [], []
    for w in weaknesses:
        eid = f"CWE-{w['id']}"
        entities.append((eid, "cwe", w["name"], w["description"][:400], SOURCE_ID))
        if w["abstraction"]:
            attributes.append((eid, "abstraction", w["abstraction"]))
        for parent in w["parents"]:
            relations.append((eid, "child-of", f"CWE-{parent}"))
    db.executemany(
        "INSERT OR REPLACE INTO entities (entity_id, entity_type, name, summary, source_id) VALUES (?,?,?,?,?)",
        entities,
    )
    db.executemany("INSERT OR IGNORE INTO attributes (entity_id, key, value) VALUES (?,?,?)", attributes)
    db.executemany("INSERT OR IGNORE INTO relations (src_id, rel_type, dst_id) VALUES (?,?,?)", relations)
    db.commit()
    return {"entities": len(entities), "attributes": len(attributes), "relations": len(relations)}


def cwe_prose_units(weaknesses: list[dict]) -> list[SourceUnit]:
    units = []
    for w in weaknesses:
        eid = f"CWE-{w['id']}"
        body = f"{eid} {w['name']}\n\n{w['description']}"
        if w["extended"]:
            body += f"\n\n{w['extended']}"
        units.append(SourceUnit(
            source_id=SOURCE_ID,
            source_title="MITRE CWE",
            source_url=f"https://cwe.mitre.org/data/definitions/{w['id']}.html",
            doc_type="cwe",
            format="xml",
            unit_key=eid,
            citation=f"{eid}: {w['name']}",
            text=body,
            extra={"cwe_id": eid, "abstraction": w["abstraction"]},
        ))
    return units


if __name__ == "__main__":
    xml_path = download_cwe()
    weaknesses = parse_cwe(xml_path)
    print(f"Parsed {len(weaknesses)} CWE weaknesses.")

    client = get_vector_client()
    ensure_prose_collection(client)
    db = get_fact_db()

    fstats = ingest_cwe_facts(db, weaknesses)
    print(f"Fact store: {fstats}")

    units = cwe_prose_units(weaknesses)
    n = ingest_units(units, xml_path, client, db, force=True)
    print(f"Prose store: {n} CWE chunks ingested")

    client.close()
    db.close()
