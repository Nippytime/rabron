"""Identify only five original city-scene field-capped Unity objects.

Never export numeric values, media, or arbitrary object text. Original UnityFS
source identity and complete aggregate object accounting are mandatory.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.validate_source_inventory import validate_object_identities
from reconstruction.tools.verify_priority_lfs import verify_source

CITY = ("StreamingAssets/aa/StandaloneWindows64/"
        "location-city-standalone_scenes_city_standalone.unity.bundle")
SHA = "5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f"
GIT_SHA = "c73e7b84edc6b4e73001923054ff3a29bd540393"
BYTES = 549_566_135
FIELDS = 2048
DEPTH = 32
CAPS = 5
MONOS = 14467
TOTAL_OBJECTS = 366174
REF = Path("reconstruction/data/city_scene_numeric_cap_identities.json")


def evidence(ledger):
    scans = ledger.get("scans", [])
    if ledger.get("schema_version") != 1 or len(scans) != 330:
        raise ValueError("The 330/330 original evidence ledger is required")
    matches = [row for row in scans if row.get("bundle") == CITY]
    if len(matches) != 1:
        raise ValueError("Exactly one original city scan is required")
    row = matches[0]
    expected = {
        "sha256": SHA, "lfs_oid_sha256": SHA, "git_blob_sha": GIT_SHA,
        "size_bytes": BYTES, "numeric_field_limit": FIELDS,
        "numeric_depth_limit": DEPTH, "numeric_field_cap_records": CAPS,
        "monobehaviours_total": MONOS, "monobehaviours_parsed": MONOS,
        "unparsed_records": 0, "bounded_numeric_scan_complete": False,
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise ValueError("Original city fingerprint or measured caps differ")
    types = row.get("objects_by_type")
    if not isinstance(types, dict) or sum(types.values()) != TOTAL_OBJECTS:
        raise ValueError("Original city object accounting differs")
    if types.get("MonoBehaviour") != MONOS:
        raise ValueError("Original city MonoBehaviour count differs")
    return row


def build_index(raw, measured):
    """Validate the *whole* existing bounded scan before emitting five IDs."""
    expected = {
        "source": CITY, "sha256": SHA, "size_bytes": BYTES,
        "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
        "monobehaviours_total": MONOS, "monobehaviours_attempted": MONOS,
        "monobehaviours_parsed": MONOS, "limit_reached": False,
        "complete_numeric_extraction": False, "unityfs_magic": True,
        "selected_path_ids": None, "missing_path_ids": [],
        "objects_by_type": measured["objects_by_type"],
    }
    if any(raw.get(key) != value for key, value in expected.items()):
        raise ValueError("City source or entire bounded object scan differs")
    records = raw.get("records")
    if not isinstance(records, list) or len(records) != MONOS:
        raise ValueError("Incomplete city MonoBehaviour record list")
    validate_object_identities(records)
    if any(rec.get("status") != "parsed" for rec in records):
        raise ValueError("Original city has an unparsed MonoBehaviour")
    capped = []
    for rec in records:
        reasons = rec.get("numeric_truncation_reasons")
        if (not isinstance(reasons, list) or
                any(x not in ("field_limit", "depth_limit") for x in reasons) or
                rec.get("fields_truncated") is not bool(reasons)):
            raise ValueError("Contradictory numeric truncation accounting")
        if not reasons:
            continue
        scope = rec.get("serialized_file")
        path_id = rec.get("path_id")
        name = rec.get("name")
        fields = rec.get("numeric_fields")
        if (not isinstance(scope, str) or not scope.strip() or
                not isinstance(path_id, str) or
                not re.fullmatch(r"-?[0-9]+", path_id) or
                not isinstance(name, str) or
                not isinstance(fields, list) or len(fields) > FIELDS):
            raise ValueError("Capped object lacks scoped identity or bound")
        capped.append({
            "serialized_file": scope,
            "path_id": path_id,
            "display_name": name[:96],
            "truncation_reasons": reasons,
            "visible_numeric_field_count": len(fields),
            "status": "capped",
        })
    if len(capped) != CAPS:
        raise ValueError("Five original city caps did not reproduce")
    capped.sort(key=lambda x: (x["serialized_file"], int(x["path_id"])))
    return {
        "schema_version": 1, "bundle": CITY, "source_sha256": SHA,
        "size_bytes": BYTES, "object_count": TOTAL_OBJECTS,
        "monobehaviours_total": MONOS, "field_limit": FIELDS,
        "depth_limit": DEPTH, "capped_count": CAPS,
        "unparsed_count": 0, "full_numeric_extraction_complete": False,
        "scope": "scoped object identities only; no original values, game formulas or media",
        "capped_objects": capped,
    }


def verify_index(index, measured):
    """Fail closed on incomplete, forged, reordered, or duplicate evidence."""
    if not isinstance(index, dict):
        raise ValueError("Missing city cap index")
    expected = {
        "schema_version": 1, "bundle": CITY, "source_sha256": SHA,
        "size_bytes": BYTES, "object_count": TOTAL_OBJECTS,
        "monobehaviours_total": MONOS, "field_limit": FIELDS,
        "depth_limit": DEPTH, "capped_count": CAPS,
        "unparsed_count": 0, "full_numeric_extraction_complete": False,
        "scope": "scoped object identities only; no original values, game formulas or media",
    }
    if set(index) != set(expected) | {"capped_objects"} or any(
            index.get(k) != v for k, v in expected.items()):
        raise ValueError("Original city cap index metadata mismatch")
    if measured["numeric_field_cap_records"] != CAPS:
        raise ValueError("Original source baseline changed")
    rows = index.get("capped_objects")
    if not isinstance(rows, list) or len(rows) != CAPS:
        raise ValueError("Five original capped records required")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                "serialized_file", "path_id", "display_name",
                "truncation_reasons", "visible_numeric_field_count", "status"}:
            raise ValueError("Incomplete capped object identity")
        scope, pid = row["serialized_file"], row["path_id"]
        identity = (scope, pid)
        if (not isinstance(scope, str) or not scope.strip() or
                not isinstance(pid, str) or not re.fullmatch(r"-?[0-9]+", pid) or
                identity in seen or
                not isinstance(row["display_name"], str) or
                len(row["display_name"]) > 96 or
                row["status"] != "capped" or
                type(row["visible_numeric_field_count"]) is not int or
                not 0 <= row["visible_numeric_field_count"] <= FIELDS or
                not isinstance(row["truncation_reasons"], list) or
                not row["truncation_reasons"] or
                any(reason not in ("field_limit", "depth_limit")
                    for reason in row["truncation_reasons"])):
            raise ValueError("Invalid or duplicate capped source identity")
        seen.add(identity)
    if rows != sorted(rows, key=lambda x: (x["serialized_file"], int(x["path_id"]))):
        raise ValueError("City cap evidence must have deterministic ordering")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "scan", "reconcile"))
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--index", type=Path)
    args = parser.parse_args()

    measured = evidence(json.loads(args.ledger.read_text(encoding="utf-8")))
    source = {"bundle": CITY, "lfs_oid_sha256": SHA, "size_bytes": BYTES}
    reference = json.loads(REF.read_text(encoding="utf-8")) if REF.exists() else None
    if reference is not None:
        verify_index(reference, measured)
    mode = "recheck" if reference is not None else "new"

    if args.command == "plan":
        verify_source(Path(CITY), source, phase="pointer")
        pointer_sha = subprocess.check_output(
            ["git", "hash-object", CITY], text=True,
        ).strip()
        if pointer_sha != GIT_SHA:
            raise ValueError("Original Git LFS pointer blob SHA-1 differs")
        print("CITY_CAP_PLAN=" + json.dumps({"mode": mode, "original_caps": CAPS,
                                             "sha256": SHA}, sort_keys=True))
        return

    if args.command == "scan":
        if args.output is None:
            parser.error("scan requires --output")
        verify_source(Path(CITY), source, phase="bytes")
        from reconstruction.tools.streamed_unityfs import (
            MAX_CITY_MONO_OBJECT_BYTES, streamed_unityfs,
        )
        with streamed_unityfs(scope="CITY", skip_container_index=False,
                              mono_budget_bytes=MAX_CITY_MONO_OBJECT_BYTES):
            raw = scan_bundle(Path(CITY), max_fields=FIELDS, max_depth=DEPTH,
                              expected_sha256=SHA)
        report = build_index(raw, measured)
        verify_index(report, measured)
        if reference is not None and report != reference:
            raise ValueError("Latest-head original city capped identities changed")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) +
                               "\n", encoding="utf-8")
        print("CITY_CAP_INDEX=" + json.dumps({
            "mode": mode, "capped_count": CAPS,
            "scoped_ids": [(x["serialized_file"], x["path_id"])
                           for x in report["capped_objects"]],
            "full_numeric_extraction_complete": False,
        }, sort_keys=True))
        return

    if args.index is None:
        parser.error("reconcile requires --index")
    report = json.loads(args.index.read_text(encoding="utf-8"))
    verify_index(report, measured)
    if reference is not None and report != reference:
        raise ValueError("Evidence differs from committed original cap IDs")
    print("CITY_CAP_SUMMARY=" + json.dumps({
        "mode": mode, "capped_count": CAPS, "indexed": len(report["capped_objects"]),
        "source_verified": True, "full_numeric_extraction_complete": False,
        "reverified": CAPS if reference is not None else 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
