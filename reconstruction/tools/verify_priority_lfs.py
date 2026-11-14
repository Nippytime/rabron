#!/usr/bin/env python3
"""Verify exact, authorized Git LFS source bytes without extracting game media.

A source is allowed only if its path, original Git LFS SHA-256 and byte count
are registered in reconstruction/data/extraction_coverage.json. Checks pointer
metadata before download and actual UnityFS bytes afterward. Never accepts
LFS pointer text as a scanned bundle.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

PREFIX = "StreamingAssets/aa/StandaloneWindows64/"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
POINTER = re.compile(
    r"version https://git-lfs\.github\.com/spec/v1\n"
    r"oid sha256:([0-9a-f]{64})\n"
    r"size ([1-9][0-9]*)\n?\Z"
)


def source_entry(ledger, bundle):
    """Get only the two explicitly tracked LFS sources, before or after scan."""
    if ledger.get("schema_version") != 1 or not bundle.startswith(PREFIX):
        raise ValueError("Unrecognized evidence ledger or bundle path")
    pending = [
        e for e in ledger.get("known_lfs_not_yet_scanned", ())
        if e.get("bundle") == bundle
    ]
    scanned = [
        e for e in ledger.get("scans", ())
        if e.get("bundle") == bundle and "lfs_oid_sha256" in e
    ]
    entries = pending + scanned
    if len(entries) != 1:
        raise ValueError("Expected exactly one registered LFS source: " + bundle)
    entry = entries[0]
    oid = entry["lfs_oid_sha256"]
    size = entry.get("size_bytes")
    if not isinstance(oid, str) or not SHA256.fullmatch(oid):
        raise ValueError("Invalid recorded LFS SHA-256")
    if type(size) is not int or size <= 0:
        raise ValueError("Invalid recorded LFS byte length")
    if "sha256" in entry and entry["sha256"] != oid:
        raise ValueError("Source scan SHA-256 differs from registered LFS OID")
    return {"bundle": bundle, "lfs_oid_sha256": oid, "size_bytes": size}


def verify_source(path, evidence, *, phase):
    if phase not in ("pointer", "bytes"):
        raise ValueError("phase must be pointer or bytes")
    if path.as_posix() != evidence["bundle"]:
        raise ValueError("Source path differs from LFS registry")
    if phase == "pointer":
        if path.stat().st_size > 1024:
            raise ValueError("Expected original Git LFS pointer before download")
        content = path.read_bytes()
        match = POINTER.fullmatch(content.decode("ascii"))
        if not match:
            raise ValueError("Invalid original Git LFS pointer metadata")
        sha, size = match.groups()
        if sha != evidence["lfs_oid_sha256"] or int(size) != evidence["size_bytes"]:
            raise ValueError("Original Git LFS pointer does not match evidence")
        return {**evidence, "phase": phase, "verified": True}

    with path.open("rb") as file:
        magic = file.read(7)
    if magic != b"UnityFS":
        raise ValueError("Expected downloaded UnityFS bytes, not an LFS pointer")
    actual_size = path.stat().st_size
    if actual_size != evidence["size_bytes"]:
        raise ValueError("Downloaded UnityFS size differs from LFS metadata")
    with path.open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    if digest != evidence["lfs_oid_sha256"]:
        raise ValueError("Downloaded UnityFS SHA-256 differs from LFS OID")
    return {**evidence, "phase": phase, "sha256": digest,
            "verified": True, "unityfs_magic": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Exact registered repository-relative path")
    parser.add_argument("--phase", required=True, choices=("pointer", "bytes"))
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional small verification JSON")
    args = parser.parse_args()
    evidence = source_entry(
        json.loads(args.ledger.read_text(encoding="utf-8")), args.bundle
    )
    result = verify_source(Path(args.bundle), evidence, phase=args.phase)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
