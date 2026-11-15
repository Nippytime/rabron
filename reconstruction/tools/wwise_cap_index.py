"""Record original Wwise scoped cap IDs without exporting numeric values/media."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.verify_priority_lfs import verify_source

BUNDLE = "StreamingAssets/aa/StandaloneWindows64/wwisedata_windows_assets_all.bundle"
SHA = "d84888fe94f74b5cb817749abbcb1af59225300523ad9a1a14e01f475e08fb35"
POINTER = "40324cc5a4281d764319e2291e9fb7c142208c57"
BYTES = 170634407
MONOS, PARSED, CAPS, UNPARSED = 275, 274, 274, 1
FIELDS, DEPTH = 2048, 32
INDEX = Path("reconstruction/data/wwise_numeric_cap_identities.json")
SCOPE = "source-scoped Wwise IDs and numeric path digests; no values, media or original formulas"


def evidence(ledger):
    scans = ledger.get("scans")
    if ledger.get("schema_version") != 1 or not isinstance(scans, list) or len(scans) != 330:
        raise ValueError("Exactly 330 documented original sources required")
    matches = [x for x in scans if x.get("bundle") == BUNDLE]
    if len(matches) != 1:
        raise ValueError("Missing or duplicated original Wwise source")
    row = matches[0]
    expected = {
        "git_blob_sha": POINTER, "lfs_oid_sha256": SHA,
        "sha256": SHA, "size_bytes": BYTES,
        "monobehaviours_total": MONOS, "monobehaviours_parsed": PARSED,
        "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
        "numeric_field_cap_records": CAPS, "unparsed_records": UNPARSED,
        "bounded_numeric_scan_complete": False,
        "objects_by_type": {"AssetBundle": 1, "MonoBehaviour": MONOS},
    }
    if any(row.get(k) != v for k, v in expected.items()):
        raise ValueError("Original Wwise SHA, limits or object ledger mismatch")
    return row


def scoped(row):
    file, pid = row.get("serialized_file"), row.get("path_id")
    if (not isinstance(file, str) or not file.strip() or
            not isinstance(pid, str) or not re.fullmatch(r"-?[0-9]+", pid)):
        raise ValueError("Missing Wwise serialized-file/path ID")
    return file, pid


def build(raw, source):
    expected = {
        "source": BUNDLE, "sha256": SHA, "size_bytes": BYTES,
        "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
        "unityfs_magic": True, "objects_by_type": source["objects_by_type"],
        "monobehaviours_total": MONOS, "monobehaviours_attempted": MONOS,
        "monobehaviours_parsed": PARSED, "limit_reached": False,
        "selected_path_ids": None, "missing_path_ids": [],
        "complete_numeric_extraction": False,
    }
    if any(raw.get(k) != v for k, v in expected.items()):
        raise ValueError("Bounded Wwise source scan does not match original")
    records = raw.get("records")
    if not isinstance(records, list) or len(records) != MONOS:
        raise ValueError("Wwise object record count changed")
    capped, unparsed, seen = [], [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Malformed original object")
        file, pid = scoped(record)
        if (file, pid) in seen:
            raise ValueError("Duplicate original Wwise object identity")
        seen.add((file, pid))
        nums = record.get("numeric_fields")
        if not isinstance(nums, list) or len(nums) > FIELDS:
            raise ValueError("Wwise numeric field bound not respected")
        if record.get("status") == "parsed":
            reasons = record.get("numeric_truncation_reasons")
            paths = [x.get("path") if isinstance(x, dict) else None for x in nums]
            if (not isinstance(reasons, list) or not reasons or
                    reasons != sorted(set(reasons)) or
                    any(x not in ("field_limit", "depth_limit") for x in reasons) or
                    record.get("fields_truncated") is not True or
                    ("field_limit" in reasons and len(nums) != FIELDS) or
                    any(not isinstance(x, str) or len(x) > 4096 for x in paths)):
                raise ValueError("Uncapped, forged or invalid Wwise numeric fields")
            name = record.get("name", "")
            if not isinstance(name, str):
                raise ValueError("Invalid original Wwise name")
            capped.append({
                "serialized_file": file, "path_id": pid, "status": "capped",
                "display_name": name[:96], "truncation_reasons": reasons,
                "visible_numeric_field_count": len(nums),
                "numeric_path_sha256": hashlib.sha256(
                    "\n".join(sorted(paths)).encode("utf-8")).hexdigest(),
            })
        elif record.get("status") == "unparsed":
            err = record.get("error_type")
            if (not isinstance(err, str) or
                    not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,95}", err) or
                    nums or record.get("fields_truncated") or
                    record.get("numeric_truncation_reasons")):
                raise ValueError("Unparsed Wwise record contains invented numeric evidence")
            unparsed.append({
                "serialized_file": file, "path_id": pid,
                "status": "unparsed", "error_type": err,
            })
        else:
            raise ValueError("Unknown Wwise object parsing state")
    if len(capped) != CAPS or len(unparsed) != UNPARSED:
        raise ValueError("Wwise original 274 caps and one unparsed not conserved")
    sort = lambda x: (x["serialized_file"], int(x["path_id"]))
    return {
        "schema_version": 1, "bundle": BUNDLE, "source_sha256": SHA,
        "size_bytes": BYTES, "objects_by_type": source["objects_by_type"],
        "monobehaviours_total": MONOS, "monobehaviours_parsed": PARSED,
        "field_limit": FIELDS, "depth_limit": DEPTH, "capped_count": CAPS,
        "unparsed_count": UNPARSED, "full_numeric_extraction_complete": False,
        "scope": SCOPE, "capped_objects": sorted(capped, key=sort),
        "unparsed_objects": sorted(unparsed, key=sort),
    }


def verify(report, source):
    expected = {
        "schema_version": 1, "bundle": BUNDLE, "source_sha256": SHA,
        "size_bytes": BYTES, "objects_by_type": source["objects_by_type"],
        "monobehaviours_total": MONOS, "monobehaviours_parsed": PARSED,
        "field_limit": FIELDS, "depth_limit": DEPTH, "capped_count": CAPS,
        "unparsed_count": UNPARSED, "full_numeric_extraction_complete": False,
        "scope": SCOPE,
    }
    if (not isinstance(report, dict) or
            set(report) != set(expected) | {"capped_objects", "unparsed_objects"} or
            any(report.get(k) != v for k, v in expected.items())):
        raise ValueError("Wwise report fingerprint, counts or schema mismatch")
    caps, missing = report.get("capped_objects"), report.get("unparsed_objects")
    if (not isinstance(caps, list) or len(caps) != CAPS or
            not isinstance(missing, list) or len(missing) != UNPARSED):
        raise ValueError("Wwise 274 plus 1 report must be nonempty/exact")
    seen = set()
    for row in caps:
        if not isinstance(row, dict) or set(row) != {
            "serialized_file", "path_id", "status", "display_name",
            "truncation_reasons", "visible_numeric_field_count", "numeric_path_sha256"}:
            raise ValueError("Incomplete original Wwise capped row")
        key = scoped(row)
        reasons, n, digest = (row["truncation_reasons"],
                              row["visible_numeric_field_count"],
                              row["numeric_path_sha256"])
        if (key in seen or row["status"] != "capped" or
                not isinstance(row["display_name"], str) or len(row["display_name"]) > 96 or
                not isinstance(reasons, list) or not reasons or
                reasons != sorted(set(reasons)) or
                any(x not in ("field_limit", "depth_limit") for x in reasons) or
                type(n) is not int or not 0 <= n <= FIELDS or
                ("field_limit" in reasons and n != FIELDS) or
                not isinstance(digest, str) or
                not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("Duplicate, forged or resolved Wwise cap")
        seen.add(key)
    for row in missing:
        if not isinstance(row, dict) or set(row) != {
            "serialized_file", "path_id", "status", "error_type"}:
            raise ValueError("Wwise unparsed row incomplete")
        key = scoped(row)
        if (key in seen or row["status"] != "unparsed" or
                not isinstance(row["error_type"], str) or
                not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,95}", row["error_type"])):
            raise ValueError("Invalid or duplicated unparsed Wwise object")
        seen.add(key)
    sort = lambda x: (x["serialized_file"], int(x["path_id"]))
    if (caps != sorted(caps, key=sort) or
            missing != sorted(missing, key=sort) or len(seen) != MONOS):
        raise ValueError("Wwise original object identities missing/reordered")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "scan", "reconcile"))
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--index", type=Path)
    args = parser.parse_args()
    source = evidence(json.loads(args.ledger.read_text(encoding="utf-8")))
    meta = {"bundle": BUNDLE, "lfs_oid_sha256": SHA, "size_bytes": BYTES}
    recorded = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else None
    if recorded is not None:
        verify(recorded, source)
    mode = "recheck" if recorded is not None else "new"
    if args.command == "plan":
        verify_source(Path(BUNDLE), meta, phase="pointer")
        git_sha = subprocess.check_output(
            ["git", "hash-object", BUNDLE], text=True).strip()
        if git_sha != POINTER:
            raise ValueError("Original Wwise Git LFS pointer SHA differs")
        print("WWISE_CAP_PLAN=" + json.dumps({"mode": mode, "capped": CAPS},
                                              sort_keys=True))
    elif args.command == "scan":
        if args.output is None:
            parser.error("scan requires --output")
        verify_source(Path(BUNDLE), meta, phase="bytes")
        from reconstruction.tools.streamed_unityfs import streamed_unityfs
        with streamed_unityfs(scope="WWISE"):
            raw = scan_bundle(Path(BUNDLE), max_fields=FIELDS, max_depth=DEPTH,
                              expected_sha256=SHA)
        report = build(raw, source)
        verify(report, source)
        if recorded is not None and recorded != report:
            raise ValueError("Original Wwise scoped cap evidence changed on recheck")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) +
                               "\n", encoding="utf-8")
        print("WWISE_CAP_INDEX=" + json.dumps({
            "mode": mode, "capped": CAPS, "unparsed": UNPARSED,
            "full_numeric_extraction_complete": False,
        }, sort_keys=True))
    else:
        if args.index is None:
            parser.error("reconcile requires --index")
        report = json.loads(args.index.read_text(encoding="utf-8"))
        verify(report, source)
        if recorded is not None and report != recorded:
            raise ValueError("Original Wwise cap report differs from committed evidence")
        print("WWISE_CAP_SUMMARY=" + json.dumps({
            "mode": mode, "capped": CAPS, "unparsed": UNPARSED,
            "identities": MONOS, "reverified": MONOS if recorded is not None else 0,
            "full_numeric_extraction_complete": False,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
