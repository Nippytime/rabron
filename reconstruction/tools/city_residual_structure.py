"""Read-only original city residual numeric-cap shape diagnosis.

Record only serialized member *names*, primitive kinds and container lengths.
Never export numeric values, serialized text, renderer IDs, media, or gameplay
formulas. This diagnostic cannot resolve any existing numeric cap.
"""
import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from reconstruction.tools.city_cap_index import (
    BYTES, CITY, GIT_SHA, MONOS, REF, SHA, TOTAL_OBJECTS, evidence, verify_index,
)
from reconstruction.tools.city_targeted_numeric_retry import (
    REPORT as RETRY_REF, verify_report,
)
from reconstruction.tools.streamed_unityfs import MAX_CITY_MONO_OBJECT_BYTES
from reconstruction.tools.verify_priority_lfs import verify_source

REPORT = Path("reconstruction/data/city_residual_structure.json")
ROOT_FIELDS = 64
MEMBER_NAMES = 8
SCOPE = "serialized member names, kinds and lengths only; no values, game formulas or media"
ROOT_TYPES = {"object", "array", "integer", "float", "bool", "text", "null", "other"}
EXPECTED_IDS = (
    ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344196"),
    ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344248"),
    ("CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets", "7968"),
)


def targets(index, retry):
    """The three still-capped identities, never the two resolved records."""
    selected = {tuple((item["serialized_file"], item["path_id"]))
                for item in index["capped_objects"]}
    remaining = tuple((item["serialized_file"], item["path_id"])
                      for item in retry["outcomes"] if item["status"] == "still_capped")
    if remaining != EXPECTED_IDS or not set(remaining) <= selected:
        raise ValueError("Residual original-city numeric cap identities changed")
    return remaining


