"""Generic, source-agnostic query API over the structured KB.

The agent decides *what* to look up; these verbs guarantee EXACT (SQL) matching,
never semantic. Works identically for ATT&CK, CWE, CVE, or any future source that
loads into the entities / attributes / relations schema.
"""
import sqlite3
from typing import Optional


def entity_types(db: sqlite3.Connection) -> list[dict]:
    """What kinds of structured entities exist, and how many of each."""
    rows = db.execute(
        "SELECT entity_type, COUNT(*) AS n FROM entities GROUP BY entity_type ORDER BY n DESC"
    ).fetchall()
    return [{"entity_type": r["entity_type"], "count": r["n"]} for r in rows]


def dump_type(db: sqlite3.Connection, entity_type: str, limit: int = 5000) -> list[dict]:
    """Every entity of a type with id/name/summary - for assembling a COMPREHENSIVE catalog
    (the whole knowledge domain, not a sample) to bake into a portable skill."""
    rows = db.execute(
        "SELECT entity_id, name, summary FROM entities WHERE entity_type = ? ORDER BY entity_id LIMIT ?",
        (entity_type, limit),
    ).fetchall()
    return [{"entity_id": r["entity_id"], "name": r["name"], "summary": r["summary"] or ""} for r in rows]


def get_entity(db: sqlite3.Connection, entity_id: str) -> Optional[dict]:
    """Exact fetch by id, with all attributes and both directions of relations."""
    row = db.execute(
        "SELECT entity_id, entity_type, name, summary, source_id FROM entities WHERE entity_id = ?",
        (entity_id,),
    ).fetchone()
    if row is None:
        return None

    attrs: dict[str, list[str]] = {}
    for a in db.execute("SELECT key, value FROM attributes WHERE entity_id = ?", (entity_id,)):
        attrs.setdefault(a["key"], []).append(a["value"])

    out = [
        {"rel_type": r["rel_type"], "id": r["dst_id"], "name": r["name"]}
        for r in db.execute(
            "SELECT rel.rel_type, rel.dst_id, e.name FROM relations rel "
            "LEFT JOIN entities e ON e.entity_id = rel.dst_id WHERE rel.src_id = ? "
            "ORDER BY rel.rel_type",
            (entity_id,),
        )
    ]
    inc = [
        {"rel_type": r["rel_type"], "id": r["src_id"], "name": r["name"]}
        for r in db.execute(
            "SELECT rel.rel_type, rel.src_id, e.name FROM relations rel "
            "LEFT JOIN entities e ON e.entity_id = rel.src_id WHERE rel.dst_id = ? "
            "ORDER BY rel.rel_type",
            (entity_id,),
        )
    ]
    return {
        "entity_id": row["entity_id"],
        "entity_type": row["entity_type"],
        "name": row["name"],
        "summary": row["summary"],
        "source_id": row["source_id"],
        "attributes": attrs,
        "relations_out": out,
        "relations_in": inc,
    }


def find_entities(
    db: sqlite3.Connection,
    entity_type: Optional[str] = None,
    name: Optional[str] = None,
    name_contains: Optional[str] = None,
    attr_key: Optional[str] = None,
    attr_value: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Find entities by exact fields. All filters are ANDed; all exact except
    name_contains (case-insensitive substring, still deterministic)."""
    where = []
    params: list = []
    joins = ""
    if attr_key is not None or attr_value is not None:
        joins = "JOIN attributes a ON a.entity_id = e.entity_id"
        if attr_key is not None:
            where.append("a.key = ?")
            params.append(attr_key)
        if attr_value is not None:
            where.append("a.value = ?")
            params.append(attr_value)
    if entity_type is not None:
        where.append("e.entity_type = ?")
        params.append(entity_type)
    if name is not None:
        where.append("e.name = ?")
        params.append(name)
    if name_contains is not None:
        where.append("e.name LIKE ?")
        params.append(f"%{name_contains}%")

    sql = f"SELECT DISTINCT e.entity_id, e.entity_type, e.name FROM entities e {joins}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY e.entity_id LIMIT ?"
    params.append(limit)

    return [
        {"entity_id": r["entity_id"], "entity_type": r["entity_type"], "name": r["name"]}
        for r in db.execute(sql, params)
    ]


def related(
    db: sqlite3.Connection,
    entity_id: str,
    rel_type: Optional[str] = None,
    direction: str = "both",
    limit: int = 100,
) -> list[dict]:
    """Traverse relations from/to an entity. direction: 'out', 'in', or 'both'."""
    results: list[dict] = []
    if direction in ("out", "both"):
        sql = (
            "SELECT rel.rel_type, rel.dst_id AS id, e.entity_type, e.name FROM relations rel "
            "LEFT JOIN entities e ON e.entity_id = rel.dst_id WHERE rel.src_id = ?"
        )
        params: list = [entity_id]
        if rel_type:
            sql += " AND rel.rel_type = ?"
            params.append(rel_type)
        sql += " LIMIT ?"
        params.append(limit)
        for r in db.execute(sql, params):
            results.append({"direction": "out", "rel_type": r["rel_type"], "id": r["id"],
                            "entity_type": r["entity_type"], "name": r["name"]})
    if direction in ("in", "both"):
        sql = (
            "SELECT rel.rel_type, rel.src_id AS id, e.entity_type, e.name FROM relations rel "
            "LEFT JOIN entities e ON e.entity_id = rel.src_id WHERE rel.dst_id = ?"
        )
        params = [entity_id]
        if rel_type:
            sql += " AND rel.rel_type = ?"
            params.append(rel_type)
        sql += " LIMIT ?"
        params.append(limit)
        for r in db.execute(sql, params):
            results.append({"direction": "in", "rel_type": r["rel_type"], "id": r["id"],
                            "entity_type": r["entity_type"], "name": r["name"]})
    return results
