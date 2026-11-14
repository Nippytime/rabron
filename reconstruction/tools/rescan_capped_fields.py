#!/usr/bin/env python3
"""Revisit only historically field-capped Unity MonoBehaviours, read-only.

Reproduce each recorded first-pass limit against SHA-256-verified source bytes;
take those exact path IDs and retry them at higher bounded limits. Report
unresolved caps instead of inferring balance formulas from client data.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.summarize_numeric_evidence import summarize


# Original GitHub Actions limits, independently documented by workflow/source.
HISTORIC_FIELD_LIMITS = {
    "scriptableobjects_assets_all.bundle": 4096,
    "location-settlement-data_assets_all.bundle": 512,
    "location-city-data_assets_all.bundle": 256,
    "location-hub-data_assets_all.bundle": 256,
    "location-sectorcenter-data_assets_all.bundle": 256,
    "location-settlement2-data_assets_all.bundle": 256,
    "inbuild_assets_all.bundle": 256,
}


def historical_entry(ledger, bundle_path):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported extraction ledger")
    matches = [record for record in ledger["scans"]
               if record["bundle"] == bundle_path]
    if len(matches) != 1:
        raise ValueError("Bundle must have exactly one documented historical scan")
    record = matches[0]
    if record["numeric_field_cap_records"] <= 0:
        raise ValueError("Only historically field-capped bundles can be targeted")
    if Path(bundle_path).name not in HISTORIC_FIELD_LIMITS:
        raise ValueError("Historical field limit not documented for this source")
    return record


def incomplete(records):
    return [r for r in records
            if r.get("status") != "parsed" or r.get("fields_truncated")]


def rescan(path, evidence, *, first_limit, target_limit=8192,
           max_depth=32, retry_limit=16384, retry_depth=48,
           scanner=scan_bundle):
    if first_limit < 1 or target_limit <= first_limit or (
            retry_limit < target_limit or max_depth < 16 or retry_depth < max_depth):
        raise ValueError("Invalid bounded rescan limits")
    fingerprint = evidence["sha256"]
    initial = scanner(path, expected_sha256=fingerprint,
                      max_fields=first_limit, max_depth=16)
    if (initial["sha256"] != fingerprint or
            initial["monobehaviours_total"] != evidence["monobehaviours_total"] or
            initial["monobehaviours_parsed"] != evidence["monobehaviours_parsed"] or
            initial["limit_reached"]):
        raise ValueError("Source differs from documented historical inspection")

    old = [r for r in initial["records"]
           if "field_limit" in r.get("numeric_truncation_reasons", [])]
    if len(old) != evidence["numeric_field_cap_records"]:
        raise ValueError("Previously capped path IDs do not reproduce: " +
                         str(len(old)) + " != " +
                         str(evidence["numeric_field_cap_records"]))
    selected = {r["path_id"] for r in old}
    if len(selected) != len(old):
        raise ValueError("Duplicate historic MonoBehaviour path IDs")
    first = scanner(path, path_ids=selected, expected_sha256=fingerprint,
                    max_fields=target_limit, max_depth=max_depth)
    if (first["missing_path_ids"] or first["sha256"] != fingerprint or
            len(first["records"]) != len(selected)):
        raise ValueError("First targeted rescan lost selected records")

    final_by_id = {r["path_id"]: r for r in first["records"]}
    needs_retry = {r["path_id"] for r in incomplete(first["records"])}
    if needs_retry:
        retry = scanner(path, path_ids=needs_retry, expected_sha256=fingerprint,
                        max_fields=retry_limit, max_depth=retry_depth)
        if (retry["missing_path_ids"] or retry["sha256"] != fingerprint or
                {r["path_id"] for r in retry["records"]} != needs_retry):
            raise ValueError("Adaptive retry did not return all selected records")
        final_by_id.update({r["path_id"]: r for r in retry["records"]})

    records = [final_by_id[key] for key in sorted(selected, key=int)]
    failures = incomplete(records)
    reasons = Counter(reason for r in records
                      for reason in r.get("numeric_truncation_reasons", []))
    report = {
        "schema_version": 1,
        "bundle": evidence["bundle"],
        "source_sha256": fingerprint,
        "historical_scan_evidence": evidence["scan_evidence"],
        "monobehaviours_in_source": initial["monobehaviours_total"],
        "historical_field_cap_limit": first_limit,
        "historical_field_cap_records_reproduced": len(old),
        "targeted_path_ids": sorted(selected, key=int),
        "target_limit": target_limit,
        "target_depth": max_depth,
        "adaptive_retry_limit": retry_limit,
        "adaptive_retry_depth": retry_depth,
        "adaptive_retried_records": len(needs_retry),
        "resolved_records": len(records) - len(failures),
        "unresolved_records": len(failures),
        "unresolved_path_ids": [r["path_id"] for r in failures],
        "remaining_truncation_reasons": dict(sorted(reasons.items())),
        "targeted_numeric_extraction_complete": not failures,
        "full_bundle_numeric_extraction_complete": False,
        "authority": "client serialized data only; no verified live game formulas",
        "records": records,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="Bounded path-ID numeric evidence JSON")
    parser.add_argument("--summary", type=Path, required=True,
                        help="Short outcome with category samples, no media")
    args = parser.parse_args()
    source = args.bundle.as_posix()
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    evidence = historical_entry(ledger, source)
    old_limit = HISTORIC_FIELD_LIMITS[args.bundle.name]
    result = rescan(args.bundle, evidence, first_limit=old_limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")

    # Summarizer accepts scanner-format records; keep full-bundle completeness
    # false, because this pass intentionally selects only earlier overflow IDs.
    numeric = summarize({
        "source": source,
        "sha256": result["source_sha256"],
        "records": result["records"],
        "monobehaviours_total": result["monobehaviours_in_source"],
        "monobehaviours_attempted": len(result["records"]),
        "monobehaviours_parsed": sum(
            r.get("status") == "parsed" for r in result["records"]),
        "complete_numeric_extraction": False,
    }, samples_per_category=20)
    summary = {key: value for key, value in result.items() if key != "records"}
    summary["numeric_candidates"] = numeric["candidate_field_groups"]
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, sort_keys=True, indent=2,
                                       allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in (
        "bundle", "source_sha256", "historical_field_cap_records_reproduced",
        "adaptive_retried_records", "resolved_records", "unresolved_records",
        "remaining_truncation_reasons")}, sort_keys=True))


if __name__ == "__main__":
    main()
