#!/usr/bin/env python3
"""Prioritize ALL tracked Unity bundles without downloading or redistributing them.

Reads the Git tree (works in sparse Actions checkouts) and a small ledger of
documented, incomplete MonoBehaviour passes. This tool DOES NOT extract asset
bytes, invent formula values, or equate parsing with gameplay reconstruction.
"""

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "reconstruction/data/extraction_coverage.json"
BUNDLE_PREFIX = "StreamingAssets/aa/StandaloneWindows64/"

HIGH_PRIORITY = (
    "scriptableobjects", "shared-global", "location-", "npc_",
    "tutorial_", "inbuild_", "weapon", "vehicle", "car-", "cargo",
    "police", "prison", "settlement", "construction", "building", "item",
)
MEDIUM_PRIORITY = (
    "character-", "inventory", "animation", "ui-", "effects", "sound",
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def tracked_bundles(*, ref="HEAD", root=ROOT):
    """Read git object names, not checkout file contents or Git LFS pointers."""
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", BUNDLE_PREFIX],
        cwd=root, check=True, text=True, capture_output=True,
    )
    return sorted(path for path in result.stdout.splitlines()
                  if path.startswith(BUNDLE_PREFIX) and path.endswith(".bundle"))


def validate_ledger(ledger, paths):
    if ledger.get("schema_version") != 1:
        raise ValueError("Unsupported evidence ledger version")
    all_paths = set(paths)
    if len(all_paths) != len(paths):
        raise ValueError("Git tree contains duplicate bundle paths")
    scanned = {}
    for entry in ledger["scans"]:
        path = entry["bundle"]
        if path not in all_paths or path in scanned:
            raise ValueError("Unknown/duplicate documented scan: " + path)
        if not SHA256.fullmatch(entry["sha256"]):
            raise ValueError("Invalid SHA-256 for " + path)
        if "lfs_oid_sha256" in entry:
            if (entry["lfs_oid_sha256"] != entry["sha256"] or
                    type(entry.get("size_bytes")) is not int or
                    entry["size_bytes"] <= 0):
                raise ValueError("Scanned LFS source fingerprint/size mismatch: " + path)
        total = entry["monobehaviours_total"]
        parsed = entry["monobehaviours_parsed"]
        capped = entry["numeric_field_cap_records"]
        if not all(isinstance(n, int) and not isinstance(n, bool) for n in
                   (total, parsed, capped)):
            raise ValueError("Invalid scan counts for " + path)
        if total < 0 or not 0 <= parsed <= total or not 0 <= capped <= parsed:
            raise ValueError("Inconsistent scan counts for " + path)
        targeted = entry.get("targeted_rescan")
        if targeted is not None:
            resolved = targeted.get("resolved_count")
            unresolved = targeted.get("unresolved_count")
            if (not all(type(n) is int and n >= 0 for n in
                        (resolved, unresolved)) or resolved + unresolved != capped or
                    targeted.get("complete_historical_field_caps") != (unresolved == 0)):
                raise ValueError("Inconsistent targeted source rescan counts: " + path)
        scanned[path] = entry
    lfs = {}
    for entry in ledger.get("known_lfs_not_yet_scanned", ()):
        path = entry["bundle"]
        if path not in all_paths or path in lfs or path in scanned:
            raise ValueError("Unknown/duplicate LFS pending bundle: " + path)
        if not SHA256.fullmatch(entry["lfs_oid_sha256"]):
            raise ValueError("Invalid LFS OID for " + path)
        lfs[path] = entry
    return scanned, lfs


def priority(path):
    name = path.rsplit("/", 1)[-1].lower()
    if any(token in name for token in HIGH_PRIORITY):
        return "high"
    if any(token in name for token in MEDIUM_PRIORITY):
        return "medium"
    return "low"


