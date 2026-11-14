#!/usr/bin/env python3
"""W1-F: bounded Git-tree-driven inventory of small original UnityFS sources.

The planner never downloads game media. Workers verify Git blob bytes and
perform read-only UnityPy scans. Evidence artifacts contain metadata only.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from reconstruction.tools.extract_unity_bundle import scan_bundle
from reconstruction.tools.plan_bundle_scans import (
    BUNDLE_PREFIX, DEFAULT_LEDGER, validate_ledger,
)
from reconstruction.tools.summarize_numeric_evidence import summarize
from reconstruction.tools.validate_source_inventory import validate

MIN_SIZE = 1024
MAX_SIZE = 999999
BATCH_SIZE = 20
MAX_BATCH_SIZE = 20
MAX_FIELDS = 2048
MAX_DEPTH = 32
SAFE_BUNDLE = re.compile(
    r"^StreamingAssets/aa/StandaloneWindows64/[A-Za-z0-9_().-]+\.bundle$"
)
SHA1 = re.compile(r"^[a-f0-9]{40}$")


def parse_tree_response(payload, expected_sha):
    """Validate GitHub's recursive Git tree metadata without fetching blobs."""
    if (payload.get("sha") != expected_sha or
            payload.get("truncated") is not False or
            not isinstance(payload.get("tree"), list)):
        raise ValueError("Git tree metadata missing, truncated or wrong commit")
    entries = {}
    for item in payload["tree"]:
        path = item.get("path")
        if not isinstance(path, str):
            raise ValueError("Git tree contains an invalid path")
        if not (path.startswith(BUNDLE_PREFIX) and path.endswith(".bundle")):
            continue  # Addressables catalog and other repository contents.
        sha, size = item.get("sha"), item.get("size")
        if (not SAFE_BUNDLE.fullmatch(path) or
                item.get("type") != "blob" or item.get("mode") != "100644" or
                not isinstance(sha, str) or not SHA1.fullmatch(sha) or
                type(size) is not int or size < 0):
            raise ValueError("Unexpected or unsafe Git tree entry: " + path)
        if path in entries:
            raise ValueError("Duplicate Git tree path: " + path)
        entries[path] = {
            "bundle": path, "git_blob_sha": sha, "git_blob_size": size,
        }
    return entries


def tree_entries(ref="HEAD"):
    # The local tree SHA pins API metadata to the checked-out PR merge ref;
    # git rev-parse reads no game blobs, unlike git ls-tree -l in a blobless clone.
    tree_sha = subprocess.run(
        ["git", "rev-parse", f"{ref}^{{tree}}"],
        check=True, text=True, capture_output=True,
    ).stdout.strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if (not SHA1.fullmatch(tree_sha) or
            not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or
            not token):
        raise ValueError("Missing trusted Git tree, repository or Actions token")
    url = f"https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return parse_tree_response(payload, expected_sha=tree_sha)

