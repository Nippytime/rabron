"""Pure fail-closed five-city-ID original numeric retry tests."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from reconstruction.tools.city_cap_index import evidence, verify_index
from reconstruction.tools.city_targeted_numeric_retry import (
    BYTES, CITY, DEPTH, FIELDS, MONOS, SHA, TARGET_FIELDS, RETRY_FIELDS,
    retry_city, verify_report,
)

ROOT = Path(__file__).resolve().parents[1]


class Scanner:
    def __init__(self, measured, index, *, invalid=None):
        self.measured = measured
        self.index = index
        self.invalid = invalid
        self.calls = []

    def __call__(self, path, *, path_ids, expected_sha256, max_fields, max_depth):
        self.calls.append((max_fields, max_depth, frozenset(path_ids)))
        source = self.measured
        selected = [x for x in self.index["capped_objects"]
                    if x["path_id"] in path_ids]
        if max_fields == FIELDS:
            capped = {x["path_id"] for x in selected}
        elif max_fields == TARGET_FIELDS:
            capped = {x["path_id"] for x in selected[3:]}
        else:
            capped = {x["path_id"] for x in selected[-1:]}
        records = []
        for item in selected:
            capped_flag = item["path_id"] in capped
            observed = max_fields if capped_flag else 7
            records.append({
                "serialized_file": item["serialized_file"],
                "path_id": item["path_id"], "status": "parsed",
                "name": item["display_name"], "fields_truncated": capped_flag,
                "numeric_truncation_reasons": ["field_limit"] if capped_flag else [],
                "numeric_fields": [{"path": "$.items[%d]" % i, "value": i}
                                   for i in range(observed)],
            })
        report = {
            "source": CITY, "sha256": SHA, "size_bytes": BYTES,
            "numeric_field_limit": max_fields, "numeric_depth_limit": max_depth,
            "unityfs_magic": True, "objects_by_type": source["objects_by_type"],
            "monobehaviours_total": MONOS,
            "monobehaviours_attempted": len(records),
            "monobehaviours_parsed": len(records),
            "selected_path_ids": sorted(path_ids), "missing_path_ids": [],
            "limit_reached": False, "complete_numeric_extraction": False,
            "selected_numeric_extraction_complete": not capped,
            "records": records,
        }
        if self.invalid == "sha":
            report["sha256"] = "0" * 64
        elif self.invalid == "missing":
            report["records"].pop()
        elif self.invalid == "swapped":
            report["records"][0]["serialized_file"] = "different-source-file"
        elif self.invalid == "duplicate":
            report["records"][1]["serialized_file"] = report["records"][0]["serialized_file"]
            report["records"][1]["path_id"] = report["records"][0]["path_id"]
        elif self.invalid == "unbounded":
            report["numeric_field_limit"] = max_fields + 1
        elif self.invalid == "false_complete":
            report["selected_numeric_extraction_complete"] = True
        return report


class CityTargetedNumericRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measured = evidence(json.loads(
            (ROOT / "data/extraction_coverage.json").read_text()))
        cls.index = json.loads(
            (ROOT / "data/city_scene_numeric_cap_identities.json").read_text())
        verify_index(cls.index, cls.measured)

    def test_uses_only_original_five_and_bounded_three_stages(self):
        scanner = Scanner(self.measured, self.index)
        with patch("reconstruction.tools.streamed_unityfs.streamed_unityfs"):
            result = retry_city(self.measured, self.index, scanner)
        verify_report(result, self.index)
        self.assertEqual(result["selected_count"], 5)
        self.assertEqual(result["resolved"], 4)
        self.assertEqual(result["unresolved"], 1)
        self.assertEqual(result["adaptive_retried"], 2)
        self.assertFalse(result["full_bundle_numeric_extraction_complete"])
        ids = {item["path_id"] for item in self.index["capped_objects"]}
        self.assertEqual(scanner.calls, [
            (2048, 32, frozenset(ids)),
            (8192, 32, frozenset(ids)),
            (16384, 48, frozenset(["344310", "7968"])),
        ])
        self.assertEqual(result["outcomes"][-1]["status"], "still_capped")
        self.assertEqual(result["outcomes"][0]["status"], "resolved")
        self.assertNotIn('"value":', json.dumps(result))

    def test_source_identity_drift_and_missing_selected_are_fatal(self):
        for reason in ("sha", "missing", "swapped", "duplicate",
                       "unbounded", "false_complete"):
            with self.subTest(reason=reason):
                scanner = Scanner(self.measured, self.index, invalid=reason)
                with patch("reconstruction.tools.streamed_unityfs.streamed_unityfs"):
                    with self.assertRaises(ValueError):
                        retry_city(self.measured, self.index, scanner)

    def test_baseline_five_field_limits_must_reproduce(self):
        scanner = Scanner(self.measured, self.index)
        original = scanner.__call__

        def tampered(*args, **kwargs):
            result = original(*args, **kwargs)
            if kwargs["max_fields"] == FIELDS:
                result["records"][0]["numeric_truncation_reasons"] = []
                result["records"][0]["fields_truncated"] = False
            return result

        with patch("reconstruction.tools.streamed_unityfs.streamed_unityfs"):
            with self.assertRaisesRegex(ValueError, "did not reproduce"):
                retry_city(self.measured, self.index, tampered)

    def test_rejects_false_numeric_completeness_and_forged_counts(self):
        scanner = Scanner(self.measured, self.index)
        with patch("reconstruction.tools.streamed_unityfs.streamed_unityfs"):
            clean = retry_city(self.measured, self.index, scanner)
        for key, value in (
                ("source_sha256", "0" * 64),
                ("resolved", 5),
                ("unresolved", 0),
                ("adaptive_retried", 0),
                ("full_bundle_numeric_extraction_complete", True),
                ("targeted_numeric_extraction_complete", True),
                ("selected_count", 0)):
            with self.subTest(key=key):
                bad = {**clean, key: value}
                with self.assertRaises(ValueError):
                    verify_report(bad, self.index)
        bad = copy.deepcopy(clean)
        bad["outcomes"][-1]["status"] = "resolved"
        with self.assertRaises(ValueError):
            verify_report(bad, self.index)

    def test_report_stays_metadata_only(self):
        scanner = Scanner(self.measured, self.index)
        with patch("reconstruction.tools.streamed_unityfs.streamed_unityfs"):
            report = retry_city(self.measured, self.index, scanner)
        self.assertEqual(len(report["outcomes"]), 5)
        self.assertEqual(
            report["outcomes"][-1]["serialized_file"],
            "CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets",
        )
        self.assertTrue(all(len(x["sample_numeric_field_paths"]) <= 8
                            for x in report["outcomes"]))


if __name__ == "__main__":
    unittest.main()
