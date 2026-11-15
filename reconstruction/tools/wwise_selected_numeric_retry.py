"""Bounded original-Wwise five-object numeric retry (paths, never values).

This inventory cannot establish authoritative game/server formulas or source
asset redistribution rights. Incomplete numeric fields remain explicit.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from reconstruction.tools.wwise_cap_index import (
    BYTES, BUNDLE as CITY, DEPTH, FIELDS, POINTER as GIT_SHA,
    MONOS, INDEX as REF, SHA, evidence, verify as verify_index,
)
from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.validate_source_inventory import validate_object_identities
from reconstruction.tools.verify_priority_lfs import verify_source

TARGET_FIELDS = 8192
TARGET_DEPTH = 32
RETRY_FIELDS = 16384
RETRY_DEPTH = 48
REPORT = Path("reconstruction/data/wwise_selected_numeric_retry.json")


def stage(path, selected, measured, *, fields, depth, scanner):
    ids = {obj["path_id"] for obj in selected}
    if len(ids) != len(selected):
        raise ValueError("Cannot select scoped identities with ambiguous path IDs")
    raw = scanner(path, path_ids=ids, max_fields=fields, max_depth=depth,
                  expected_sha256=SHA)
    expected = {
        "source": CITY, "sha256": SHA, "size_bytes": BYTES,
        "numeric_field_limit": fields, "numeric_depth_limit": depth,
        "unityfs_magic": True, "objects_by_type": measured["objects_by_type"],
        "monobehaviours_total": MONOS, "monobehaviours_attempted": len(ids),
        "selected_path_ids": sorted(ids), "missing_path_ids": [],
        "limit_reached": False, "complete_numeric_extraction": False,
    }
    if any(raw.get(k) != v for k, v in expected.items()):
        raise ValueError("Original Wwise source or selected scan accounting changed")
    records = raw.get("records")
    if not isinstance(records, list) or len(records) != len(ids):
        raise ValueError("Selected Wwise objects missing or unexpectedly duplicated")
    validate_object_identities(records)
    wanted = {(s["serialized_file"], s["path_id"]) for s in selected}
    actual = {(r.get("serialized_file"), r.get("path_id")) for r in records}
    if actual != wanted:
        raise ValueError("Selected Wwise serialized-file/path identities changed")
    count = sum(r.get("status") == "parsed" for r in records)
    if raw.get("monobehaviours_parsed") != count:
        raise ValueError("Parsed Wwise record accounting contradicts source scan")
    if raw.get("selected_numeric_extraction_complete") is not (
            count == len(ids) and
            all(not r.get("fields_truncated") for r in records)):
        raise ValueError("Selected Wwise numeric completeness is false or forged")
    out = {}
    for rec in records:
        name = rec.get("name", "") if rec.get("status") == "parsed" else ""
        numeric = rec.get("numeric_fields")
        reasons = rec.get("numeric_truncation_reasons", [])
        if (rec.get("status") not in ("parsed", "unparsed") or
                not isinstance(numeric, list) or len(numeric) > fields or
                not isinstance(reasons, list) or
                any(x not in ("field_limit", "depth_limit") for x in reasons) or
                (rec.get("status") == "parsed" and
                 rec.get("fields_truncated") is not bool(reasons)) or
                not isinstance(name, str)):
            raise ValueError("Invalid selected object or cap record")
        if rec["status"] == "unparsed" and (reasons or numeric):
            raise ValueError("Unparsed record cannot claim extracted fields")
        paths = [field.get("path") for field in numeric]
        if any(not isinstance(x, str) for x in paths):
            raise ValueError("Original numeric field path missing")
        paths.sort()
        out[(rec["serialized_file"], rec["path_id"])] = {
            "status": rec["status"],
            "field_count": len(paths),
            "truncation_reasons": reasons,
            "error_type": rec.get("error_type", "") if rec["status"] == "unparsed" else "",
            "path_digest": hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest(),
            "sample_field_paths": [p[:120] for p in paths[:8]],
            "display_name": name[:96],
        }
    return out


def retry_wwise(measured, index, scanner):
    """Exactly three bounded stages; retry only still-incomplete records."""
    verify_index(index, measured)
    caps = index["capped_objects"]
    selected = [caps[i] for i in (0, 136, 273)]
    if [x["path_id"] for x in selected] != [
            "-9215429395481605246", "-6697251573783040",
            "9197897462607697745"]:
        raise ValueError("Original first/mid/last Wwise sample identities changed")

    def run(items, fields, depth):
        from reconstruction.tools.streamed_unityfs import (
            MAX_WWISE_MONO_OBJECT_BYTES, streamed_unityfs,
        )
        with streamed_unityfs(scope="WWISE", skip_container_index=True,
                              mono_budget_bytes=MAX_WWISE_MONO_OBJECT_BYTES):
            return stage(Path(CITY), items, measured, fields=fields,
                         depth=depth, scanner=scanner)

    baseline = run(selected, FIELDS, DEPTH)
    for item in selected:
        old = baseline[(item["serialized_file"], item["path_id"])]
        if (old["status"] != "parsed" or
                old["truncation_reasons"] != ["field_limit"] or
                old["field_count"] != FIELDS or
                old["display_name"] != item["display_name"] or
                old["path_digest"] != item["numeric_path_sha256"]):
            raise ValueError("Original Wwise sampled 2048-field caps or numeric paths did not reproduce")
    first = run(selected, TARGET_FIELDS, TARGET_DEPTH)
    to_retry = [item for item in selected
                if first[(item["serialized_file"], item["path_id"])]["status"] != "parsed"
                or first[(item["serialized_file"], item["path_id"])]["truncation_reasons"]]
    last = run(to_retry, RETRY_FIELDS, RETRY_DEPTH) if to_retry else {}
    results = []
    for item in selected:
        identity = (item["serialized_file"], item["path_id"])
        record = last.get(identity, first[identity])
        status = ("unparsed" if record["status"] == "unparsed" else
                  "still_capped" if record["truncation_reasons"] else "resolved")
        results.append({
            "serialized_file": identity[0], "path_id": identity[1],
            "status": status, "adaptive_retried": identity in last,
            "numeric_field_count": record["field_count"],
            "truncation_reasons": record["truncation_reasons"],
            "parse_error_type": record["error_type"],
            "numeric_path_sha256": record["path_digest"],
            "sample_numeric_field_paths": record["sample_field_paths"],
        })
    resolved = sum(x["status"] == "resolved" for x in results)
    return {
        "schema_version": 1, "source": CITY, "source_sha256": SHA,
        "size_bytes": BYTES, "selected_count": len(selected),
        "historical_field_limit": FIELDS, "historical_depth_limit": DEPTH,
        "first_retry_limit": TARGET_FIELDS, "first_retry_depth": TARGET_DEPTH,
        "adaptive_limit": RETRY_FIELDS, "adaptive_depth": RETRY_DEPTH,
        "adaptive_retried": len(to_retry), "resolved": resolved,
        "unresolved": len(selected) - resolved,
        "targeted_numeric_extraction_complete": resolved == len(selected),
        "full_bundle_numeric_extraction_complete": False,
        "scope": "three selected Wwise numeric path identities only; no values, audio or original formulas",
        "unselected_original_caps_untouched": 271,
        "outcomes": results,
    }


def verify_report(report, index):
    """Artifact reconciliation does not silently turn caps into completed formulas."""
    expected = {
        "schema_version": 1, "source": CITY, "source_sha256": SHA,
        "size_bytes": BYTES, "selected_count": 3,
        "historical_field_limit": FIELDS, "historical_depth_limit": DEPTH,
        "first_retry_limit": TARGET_FIELDS, "first_retry_depth": TARGET_DEPTH,
        "adaptive_limit": RETRY_FIELDS, "adaptive_depth": RETRY_DEPTH,
        "full_bundle_numeric_extraction_complete": False,
        "scope": "three selected Wwise numeric path identities only; no values, audio or original formulas",
        "unselected_original_caps_untouched": 271,
    }
    if not isinstance(report, dict) or set(report) != set(expected) | {
            "adaptive_retried", "resolved", "unresolved",
            "targeted_numeric_extraction_complete", "outcomes"} or any(
                report.get(k) != v for k, v in expected.items()):
        raise ValueError("Targeted source report schema/provenance mismatch")
    rows = report.get("outcomes")
    caps = index["capped_objects"]
    selected = [caps[i] for i in (0, 136, 273)]
    if [x["path_id"] for x in selected] != [
            "-9215429395481605246", "-6697251573783040",
            "9197897462607697745"]:
        raise ValueError("Original first/mid/last Wwise sample identities changed")
    if not isinstance(rows, list) or len(rows) != len(selected):
        raise ValueError("Exactly three source-scoped Wwise outcomes required")
    keys = [(r.get("serialized_file"), r.get("path_id")) for r in rows]
    if keys != [(r["serialized_file"], r["path_id"]) for r in selected]:
        raise ValueError("Scoped selected Wwise IDs reordered or swapped")
    if type(report.get("adaptive_retried")) is not int or not (
            0 <= report["adaptive_retried"] <= len(rows)):
        raise ValueError("Invalid retry count")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                "serialized_file", "path_id", "status", "adaptive_retried",
                "numeric_field_count", "truncation_reasons", "parse_error_type",
                "numeric_path_sha256", "sample_numeric_field_paths"}:
            raise ValueError("Missing or extraneous numeric retry fields")
        if (row["status"] not in ("resolved", "still_capped", "unparsed") or
                type(row["adaptive_retried"]) is not bool or
                type(row["numeric_field_count"]) is not int or
                not 0 <= row["numeric_field_count"] <=
                (RETRY_FIELDS if row["adaptive_retried"] else TARGET_FIELDS) or
                not isinstance(row["truncation_reasons"], list) or
                any(t not in ("field_limit", "depth_limit")
                    for t in row["truncation_reasons"]) or
                not isinstance(row["parse_error_type"], str) or
                not isinstance(row["numeric_path_sha256"], str) or
                len(row["numeric_path_sha256"]) != 64 or
                any(c not in "0123456789abcdef"
                    for c in row["numeric_path_sha256"]) or
                not isinstance(row["sample_numeric_field_paths"], list) or
                len(row["sample_numeric_field_paths"]) > 8 or
                any(not isinstance(s, str) or len(s) > 120
                    for s in row["sample_numeric_field_paths"])):
            raise ValueError("Bad scoped retry data")
        if ((row["status"] == "resolved") !=
                (not row["truncation_reasons"] and not row["parse_error_type"]) or
                (row["status"] == "unparsed") != bool(row["parse_error_type"])):
            raise ValueError("Source object erroneously marked resolved")
    resolved = sum(row["status"] == "resolved" for row in rows)
    if (report.get("resolved") != resolved or
            report.get("unresolved") != len(rows) - resolved or
            report["adaptive_retried"] !=
            sum(row["adaptive_retried"] for row in rows) or
            report.get("targeted_numeric_extraction_complete") is not
            (resolved == len(rows))):
        raise ValueError("Numeric targeted retry conservation failed")
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
    verify_index(index, measured)
    source = {"bundle": CITY, "lfs_oid_sha256": SHA, "size_bytes": BYTES}
    previous = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else None
    if previous is not None:
        verify_report(previous, index)
    mode = "recheck" if previous is not None else "new"
    if args.command == "plan":
        verify_source(Path(CITY), source, phase="pointer")
        git_sha = subprocess.check_output(
            ["git", "hash-object", CITY], text=True).strip()
        if git_sha != GIT_SHA:
            raise ValueError("Original source pointer Git blob SHA differs")
        print("WWISE_SAMPLE_PLAN=" + json.dumps({"mode": mode, "targets": 3},
                                             sort_keys=True))
    elif args.command == "scan":
        if args.output is None:
            parser.error("scan requires --output")
        verify_source(Path(CITY), source, phase="bytes")
        report = retry_wwise(measured, index, scan_bundle)
        verify_report(report, index)
        if previous is not None and report != previous:
            raise ValueError("Recorded targeted original retry differs on recheck")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) +
                               "\n", encoding="utf-8")
        print("WWISE_SAMPLE_RESULT=" + json.dumps({
            "mode": mode, "resolved": report["resolved"],
            "unresolved": report["unresolved"],
            "adaptive_retried": report["adaptive_retried"],
            "full_bundle_numeric_extraction_complete": False,
        }, sort_keys=True))
    else:
        if args.result is None:
            parser.error("reconcile requires --result")
        report = json.loads(args.result.read_text(encoding="utf-8"))
        verify_report(report, index)
        if previous is not None and report != previous:
            raise ValueError("Source retry result does not equal committed evidence")
        print("WWISE_SAMPLE_SUMMARY=" + json.dumps({
            "mode": mode, "resolved": report["resolved"],
            "unresolved": report["unresolved"],
            "verified_identities": len(report["outcomes"]),
            "full_bundle_numeric_extraction_complete": False,
            "reverified": len(report["outcomes"]) if previous is not None else 0,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
