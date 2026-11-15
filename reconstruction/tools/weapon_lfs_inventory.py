"""Source-pinned, metadata-only two-weapon Git LFS inspection.

The pointer is not the UnityFS binary. Never mark absent LFS bytes as scanned.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.plan_bundle_scans import validate_ledger
from reconstruction.tools.small_bundle_inventory import tree_entries
from reconstruction.tools.summarize_numeric_evidence import summarize
from reconstruction.tools.validate_source_inventory import validate
from reconstruction.tools.verify_priority_lfs import verify_source

PREFIX = "StreamingAssets/aa/StandaloneWindows64/"
EVIDENCE = "GitHub Actions W1-AC original weapon LFS source inventory artifact"
AD_EVIDENCE = "GitHub Actions W1-AD original equipment-realm LFS source inventory artifact"
AE_EVIDENCE = "GitHub Actions W1-AE original RC556-TAG12K LFS source inventory artifact"
AF_EVIDENCE = "GitHub Actions W1-AF original KL545-character LFS source inventory artifact"
AG_EVIDENCE = "GitHub Actions W1-AG original global-hub LFS source inventory artifact"
AH_EVIDENCE = "GitHub Actions W1-AH original shared-props Wwise-battle LFS source inventory artifact"
AI_EVIDENCE = "GitHub Actions W1-AI original sector-center common LFS source inventory artifact"
AJ_EVIDENCE = "GitHub Actions W1-AJ original shared-characters legacy-props LFS source inventory artifact"
FIELDS = 2048
DEPTH = 32
NAMES = {"weapon-mc10_assets_all.bundle", "weapon-pdw90_assets_all.bundle"}
AD_NAMES = {"equipement_assets_vfx.bundle", "space-realm_scenes_all.bundle"}
AE_NAMES = {"weapon-rc556_assets_all.bundle", "weapon-tag12k_assets_all.bundle"}
AF_NAMES = {"weapon-kl545_assets_all.bundle", "character_assets_.bundle"}
AG_NAMES = {"space-global_assets_all.bundle", "location-hub_standalone_scenes_all.bundle"}
AH_NAMES = {"shared-environment-props_assets_all.bundle", "wwisedata_windows_battle_assets_all.bundle"}
AI_NAMES = {"location-sectorcenter-standalone_scenes_all.bundle", "shared-environment-common_assets_all.bundle"}
AJ_NAMES = {"shared-characters_assets_all.bundle", "environment-props-legacy_assets_all.bundle"}
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")


def load_targets(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or len(data.get("sources", [])) != 2:
        raise ValueError("Exactly two versioned LFS source targets required")
    sources = data["sources"]
    if {e.get("bundle", "").removeprefix(PREFIX) for e in sources} not in (NAMES, AD_NAMES, AE_NAMES, AF_NAMES, AG_NAMES, AH_NAMES, AI_NAMES, AJ_NAMES):
        raise ValueError("Unexpected original LFS source scope")
    # Allow this exact pair's larger declared original objects without
    # changing the existing bound for any historical source scope.
    max_source_bytes = 185_000_000 if {
        e["bundle"].removeprefix(PREFIX) for e in sources
    } == AJ_NAMES else 150_000_000
    for e in sources:
        if (set(e) != {"bundle", "git_blob_sha", "lfs_oid_sha256", "size_bytes"}
                or not e["bundle"].startswith(PREFIX)
                or not HEX40.fullmatch(e["git_blob_sha"])
                or not HEX64.fullmatch(e["lfs_oid_sha256"])
                or type(e["size_bytes"]) is not int
                or not 1_000_000 <= e["size_bytes"] <= max_source_bytes):
            raise ValueError("Invalid original Git pointer source fingerprint")
    return sources


def verify_pointer(entry):
    path = Path(entry["bundle"])
    verified = verify_source(path, entry, phase="pointer")
    payload = path.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(payload)).encode() +
                       b"\0" + payload).hexdigest()
    if sha != entry["git_blob_sha"]:
        raise ValueError("Original LFS Git pointer SHA-1 mismatch")
    return verified


def source_plan(sources, ledger, entries, *, expected_tracked=330,
                scan_evidence=EVIDENCE):
    if len(entries) != expected_tracked:
        raise ValueError("Tracked original Git bundle count changed")
    scanned, pending = validate_ledger(ledger, sorted(entries))
    if any(e["bundle"] in pending for e in sources):
        raise ValueError("Previously pending LFS source needs reconciliation")
    modes = []
    for e in sources:
        git = entries.get(e["bundle"])
        if (git is None or git["git_blob_sha"] != e["git_blob_sha"]
                or not 120 <= git["git_blob_size"] <= 150):
            raise ValueError("Original Git LFS pointer blob fingerprint drift")
        old = scanned.get(e["bundle"])
        if old is not None and (
                old.get("lfs_oid_sha256") != e["lfs_oid_sha256"] or
                old.get("sha256") != e["lfs_oid_sha256"] or
                old.get("size_bytes") != e["size_bytes"] or
                old.get("git_blob_sha") != e["git_blob_sha"] or
                old.get("scan_evidence") != scan_evidence):
            raise ValueError("Previously documented source evidence drift")
        modes.append("recheck" if old else "new")
    if len(set(modes)) != 1:
        raise ValueError("Partially documented source set cannot be certified")
    return {"schema_version": 1, "mode": modes[0], "sources": sources,
            "tracked_bundles": expected_tracked,
            "documented_before": len(ledger["scans"])}


def scan(entry, run_url, *, scan_evidence=EVIDENCE):
    path = Path(entry["bundle"])
    verified = verify_source(path, entry, phase="bytes")
    if path.name == "wwisedata_windows_battle_assets_all.bundle":
        from reconstruction.tools.streamed_unityfs import streamed_unityfs
        with streamed_unityfs():
            raw = scan_bundle(path, max_fields=FIELDS, max_depth=DEPTH,
                              expected_sha256=verified["sha256"])
    else:
        raw = scan_bundle(path, max_fields=FIELDS, max_depth=DEPTH,
                          expected_sha256=verified["sha256"])
    summary = summarize(raw, samples_per_category=3)
    checked = validate(raw, summary, source=entry["bundle"],
                       expected_size=entry["size_bytes"],
                       max_fields=FIELDS, max_depth=DEPTH)
    return {
        "bundle": entry["bundle"], "sha256": verified["sha256"],
        "size_bytes": entry["size_bytes"],
        "git_blob_sha": entry["git_blob_sha"],
        "lfs_oid_sha256": entry["lfs_oid_sha256"],
        "scan_evidence": scan_evidence, "run_url": run_url,
        "scope": "bounded MonoBehaviour fields and object type counts only; not source code or game formulas",
        "status": "documented_scan_not_fully_verified",
        "monobehaviours_total": checked["monobehaviours_total"],
        "monobehaviours_parsed": checked["parsed"],
        "numeric_field_cap_records": checked["truncated"],
        "unparsed_records": checked["unparsed"],
        "bounded_numeric_scan_complete": checked["bounded_mono_numeric_complete"],
        "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
        "objects_by_type": checked["object_types"],
        "candidate_field_counts": {
            name: value["matching_numeric_fields"]
            for name, value in summary["candidate_field_groups"].items()
        },
    }


def reconcile(plan, records, ledger, run_url, tracked, *,
              scan_evidence=EVIDENCE):
    if (plan["tracked_bundles"] != len(tracked) or
            plan["documented_before"] != len(ledger["scans"]) or
            len(records) != 2 or
            len({r.get("bundle") for r in records}) != 2):
        raise ValueError("Two-original LFS coverage/accounting changed")
    expected = {e["bundle"]: e for e in plan["sources"]}
    if set(expected) != {e["bundle"] for e in records}:
        raise ValueError("Missing, swapped or duplicate LFS source result")
    old = {e["bundle"]: e for e in ledger["scans"]}
    for record in records:
        e = expected[record["bundle"]]
        if (record.get("git_blob_sha") != e["git_blob_sha"] or
                record.get("lfs_oid_sha256") != e["lfs_oid_sha256"] or
                record.get("sha256") != e["lfs_oid_sha256"] or
                record.get("size_bytes") != e["size_bytes"] or
                record.get("scan_evidence") != scan_evidence or
                record.get("run_url") != run_url or
                record.get("numeric_field_limit") != FIELDS or
                record.get("numeric_depth_limit") != DEPTH or
                record.get("status") != "documented_scan_not_fully_verified" or
                type(record.get("monobehaviours_total")) is not int or
                record["monobehaviours_total"] < 0 or
                type(record.get("unparsed_records")) is not int or
                record["unparsed_records"] < 0):
            raise ValueError("Source record lacks measured original identity")
        total = record["monobehaviours_total"]
        parsed = record.get("monobehaviours_parsed")
        unparsed = record["unparsed_records"]
        capped = record.get("numeric_field_cap_records")
        complete = record.get("bounded_numeric_scan_complete")
        objects = record.get("objects_by_type")
        candidates = record.get("candidate_field_counts")
        if (type(parsed) is not int or parsed < 0 or
                parsed + unparsed != total or
                type(capped) is not int or not 0 <= capped <= parsed or
                type(complete) is not bool or
                complete != (unparsed == 0 and capped == 0) or
                not isinstance(objects, dict) or not objects or
                any(not isinstance(name, str) or not name or
                    type(count) is not int or count < 0
                    for name, count in objects.items()) or
                sum(objects.values()) <= 0 or
                objects.get("MonoBehaviour", 0) != total or
                not isinstance(candidates, dict) or
                set(candidates) != {"economy", "combat", "progression",
                                    "timing_and_world"} or
                any(type(count) is not int or count < 0
                    for count in candidates.values())):
            raise ValueError("Original Unity object/MonoBehaviour/numeric accounting mismatch")
    if plan["mode"] == "new":
        if any(e["bundle"] in old for e in records):
            raise ValueError("Original source was documented before scan")
        proposed = {**ledger, "scans": [*ledger["scans"], *records]}
        new_count = 2
    elif plan["mode"] == "recheck":
        compare = ("sha256", "size_bytes", "git_blob_sha", "lfs_oid_sha256",
                   "monobehaviours_total", "monobehaviours_parsed",
                   "unparsed_records", "numeric_field_cap_records",
                   "bounded_numeric_scan_complete", "objects_by_type",
                   "candidate_field_counts", "numeric_field_limit",
                   "numeric_depth_limit", "scan_evidence")
        if any(e["bundle"] not in old or
               any(old[e["bundle"]].get(k) != e.get(k) for k in compare)
               for e in records):
            raise ValueError("Previously documented original LFS source drift")
        proposed = ledger
        new_count = 0
    else:
        raise ValueError("Unsupported original-source scan mode")
    validate_ledger(proposed, sorted(tracked))
    return {
        "documented_before": len(ledger["scans"]),
        "documented_after": len(proposed["scans"]),
        "new_documented": new_count,
        "source_reverified": 2 - new_count,
        "unscanned_after": len(tracked) - len(proposed["scans"]),
        "tracked_bundles": len(tracked), "unparseable_attempts": [],
        "source_run_url": run_url,
    }, proposed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "pointer", "bytes", "scan", "reconcile"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--bundle")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--run-url")
    args = parser.parse_args()
    targets = load_targets(args.manifest)
    names = {e["bundle"].removeprefix(PREFIX) for e in targets}
    if names == AD_NAMES:
        evidence, log_prefix = AD_EVIDENCE, "W1AD"
    elif names == AE_NAMES:
        evidence, log_prefix = AE_EVIDENCE, "W1AE"
    elif names == AF_NAMES:
        evidence, log_prefix = AF_EVIDENCE, "W1AF"
    elif names == AG_NAMES:
        evidence, log_prefix = AG_EVIDENCE, "W1AG"
    elif names == AH_NAMES:
        evidence, log_prefix = AH_EVIDENCE, "W1AH"
    elif names == AI_NAMES:
        evidence, log_prefix = AI_EVIDENCE, "W1AI"
    elif names == AJ_NAMES:
        evidence, log_prefix = AJ_EVIDENCE, "W1AJ"
    else:
        evidence, log_prefix = EVIDENCE, "W1AC"
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    if args.command in ("pointer", "bytes"):
        item = next((e for e in targets if e["bundle"] == args.bundle), None)
        if item is None:
            raise ValueError("Source path absent from exact LFS registry")
        result = (verify_pointer(item) if args.command == "pointer" else
                  verify_source(Path(item["bundle"]), item, phase="bytes"))
        print(json.dumps(result, sort_keys=True))
    elif args.command == "scan":
        item = next((e for e in targets if e["bundle"] == args.bundle), None)
        if item is None or not args.run_url or args.output is None:
            raise ValueError("Exact scan source/run/output required")
        record = scan(item, args.run_url, scan_evidence=evidence)
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"source": record["bundle"], "objects": sum(
            record["objects_by_type"].values())}, sort_keys=True))
    else:
        entries = tree_entries()
        if args.command == "plan":
            plan = source_plan(targets, ledger, entries,
                               scan_evidence=evidence)
            for item in targets:
                verify_pointer(item)
            if args.output is None or args.matrix is None:
                raise ValueError("Plan and matrix output paths required")
            args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
            args.matrix.write_text(json.dumps({"include": [
                {"name": e["bundle"].removeprefix(PREFIX)} for e in targets
            ]}, separators=(",", ":")) + "\n")
            print(json.dumps({"mode": plan["mode"], "source_count": 2,
                              "documented_before": plan["documented_before"]}))
        else:
            if not args.plan or not args.evidence_dir or not args.run_url or not args.output:
                raise ValueError("Reconciliation requires source plan, artifacts and run URL")
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            records = [json.loads((args.evidence_dir / (
                entry["bundle"].removeprefix(PREFIX) + ".json")).read_text())
                       for entry in plan["sources"]]
            if [e["bundle"] for e in plan.get("sources", [])] != [
                    e["bundle"] for e in targets]:
                raise ValueError("Reconciliation plan differs from source manifest")
            report, proposed = reconcile(
                plan, records, ledger, args.run_url, entries,
                scan_evidence=evidence)
            args.output.write_text(json.dumps({
                "report": report, "proposed_ledger": proposed
            }, indent=2, sort_keys=True) + "\n")
            print(log_prefix + "_SUMMARY=" + json.dumps(report, separators=(",", ":"), sort_keys=True))
            new = proposed["scans"][len(ledger["scans"]):]
            encoded = json.dumps(new, separators=(",", ":"), sort_keys=True)
            for index in range(0, len(encoded), 4000):
                print(f"{log_prefix}_CHUNK_{index // 4000:03d}={encoded[index:index + 4000]}")


if __name__ == "__main__":
    main()
