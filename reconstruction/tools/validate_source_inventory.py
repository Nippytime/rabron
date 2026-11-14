"""Fail-closed cross-check of read-only UnityFS scalar scan artifacts.

A scanner process exiting successfully is not evidence that its source and
object accounting are intact. Explicitly distinguish a valid zero-MonoBehaviour
asset from missing, truncated, or unparsed MonoBehaviour records.
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def validate_object_identities(records, *, id_field="path_id"):
    """Never collapse same-file duplicates or unscoped cross-file path IDs."""
    ids = [record.get(id_field) for record in records]
    if any(not isinstance(value, str) or
           re.fullmatch(r"-?[0-9]+", value) is None for value in ids):
        raise ValueError("Missing or invalid Unity path ID")
    duplicates = {key for key, count in Counter(ids).items() if count > 1}
    for record in records:
        scope = record.get("serialized_file")
        if scope is not None and (not isinstance(scope, str) or not scope.strip()):
            raise ValueError("Invalid serialized file identity")
        if record[id_field] in duplicates and scope is None:
            raise ValueError("Duplicate Unity path IDs lack serialized-file scope")
    identities = [(record.get("serialized_file"), record[id_field])
                  for record in records]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate Unity object ID within serialized file")


def validate(manifest, summary, *, source, expected_size, max_fields, max_depth):
    if (expected_size < 1 or max_fields < 1 or max_depth < 0 or
            manifest.get("source") != source or
            summary.get("source") != source):
        raise ValueError("Source or scan arguments do not match recorded input")
    path = Path(source)
    if not path.is_file() or path.stat().st_size != expected_size:
        raise ValueError("Original UnityFS source missing or byte size differs")
    with path.open("rb") as handle:
        if handle.read(7) != b"UnityFS":
            raise ValueError("Source is not the original UnityFS binary")
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if (manifest.get("sha256") != digest or
            summary.get("source_sha256") != digest or
            manifest.get("size_bytes") != expected_size):
        raise ValueError("Measured source fingerprint differs between artifacts")
    if (manifest.get("numeric_field_limit") != max_fields or
            manifest.get("numeric_depth_limit") != max_depth or
            manifest.get("limit_reached") is not False or
            manifest.get("selected_path_ids") is not None):
        raise ValueError("Expected unrestricted full MonoBehaviour inventory")

    records = manifest.get("records")
    object_types = manifest.get("objects_by_type")
    if not isinstance(records, list) or not isinstance(object_types, dict):
        raise ValueError("Missing inventory records or object type counts")
    if not object_types or sum(object_types.values()) <= 0:
        raise ValueError("No Unity objects inventoried")
    total = manifest.get("monobehaviours_total")
    parsed = manifest.get("monobehaviours_parsed")
    attempted = manifest.get("monobehaviours_attempted")
    if (type(total) is not int or type(parsed) is not int or
            type(attempted) is not int or total < 0 or
            not 0 <= parsed <= attempted == total == len(records) or
            object_types.get("MonoBehaviour", 0) != total):
        raise ValueError("MonoBehaviour counts do not reconcile")
    validate_object_identities(records)
    if any(record.get("status") not in ("parsed", "unparsed") for record in records):
        raise ValueError("Unrecognized MonoBehaviour parsing status")
    success = sum(record["status"] == "parsed" for record in records)
    missing = total - success
    truncated = sum(bool(record.get("fields_truncated")) for record in records)
    if (success != parsed or
            summary.get("monobehaviours_parsed") != parsed or
            summary.get("monobehaviours_attempted") != attempted or
            summary.get("monobehaviours_total") != total or
            summary.get("records_with_truncated_numeric_fields") != truncated or
            summary.get("object_counts") != object_types):
        raise ValueError("Summarized counts contradict source inventory")
    for record in records:
        reasons = record.get("numeric_truncation_reasons", [])
        if (not isinstance(reasons, list) or
                any(reason not in ("field_limit", "depth_limit")
                    for reason in reasons) or
                (record.get("status") == "parsed" and
                 bool(reasons) != bool(record.get("fields_truncated")))):
            raise ValueError("Numeric truncation flags are inconsistent")
    complete = missing == 0 and truncated == 0
    if (manifest.get("complete_numeric_extraction") is not complete or
            summary.get("complete_numeric_extraction") is not complete):
        raise ValueError("False completeness result in source inventory")
    return {
        "source": source,
        "sha256": digest,
        "monobehaviours_total": total,
        "parsed": success,
        "unparsed": missing,
        "truncated": truncated,
        "bounded_mono_numeric_complete": complete,
        "object_types": object_types,
        "scope_warning": (
            "Client MonoBehaviour numeric-field inventory only; excludes "
            "authoritative server formulas, IL2CPP methods and media recovery."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-size", type=int, required=True)
    parser.add_argument("--max-fields", type=int, required=True)
    parser.add_argument("--max-depth", type=int, required=True)
    args = parser.parse_args()
    result = validate(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        json.loads(args.summary.read_text(encoding="utf-8")),
        source=args.source,
        expected_size=args.expected_size,
        max_fields=args.max_fields,
        max_depth=args.max_depth,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