def plan_scans(paths, ledger):
    """Return a stable, truthful backlog and coverage summary."""
    paths = sorted(paths)
    known, pending_lfs = validate_ledger(ledger, paths)
    queue = []
    for path in paths:
        evidence = known.get(path)
        if evidence:
            # Even with no reported cap, the historic scanner omitted nested
            # depth-limit branches and did not extract every Unity object kind.
            cap = evidence["numeric_field_cap_records"]
            retry = evidence.get("targeted_rescan")
            remaining = retry["unresolved_count"] if retry else cap
            if evidence["monobehaviours_total"] == 0:
                status = "inspected_no_monobehaviours"
            elif cap and not remaining:
                status = "historic_caps_resolved_scope_partial"
            elif remaining:
                status = "partial_field_cap"
            else:
                status = "documented_monobehaviour_pass_unverified"
        elif path in pending_lfs:
            status = "needs_lfs_bytes"
        else:
            status = "not_documented_scanned"
        rank = priority(path)
        queue.append({
            "bundle": path,
            "priority": rank,
            "status": status,
            "next_action": (
                ("review unresolved field-limited objects with source labels"
                 if status == "partial_field_cap" else
                 "inventory non-MonoBehaviour content references; no numeric rules"
                 if status == "inspected_no_monobehaviours" else
                 "audit other Unity object types and confirm source semantics")
                if evidence else
                "fetch verified LFS bytes then inventory" if path in pending_lfs
                else "run read-only UnityFS inventory and classify results"
            ),
            "evidence_doc": evidence["scan_evidence"] if evidence else None,
            "historic_numeric_cap_records": (
                evidence["numeric_field_cap_records"] if evidence else None
            ),
            "remaining_historic_field_caps": (
                evidence.get("targeted_rescan", {}).get(
                    "unresolved_count", evidence["numeric_field_cap_records"])
                if evidence else None
            ),
            "historic_source_sha256": evidence["sha256"] if evidence else None,
        })
    rank = {"high": 0, "medium": 1, "low": 2}
    status_rank = {
        "needs_lfs_bytes": 0,
        "partial_field_cap": 1,
        "not_documented_scanned": 2,
        "documented_monobehaviour_pass_unverified": 3,
        "historic_caps_resolved_scope_partial": 4,
        "inspected_no_monobehaviours": 5,
    }
    queue.sort(key=lambda item: (rank[item["priority"]],
                                 status_rank[item["status"]],
                                 item["bundle"]))
    count = Counter(item["status"] for item in queue)
    return {
        "schema_version": 1,
        "scope": "Tracked UnityFS .bundle paths; MonoBehaviour documentation only",
        "tracked_bundles": len(paths),
        "historically_documented_scan_bundles": len(known),
        "documented_monobehaviours_parsed": sum(
            e["monobehaviours_parsed"] for e in known.values()
        ),
        "historic_field_capped_records": sum(
            e["numeric_field_cap_records"] for e in known.values()
        ),
        "remaining_historic_field_capped_records": sum(
            e.get("targeted_rescan", {}).get(
                "unresolved_count", e["numeric_field_cap_records"])
            for e in known.values()
        ),
        "statuses": dict(sorted(count.items())),
        "source_limitations": ledger.get("blocking_missing_sources", []),
        "warning": (
            "Historical scans are NOT complete source extraction. Even zero "
            "reported field caps cannot establish nested-depth completeness, "
            "all Unity object types, server-side formulas, or asset use rights."
        ),
        "backlog": queue,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD", help="Git tree to inspect")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-tracked", type=int, default=0)
    args = parser.parse_args()
    if args.min_tracked < 0:
        parser.error("--min-tracked must be nonnegative")
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    data = plan_scans(tracked_bundles(ref=args.ref), ledger)
    if data["tracked_bundles"] < args.min_tracked:
        raise ValueError("Expected at least " + str(args.min_tracked) +
                         " tracked Unity bundles, got " + str(data["tracked_bundles"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: data[key] for key in (
        "tracked_bundles", "historically_documented_scan_bundles",
        "documented_monobehaviours_parsed", "historic_field_capped_records",
        "remaining_historic_field_capped_records",
        "statuses")}, sort_keys=True))
    for item in data["backlog"][:12]:
        print(item["status"] + "\t" + item["bundle"])


if __name__ == "__main__":
    main()