def kind(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "text"
    return "other"


def member_names(value):
    if not isinstance(value, dict):
        return []
    names = list(value)
    if any(type(name) is not str or not name or len(name) > 120 for name in names):
        raise ValueError("Unexpected serialized member-name identity")
    return sorted(names)


def summarize(parsed):
    """Bound output, not the original parser's 8 MiB object safety budget."""
    names = member_names(parsed)
    fields = []
    for name in names[:ROOT_FIELDS]:
        value = parsed[name]
        value_kind = kind(value)
        count = len(value) if value_kind in ("array", "object") else None
        first_keys = []
        if value_kind == "array" and value:
            first_keys = member_names(value[0])[:MEMBER_NAMES]
        fields.append({
            "field": name, "kind": value_kind,
            "element_count": count, "first_element_members": first_keys,
        })
    return {
        "root_member_count": len(names),
        "root_member_names_truncated": len(names) > ROOT_FIELDS,
        "fields": fields,
    }


def scan_city(measured, wanted, *, loader=None):
    """Parse exactly three selected MonoBehaviours and count all source headers."""
    if loader is None:
        import UnityPy
        from UnityPy.helpers import TypeTreeHelper
        TypeTreeHelper.read_typetree_boost = False
        loader = UnityPy.load
    env = loader(str(CITY))
    counts = Counter()
    observed = {}
    for reader in env.objects:
        counts[reader.type.name] += 1
        if reader.type.name != "MonoBehaviour":
            continue
        identity = (getattr(getattr(reader, "assets_file", None), "name", None),
                    str(reader.path_id))
        if identity not in wanted:
            continue
        if identity in observed:
            raise ValueError("Duplicate selected original city object")
        size = getattr(reader, "byte_size", None)
        if type(size) is not int or not 0 < size <= MAX_CITY_MONO_OBJECT_BYTES:
            raise ValueError("Original city object exceeds fixed 8 MiB parse budget")
        parsed = reader.parse_as_dict()
        observed[identity] = {
            "serialized_file": identity[0],
            "path_id": identity[1],
            "object_byte_size": size,
            **summarize(parsed),
        }
    if dict(counts) != measured["objects_by_type"] or counts["MonoBehaviour"] != MONOS:
        raise ValueError("Source-wide city object inventory changed")
    if set(observed) != set(wanted):
        raise ValueError("Missing selected original city object")
    return {
        "schema_version": 1,
        "source": CITY,
        "source_sha256": SHA,
        "size_bytes": BYTES,
        "source_object_count": TOTAL_OBJECTS,
        "source_monobehaviours": MONOS,
        "selected_count": len(wanted),
        "numeric_caps_resolved": 0,
        "numeric_extraction_complete": False,
        "scope": SCOPE,
        "outcomes": [observed[key] for key in wanted],
    }


def verify_report(report, wanted):
    expected = {
        "schema_version": 1, "source": CITY, "source_sha256": SHA,
        "size_bytes": BYTES, "source_object_count": TOTAL_OBJECTS,
        "source_monobehaviours": MONOS, "selected_count": 3,
        "numeric_caps_resolved": 0, "numeric_extraction_complete": False,
        "scope": SCOPE,
    }
    if (type(report) is not dict or set(report) != set(expected) | {"outcomes"}
            or any(report.get(key) != value for key, value in expected.items())):
        raise ValueError("Source metadata or incomplete numeric status differs")
    rows = report.get("outcomes")
    if type(rows) is not list or len(rows) != 3 or tuple(
        (row.get("serialized_file"), row.get("path_id"))
        for row in rows if type(row) is dict) != wanted:
        raise ValueError("Selected city structure identities missing or reordered")
    for row in rows:
        if type(row) is not dict or set(row) != {
                "serialized_file", "path_id", "object_byte_size",
                "root_member_count", "root_member_names_truncated", "fields"}:
            raise ValueError("Unexpected source structure fields")
        total, partial, fields = (row["root_member_count"],
                                  row["root_member_names_truncated"], row["fields"])
        if (type(row["object_byte_size"]) is not int or
                not 0 < row["object_byte_size"] <= MAX_CITY_MONO_OBJECT_BYTES or
                type(total) is not int or total < 0 or
                type(partial) is not bool or
                type(fields) is not list or len(fields) != min(total, ROOT_FIELDS) or
                partial is not (total > ROOT_FIELDS)):
            raise ValueError("Invalid or incomplete top-level object shape")
        names = []
        for field in fields:
            if type(field) is not dict or set(field) != {
                    "field", "kind", "element_count", "first_element_members"}:
                raise ValueError("Unexpected serialized structure datum")
            name, category = field["field"], field["kind"]
            count, children = field["element_count"], field["first_element_members"]
            if (type(name) is not str or not name or len(name) > 120 or
                    category not in ROOT_TYPES or
                    (category in ("array", "object")) is not (type(count) is int) or
                    (type(count) is int and count < 0) or
                    type(children) is not list or len(children) > MEMBER_NAMES or
                    any(type(c) is not str or not c or len(c) > 120 for c in children) or
                    children != sorted(set(children)) or
                    (category != "array" and children)):
                raise ValueError("Invalid original structural metadata")
            names.append(name)
        if names != sorted(set(names)):
            raise ValueError("Duplicate or non-deterministic root member names")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "scan", "reconcile"))
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    measured = evidence(json.loads(args.ledger.read_text(encoding="utf-8")))
    index = json.loads(REF.read_text(encoding="utf-8"))
    retry = json.loads(RETRY_REF.read_text(encoding="utf-8"))
    verify_index(index, measured)
    from reconstruction.tools.city_targeted_numeric_retry import verify_report as verify_retry
    verify_retry(retry, index)
    wanted = targets(index, retry)
    previous = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else None
    if previous is not None:
        verify_report(previous, wanted)
    mode = "recheck" if previous is not None else "new"
    source = {"bundle": CITY, "lfs_oid_sha256": SHA, "size_bytes": BYTES}

    if args.command == "plan":
        verify_source(Path(CITY), source, phase="pointer")
        pointer = subprocess.check_output(["git", "hash-object", CITY], text=True).strip()
        if pointer != GIT_SHA:
            raise ValueError("City original pointer Git SHA-1 changed")
        print("CITY_SHAPE_PLAN=" + json.dumps({"mode": mode, "targets": 3},
                                             sort_keys=True))
        return
    if args.command == "scan":
        if args.output is None:
            parser.error("scan requires --output")
        verify_source(Path(CITY), source, phase="bytes")
        from reconstruction.tools.streamed_unityfs import streamed_unityfs
        with streamed_unityfs(scope="CITY", skip_container_index=False,
                              mono_budget_bytes=MAX_CITY_MONO_OBJECT_BYTES):
            report = scan_city(measured, wanted)
        verify_report(report, wanted)
        if previous is not None and report != previous:
            raise ValueError("Source structure differs from committed evidence")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
        print("CITY_SHAPE_RESULT=" + json.dumps({
            "mode": mode, "selected": len(report["outcomes"]),
            "numeric_caps_resolved": 0, "numeric_extraction_complete": False,
        }, sort_keys=True))
        return
    if args.result is None:
        parser.error("reconcile requires --result")
    report = json.loads(args.result.read_text(encoding="utf-8"))
    verify_report(report, wanted)
    if previous is not None and report != previous:
        raise ValueError("Measured city shape does not match committed evidence")
    print("CITY_SHAPE_SUMMARY=" + json.dumps({
        "mode": mode, "verified_identities": len(report["outcomes"]),
        "reverified": len(report["outcomes"]) if previous is not None else 0,
        "numeric_caps_resolved": 0, "numeric_extraction_complete": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
