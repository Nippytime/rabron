#!/usr/bin/env python3
"""Read-only Unity AssetBundle inventory with provenance and explicit parse gaps.

Install UnityPy==1.25.4 to scan a real bundle. No models, textures, sounds or
unredacted text assets are exported; only object identity and scalar config.
"""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def numeric_fields(data, *, max_fields=512, max_depth=16):
    """Return sorted, scalar-only field paths and a truthful truncation flag."""
    if max_fields < 1 or max_depth < 0:
        raise ValueError("Limits must be positive (depth may be zero)")
    found = []
    depth_skipped = False
    stack = [("$", data, 0)]
    while stack:
        path, node, depth = stack.pop()
        if isinstance(node, bool) or node is None:
            continue
        if isinstance(node, (int, float)):
            if isinstance(node, float) and not math.isfinite(node):
                continue
            if len(found) == max_fields:
                return sorted(found, key=lambda item: item["path"]), True
            found.append({"path": path, "value": node})
        elif isinstance(node, dict):
            if depth < max_depth:
                stack.extend((f"{path}.{key}", value, depth + 1)
                             for key, value in sorted(node.items(),
                                                       key=lambda item: str(item[0]),
                                                       reverse=True))
            elif node:
                depth_skipped = True
        elif isinstance(node, (list, tuple)):
            if depth < max_depth:
                stack.extend((f"{path}[{index}]", value, depth + 1)
                             for index, value in reversed(list(enumerate(node))))
            elif node:
                depth_skipped = True
    # A skipped nested subtree may contain numerics. Mark extraction partial
    # instead of reporting false completeness. Empty containers are harmless.
    return sorted(found, key=lambda item: item["path"]), depth_skipped


def scan_bundle(path: Path, *, max_behaviours=None, max_fields=512,
                max_depth=16):
    if max_fields < 1 or max_depth < 0:
        raise ValueError("max_fields must be positive and max_depth nonnegative")
    # A successful git checkout can still contain a small Git LFS pointer
    # instead of the requested Unity binary when the LFS object was not fetched.
    with path.open("rb") as source:
        signature = source.read(128)
    if signature.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError(f"Not a Unity bundle: {path} is a Git LFS pointer")
    if not signature.startswith(b"UnityFS"):
        raise ValueError(f"Not a UnityFS bundle: {path}")
    try:
        import UnityPy
        from UnityPy.helpers import TypeTreeHelper
    except ImportError as exc:
        raise RuntimeError("Install UnityPy==1.25.4 before binary scanning") from exc

    # Disables fast native typetree parsing that may crash on unexpected schema.
    TypeTreeHelper.read_typetree_boost = False

    with path.open("rb") as source:
        sha256 = hashlib.file_digest(source, "sha256").hexdigest()

    environment = UnityPy.load(str(path))
    objects = Counter()
    errors = Counter()
    records = []
    total_behaviours = 0
    cap_hit = False

    for reader in environment.objects:
        kind = reader.type.name
        objects[kind] += 1
        if kind != "MonoBehaviour":
            continue
        total_behaviours += 1
        if max_behaviours is not None and len(records) >= max_behaviours:
            cap_hit = True
            continue

        entry = {"path_id": str(reader.path_id), "class": kind}
        try:
            parsed = reader.parse_as_dict()
            entry["name"] = str(parsed.get("m_Name", ""))
            entry["numeric_fields"], entry["fields_truncated"] = numeric_fields(
                parsed, max_fields=max_fields, max_depth=max_depth
            )
            entry["status"] = "parsed"
        except (Exception) as exc:
            # Missing MonoBehaviour typetrees must stay visible as missing data.
            reason = type(exc).__name__
            errors[reason] += 1
            entry["status"] = "unparsed"
            entry["error_type"] = reason
            entry["numeric_fields"] = []
        records.append(entry)

    parsed_count = sum(entry["status"] == "parsed" for entry in records)
    result = {
        "tool": "UnityPy",
        "tool_version": getattr(UnityPy, "__version__", "unknown"),
        "source": str(path),
        "sha256": sha256,
        "size_bytes": path.stat().st_size,
        "numeric_field_limit": max_fields,
        "numeric_depth_limit": max_depth,
        "unityfs_magic": path.open("rb").read(8).startswith(b"UnityFS"),
        "objects_by_type": dict(sorted(objects.items())),
        "monobehaviours_total": total_behaviours,
        "monobehaviours_attempted": len(records),
        "monobehaviours_parsed": parsed_count,
        "unparsed_reason_counts": dict(sorted(errors.items())),
        "limit_reached": cap_hit,
        "complete_numeric_extraction": (
            not cap_hit and parsed_count == total_behaviours
            and not any(e.get("fields_truncated") for e in records)
        ),
        "records": records,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-behaviours", type=int, default=None)
    parser.add_argument("--max-fields", type=int, default=512)
    parser.add_argument("--max-depth", type=int, default=16,
                        help="Nested field traversal depth; exceeding it now marks scan incomplete")
    args = parser.parse_args()

    if args.max_behaviours is not None and args.max_behaviours < 1:
        parser.error("--max-behaviours must be >= 1")
    if args.max_fields < 1 or args.max_depth < 0:
        parser.error("--max-fields must be >= 1 and --max-depth must be >= 0")
    result = scan_bundle(args.bundle, max_behaviours=args.max_behaviours,
                         max_fields=args.max_fields, max_depth=args.max_depth)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "sha256", "objects_by_type", "monobehaviours_total",
        "monobehaviours_parsed", "unparsed_reason_counts",
        "complete_numeric_extraction", "limit_reached")}, sort_keys=True))


if __name__ == "__main__":
    main()
