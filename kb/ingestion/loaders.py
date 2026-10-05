import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceUnit:
    """One citable unit of a source (a PDF page, an ATT&CK technique, ...).

    Chunks derived from this unit all inherit its citation + provenance.
    """

    source_id: str
    source_title: str
    source_url: str
    doc_type: str
    format: str
    unit_key: str          # stable id within the source, e.g. "p14" or "T1055"
    citation: str          # human-readable base citation
    text: str
    extra: dict = field(default_factory=dict)


def load_pdf(path, source_id: str, source_title: str, source_url: str) -> list[SourceUnit]:
    """One SourceUnit per page, so citations carry a page number."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    units: list[SourceUnit] = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        units.append(
            SourceUnit(
                source_id=source_id,
                source_title=source_title,
                source_url=source_url,
                doc_type="standard",
                format="pdf",
                unit_key=f"p{i}",
                citation=f"{source_title}, p.{i}",
                text=text,
                extra={"page": i},
            )
        )
    return units


def load_stix_attack(
    path,
    source_id: str,
    source_title: str,
    limit: int | None = None,
) -> list[SourceUnit]:
    """One SourceUnit per non-deprecated ATT&CK technique (attack-pattern).

    Structured relations (technique -> tactic) are captured in extra for the
    fact store later; here we index the prose description with a citation.
    """
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    units: list[SourceUnit] = []
    for o in bundle.get("objects", []):
        if o.get("type") != "attack-pattern":
            continue
        if o.get("x_mitre_deprecated") or o.get("revoked"):
            continue
        ext = next(
            (r for r in o.get("external_references", []) if r.get("source_name") == "mitre-attack"),
            None,
        )
        tech_id = ext.get("external_id") if ext else None
        desc = (o.get("description") or "").strip()
        name = o.get("name", "")
        if not tech_id or not desc:
            continue
        url = ext.get("url", f"https://attack.mitre.org/techniques/{tech_id}")
        tactics = [
            p.get("phase_name")
            for p in o.get("kill_chain_phases", [])
            if p.get("kill_chain_name") == "mitre-attack"
        ]
        units.append(
            SourceUnit(
                source_id=source_id,
                source_title=source_title,
                source_url=url,
                doc_type="attack-technique",
                format="stix",
                unit_key=tech_id,
                citation=f"MITRE ATT&CK {tech_id}: {name}",
                # Prefix the technique ID so exact-ID queries (e.g. "T1055") match
                # on both the dense and BM25 branches.
                text=f"{tech_id} {name}\n\n{desc}",
                extra={"technique_id": tech_id, "name": name, "tactics": tactics},
            )
        )
        if limit and len(units) >= limit:
            break
    return units