def make_plan(entries, ledger, *, batch_size=BATCH_SIZE, expected_tracked=330):
    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ValueError("Batch size must be between 1 and 20")
    if len(entries) != expected_tracked:
        raise ValueError("Tracked original bundle count changed; review inventory")
    scanned, pending_lfs = validate_ledger(ledger, sorted(entries))
    eligible = [
        entry for path, entry in sorted(entries.items())
        if path not in scanned and path not in pending_lfs
        and MIN_SIZE <= entry["git_blob_size"] <= MAX_SIZE
    ]
    # Once the measured W1-F entries are committed, keep exercising the same
    # binary provenance gate instead of generating an empty matrix.
    recheck = []
    if not eligible:
        recheck = [
            entry for path, entry in sorted(entries.items())
            if path in scanned and scanned[path].get("scan_evidence") ==
            "GitHub Actions W1-F small-source inventory artifact"
        ]
        for entry in recheck:
            documented = scanned[entry["bundle"]]
            if (documented.get("git_blob_sha") != entry["git_blob_sha"] or
                    documented.get("size_bytes") != entry["git_blob_size"]):
                raise ValueError("Previously documented Git source changed: " +
                                 entry["bundle"])
    # Size comes from the pinned Git tree, not checkout or LFS pointer bytes.
    selected = eligible or recheck
    batches = [
        {"id": index // batch_size, "sources": selected[index:index + batch_size]}
        for index in range(0, len(selected), batch_size)
    ]
    selected_paths = [e["bundle"] for group in batches
                      for e in group["sources"]]
    if len(set(selected_paths)) != len(selected_paths):
        raise ValueError("Duplicate planned source")
    if len(scanned) + (len(entries) - len(scanned)) != expected_tracked:
        raise ValueError("Source conservation failed")
    return {
        "schema_version": 1, "tracked_bundles": len(entries),
        "documented_scans_before": len(scanned),
        "unscanned_before": len(entries) - len(scanned),
        "eligible_small_sources": len(eligible),
        "recheck_documented_sources": len(recheck),
        "selected_small_sources": len(selected),
        "mode": "recheck" if recheck else "new",
        "excluded_pending_lfs": len(pending_lfs),
        "batch_size": batch_size, "batches": batches,
        "warning": "Git blob inventory only; no binary extraction completed at planning.",
    }


def selected_batch(plan, batch_id):
    if plan.get("schema_version") != 1:
        raise ValueError("Invalid plan version")
    groups = plan.get("batches")
    if not isinstance(groups, list):
        raise ValueError("Missing batch list")
    ids = [x["id"] for x in groups]
    if ids != list(range(len(groups))):
        raise ValueError("Duplicate or non-contiguous batch IDs")
    matches = [x for x in groups if x["id"] == batch_id]
    if len(matches) != 1:
        raise ValueError("Batch not present in plan")
    sources = matches[0]["sources"]
    if not 1 <= len(sources) <= MAX_BATCH_SIZE:
        raise ValueError("Unbounded batch")
    if len({x["bundle"] for x in sources}) != len(sources):
        raise ValueError("Duplicate batch path")
    for source in sources:
        if (not SAFE_BUNDLE.fullmatch(source["bundle"]) or
                not SHA1.fullmatch(source["git_blob_sha"]) or
                type(source["git_blob_size"]) is not int or
                not MIN_SIZE <= source["git_blob_size"] <= MAX_SIZE):
            raise ValueError("Unsafe batch input")
    return sources


def verify_bytes(path, entry):
    """Reject missing, swapped, truncated, LFS-pointer or non-UnityFS bytes."""
    if not path.is_file():
        raise ValueError("Checked-out source missing: " + str(path))
    size = path.stat().st_size
    if size != entry["git_blob_size"]:
        raise ValueError("Git source size mismatch: " + str(path))
    with path.open("rb") as file:
        data = file.read()
    if not data.startswith(b"UnityFS"):
        raise ValueError("Git blob is not a UnityFS binary: " + str(path))
    git_oid = hashlib.sha1(b"blob " + str(size).encode("ascii") +
                           b"\0" + data).hexdigest()
    if git_oid != entry["git_blob_sha"]:
        raise ValueError("Git blob SHA-1 mismatch: " + str(path))
    return hashlib.sha256(data).hexdigest()


def inspect_source(entry):
    path = Path(entry["bundle"])
    sha256 = verify_bytes(path, entry)
    result = {
        **entry, "sha256": sha256, "scan_tool": "UnityPy==1.25.4",
        "numeric_field_limit": MAX_FIELDS, "numeric_depth_limit": MAX_DEPTH,
        "source_status": "unparseable", "monobehaviours_total": None,
        "monobehaviours_parsed": None, "numeric_field_cap_records": None,
    }
    try:
        inventory = scan_bundle(path, max_fields=MAX_FIELDS,
                                max_depth=MAX_DEPTH, expected_sha256=sha256)
    except Exception as exc:
        # A valid original blob can have a schema this UnityPy version cannot
        # parse. Preserve this as a *failed scan attempt*, not as zero objects.
        if isinstance(exc, (ImportError, ModuleNotFoundError)) or (
                isinstance(exc, RuntimeError) and
                "Install UnityPy" in str(exc)):
            raise
        result["parse_error_type"] = type(exc).__name__
        return result
    # Validation errors mean evidence disagrees with actual bytes/counts.
    # They must fail CI instead of being relabeled as parser limitations.
    summary = summarize(inventory, samples_per_category=3)
    validated = validate(
        inventory, summary, source=str(path),
        expected_size=entry["git_blob_size"],
        max_fields=MAX_FIELDS, max_depth=MAX_DEPTH,
    )
    result.update({
        "source_status": (
            "bounded_mono_numeric_complete" if
            validated["bounded_mono_numeric_complete"] else "partial_mono_numeric"
        ),
        "unitypy_version": inventory["tool_version"],
        "objects_by_type": validated["object_types"],
        "monobehaviours_total": validated["monobehaviours_total"],
        "monobehaviours_parsed": validated["parsed"],
        "unparsed_records": validated["unparsed"],
        "numeric_field_cap_records": validated["truncated"],
        "bounded_numeric_scan_complete":
            validated["bounded_mono_numeric_complete"],
        "path_ids": [
            {"id": record["path_id"], "status": record["status"],
             "truncation": record.get("numeric_truncation_reasons", []),
             **({"error_type": record["error_type"]}
                if "error_type" in record else {})}
            for record in inventory["records"]
        ],
        "candidate_field_counts": {
            name: group["matching_numeric_fields"]
            for name, group in summary["candidate_field_groups"].items()
        },
        "candidate_examples": {
            name: group["examples"]
            for name, group in summary["candidate_field_groups"].items()
        },
    })
    return result


def run_batch(plan, batch_id, output):
    sources = selected_batch(plan, batch_id)
    results = []
    output.parent.mkdir(parents=True, exist_ok=True)
    for source in sources:
        # Missing/corrupt Git bytes are CI failures, not ordinary parse gaps.
        result = inspect_source(source)
        results.append(result)
        output.write_text(
            json.dumps({"schema_version": 1, "batch_id": batch_id,
                        "sources": results}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if all(e["source_status"] == "unparseable" for e in results):
        raise ValueError("No source in batch could be inventoried")
    return results


def consolidate(plan, evidence_dir, ledger, *, run_url):
    expected = {
        item["bundle"]: item
        for group in plan["batches"] for item in group["sources"]
    }
    if len(expected) != plan["selected_small_sources"]:
        raise ValueError("Planner totals conflict")
    seen = {}
    for group in plan["batches"]:
        file = evidence_dir / ("batch-%02d.json" % group["id"])
        if not file.is_file():
            raise ValueError("Missing batch result: " + str(file))
        payload = json.loads(file.read_text(encoding="utf-8"))
        if payload.get("batch_id") != group["id"]:
            raise ValueError("Batch ID does not match")
        actual_paths = [entry["bundle"] for entry in payload["sources"]]
        planned_paths = [entry["bundle"] for entry in group["sources"]]
        if actual_paths != planned_paths:
            raise ValueError("Missing/duplicate/reordered batch evidence")
        for entry in payload["sources"]:
            path = entry["bundle"]
            if path in seen or any(entry.get(k) != expected[path][k] for k in
                                   ("git_blob_sha", "git_blob_size")):
                raise ValueError("Duplicate or inconsistent source evidence")
            if not re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", "")):
                raise ValueError("Missing measured source SHA-256")
            seen[path] = entry
    if set(seen) != set(expected):
        raise ValueError("Unaccounted source paths")
    new = []
    incomplete = []
    for path in sorted(seen):
        e = seen[path]
        if e["source_status"] == "unparseable":
            incomplete.append({"bundle": path, "error": e["parse_error_type"]})
            continue
        if (e["source_status"] not in
                ("bounded_mono_numeric_complete", "partial_mono_numeric") or
                e["monobehaviours_total"] != len(e["path_ids"]) or
                e["monobehaviours_parsed"] != sum(
                    x["status"] == "parsed" for x in e["path_ids"]) or
                e["numeric_field_cap_records"] != sum(
                    bool(x["truncation"]) for x in e["path_ids"])):
            raise ValueError("Contradictory per-object inventory")
        new.append({
            "bundle": path, "sha256": e["sha256"],
            "size_bytes": e["git_blob_size"],
            "git_blob_sha": e["git_blob_sha"],
            "scan_evidence": "GitHub Actions W1-F small-source inventory artifact",
            "run_url": run_url,
            "scope": "bounded MonoBehaviour fields and object type counts only; not source code or game formulas",
            "status": "documented_scan_not_fully_verified",
            "monobehaviours_total": e["monobehaviours_total"],
            "monobehaviours_parsed": e["monobehaviours_parsed"],
            "numeric_field_cap_records": e["numeric_field_cap_records"],
            "unparsed_records": e["unparsed_records"],
            "bounded_numeric_scan_complete": e["bounded_numeric_scan_complete"],
            "numeric_field_limit": e["numeric_field_limit"],
            "numeric_depth_limit": e["numeric_depth_limit"],
            "objects_by_type": e["objects_by_type"],
            "candidate_field_counts": e["candidate_field_counts"],
        })
    if plan.get("mode") == "recheck":
        # A regression in a source already measured as scanned is an error,
        # never a silent reduction in documented coverage.
        if incomplete:
            raise ValueError("Previously documented source became unparseable")
        known = {e["bundle"]: e for e in ledger["scans"]}
        compare = (
            "sha256", "git_blob_sha", "size_bytes", "monobehaviours_total",
            "monobehaviours_parsed", "numeric_field_cap_records",
            "unparsed_records", "bounded_numeric_scan_complete",
            "numeric_field_limit", "numeric_depth_limit", "objects_by_type",
            "candidate_field_counts",
        )
        for entry in new:
            prior = known.get(entry["bundle"])
            if prior is None or any(prior.get(key) != entry.get(key)
                                    for key in compare):
                raise ValueError("Rechecked source evidence drift: " +
                                 entry["bundle"])
        proposed = ledger
        newly_documented = 0
    elif plan.get("mode") == "new":
        proposed = {**ledger, "scans": ledger["scans"] + new}
        newly_documented = len(new)
    else:
        raise ValueError("Unsupported planner mode")
    tracked = plan["tracked_bundles"]
    if (len(ledger["scans"]) != plan["documented_scans_before"] or
            len(new) + len(incomplete) != plan["selected_small_sources"] or
            len(proposed["scans"]) + (
                tracked - len(proposed["scans"])) != tracked):
        raise ValueError("Coverage conservation failed")
    # In recheck mode source paths also exist in the committed ledger.
    # The planner already rejects duplicates inside each collection, so
    # validate the canonical union rather than inventing duplicate Git paths.
    accounted_paths = sorted(set(expected) |
                             {e["bundle"] for e in ledger["scans"]} |
                             {e["bundle"] for e in
                              ledger.get("known_lfs_not_yet_scanned", [])})
    validate_ledger(proposed, accounted_paths)
    return {
        "schema_version": 1, "tracked_bundles": tracked,
        "documented_before": plan["documented_scans_before"],
        "new_documented": newly_documented,
        "source_reverified": len(new) - newly_documented,
        "documented_after": len(proposed["scans"]),
        "unscanned_after": tracked - len(proposed["scans"]),
        "unparseable_attempts": incomplete,
        "source_run_url": run_url,
        "warning": "Proposed ledger generated from measured CI evidence; review before committing. MonoBehaviour metadata is not authoritative gameplay.",
    }, proposed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="command", required=True)
    p = modes.add_parser("plan")
    p.add_argument("--ref", default="HEAD")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--matrix", type=Path, required=True)
    p.add_argument("--expected-tracked", type=int, default=330)
    for mode in ("checkout", "scan"):
        p = modes.add_parser(mode)
        p.add_argument("--plan", required=True, type=Path)
        p.add_argument("--batch-id", required=True, type=int)
        if mode == "scan":
            p.add_argument("--output", required=True, type=Path)
    p = modes.add_parser("consolidate")
    p.add_argument("--plan", required=True, type=Path)
    p.add_argument("--evidence-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--proposed-ledger", required=True, type=Path)
    p.add_argument("--run-url", required=True)
    args = parser.parse_args()
    if args.command == "plan":
        entries = tree_entries(args.ref)
        ledger = json.loads(DEFAULT_LEDGER.read_text(encoding="utf-8"))
        plan = make_plan(entries, ledger, expected_tracked=args.expected_tracked)
        args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
        args.matrix.write_text(json.dumps({
            "include": [{"id": group["id"]} for group in plan["batches"]]
        }, separators=(",", ":")) + "\n")
        print(json.dumps({k: plan[k] for k in
                          ("tracked_bundles", "documented_scans_before",
                           "eligible_small_sources")}, sort_keys=True))
        return
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if args.command == "checkout":
        sources = selected_batch(plan, args.batch_id)
        subprocess.run(["git", "sparse-checkout", "set", "--no-cone",
                        "reconstruction/", *[e["bundle"] for e in sources]],
                       check=True)
    elif args.command == "scan":
        results = run_batch(plan, args.batch_id, args.output)
        print(json.dumps({
            "batch": args.batch_id,
            "sources": len(results),
            "partial": sum(e["source_status"] != "bounded_mono_numeric_complete"
                           for e in results),
        }))
    else:
        ledger = json.loads(DEFAULT_LEDGER.read_text(encoding="utf-8"))
        report, proposed = consolidate(plan, args.evidence_dir, ledger,
                                       run_url=args.run_url)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        args.proposed_ledger.write_text(
            json.dumps(proposed, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
