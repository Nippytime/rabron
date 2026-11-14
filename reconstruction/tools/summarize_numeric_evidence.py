#!/usr/bin/env python3
"""Classify source-anchored numeric Unity fields without inventing gameplay formulas.

Input: JSON exported by extract_unity_bundle.py.
Output: small, deterministic per-bundle evidence summary (not recovered code).
"""

import argparse
import json
from collections import Counter
from pathlib import Path

GROUP_TOKENS = {
    "economy": ("cash", "money", "price", "cost", "tax", "profit", "deposit",
                "launder", "sell", "loot", "bribe", "salary", "fence", "reward"),
    "combat": ("damage", "health", "armor", "bullet", "spread", "recoil",
               "accuracy", "weapon", "ammo", "stamina", "fire", "reload"),
    "progression": ("experience", "authority", "level", "rank", "skill",
                    "jail", "sentence", "progress"),
    "timing_and_world": ("speed", "time", "radius", "range", "rate", "duration",
                         "cooldown", "distance", "weight", "chance",
                         "probability", "capacity", "multiplier"),
}

REFERENCE_FRAGMENTS = (
    "m_fileid", "m_pathid", "m_script", "m_gameobject",
    "m_tableentryreference", "m_localvariables", "_localizedstring",
    "m_fallbackstate", "m_waitforcompletion", "idinternal",
    "groupidinternal", "references.version", ".m_enabled",
    ".rid", "references.count",
)

ANIMATION_FRAGMENTS = (
    ".m_curve", ".m_clips[", ".tracks[", ".m_keyframes",
    ".m_rotation", ".m_position", ".m_scale", ".m_keyframe",
)


def classify_asset(name: str) -> str:
    lower = name.lower()
    if "viewdescription" in lower or lower.endswith("localization") or "style" in lower:
        return "client_presentation"
    if "viewconfiguration" in lower or "preset" in lower or "settings" in lower:
        return "client_configuration"
    if "references" in lower or "reference" in lower:
        return "content_reference"
    return "unclassified"


def classify_field(path: str) -> str | None:
    """Pick first matching category; none means no formula implication."""
    path_lower = path.lower()
    if any(part in path_lower for part in REFERENCE_FRAGMENTS):
        return None
    if any(part in path_lower for part in ANIMATION_FRAGMENTS):
        return None
    # Match on *field* path, not the asset name; avoid claiming an "economy"
    # field exists solely because an asset is called "MoneyWorkbench".
    for category, tokens in GROUP_TOKENS.items():
        if any(token in path_lower for token in tokens):
            return category
    return None


def summarize(manifest: dict, *, samples_per_category: int = 30) -> dict:
    if samples_per_category < 0:
        raise ValueError("samples_per_category must not be negative")
    required = ("sha256", "source", "records", "monobehaviours_total",
                "monobehaviours_attempted", "monobehaviours_parsed",
                "complete_numeric_extraction")
    missing = [name for name in required if name not in manifest]
    if missing:
        raise ValueError("Invalid scanner manifest; missing " + ", ".join(missing))

    buckets = {name: [] for name in GROUP_TOKENS}
    asset_categories = Counter()
    skipped_ref_fields = 0
    candidates_total = Counter()
    truncated = 0

    for record in manifest["records"]:
        asset_name = record.get("name") or ""
        label = classify_asset(asset_name)
        asset_categories[label] += 1
        truncated += bool(record.get("fields_truncated"))
        for field in record.get("numeric_fields", ()):
            category = classify_field(field["path"])
            if category is None:
                skipped_ref_fields += 1
                continue
            candidates_total[category] += 1
            buckets[category].append({
                "asset": asset_name,
                "asset_kind": label,
                "path_id": record["path_id"],
                "field": field["path"],
                "value": field["value"],
            })

    priority = {
        "unclassified": 0,
        "client_configuration": 1,
        "content_reference": 2,
        "client_presentation": 3,
    }
    groups = {}
    for name, records in buckets.items():
        records.sort(key=lambda entry: (
            priority[entry["asset_kind"]],
            entry["asset"], entry["path_id"], entry["field"],
        ))
        groups[name] = {
            "matching_numeric_fields": candidates_total[name],
            "sample_size": min(len(records), samples_per_category),
            "examples": records[:samples_per_category],
        }

    return {
        "source": manifest["source"],
        "source_sha256": manifest["sha256"],
        "object_counts": manifest.get("objects_by_type", {}),
        "monobehaviours_total": manifest["monobehaviours_total"],
        "monobehaviours_attempted": manifest["monobehaviours_attempted"],
        "monobehaviours_parsed": manifest["monobehaviours_parsed"],
        "records_with_truncated_numeric_fields": truncated,
        "complete_numeric_extraction": manifest["complete_numeric_extraction"],
        "asset_category_counts": dict(sorted(asset_categories.items())),
        "numeric_fields_without_target_keywords_or_filtered": skipped_ref_fields,
        "candidate_field_groups": groups,
        "warning": ("Fields are source-backed but NOT validated as game or "
                    "server formulas; inspect asset_kind and source. "
                    "Client presentation/animation fields are not combat or economy truth."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--samples-per-category", type=int, default=30)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    summary = summarize(data, samples_per_category=args.samples_per_category)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "bundle": summary["source"],
        "attempted": summary["monobehaviours_attempted"],
        "parsed": summary["monobehaviours_parsed"],
        "partial": not summary["complete_numeric_extraction"],
        "asset_categories": summary["asset_category_counts"],
        "candidate_counts": {name: group["matching_numeric_fields"]
                             for name, group in summary["candidate_field_groups"].items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
