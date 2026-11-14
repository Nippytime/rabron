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
        total = entry["monobehaviours_total"]
        parsed = entry["monobehaviours_parsed"]
        capped = entry["numeric_field_cap_records"]
        if not all(isinstance(n, int) and not isinstance(n, bool) for n in
                   (total, parsed, capped)):
            raise ValueError("Invalid scan counts for " + path)
        if total < 0 or not 0 <= parsed <= total or not 0 <= capped <= parsed:
            raise ValueError("Inconsistent scan counts for " + path)
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
            status = ("partial_field_cap" if evidence["numeric_field_cap_records"]
                      else "documented_monobehaviour_pass_unverified")
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
                "rescan with depth-aware completeness and raised field limit"
                if evidence else
                "fetch verified LFS bytes then inventory" if path in pending_lfs
                else "run read-only UnityFS inventory and classify results"
            ),
            "evidence_doc": evidence["scan_evidence"] if evidence else None,
            "historic_numeric_cap_records": (
                evidence["numeric_field_cap_records"] if evidence else None
            ),
            "historic_source_sha256": evidence["sha256"] if evidence else None,
        })
    rank = {"high": 0, "medium": 1, "low": 2}
    status_rank = {
        "needs_lfs_bytes": 0,
        "partial_field_cap": 1,
        "not_documented_scanned": 2,
        "documented_monobehaviour_pass_unverified": 3,
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
        "statuses")}, sort_keys=True))
    for item in data["backlog"][:12]:
        print(item["status"] + "\t" + item["bundle"])


if __name__ == "__main__":
    main()
