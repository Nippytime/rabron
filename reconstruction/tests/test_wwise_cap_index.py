"""Wwise original 274-cap plus one-unparsed strict evidence checks."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.wwise_cap_index import (
    BUNDLE, SHA, BYTES, MONOS, PARSED, CAPS, FIELDS, DEPTH,
    build, evidence, verify,
)

ROOT = Path(__file__).resolve().parents[1]


class OriginalWwiseCapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(
            (ROOT / "data/extraction_coverage.json").read_text(encoding="utf-8"))
        cls.source = evidence(cls.ledger)

    @staticmethod
    def raw():
        records = []
        for i in range(PARSED):
            numeric = [{"path": "$.depth", "value": 1}]
            reasons = ["depth_limit"]
            if i == 0:
                numeric = [{"path": "$.values[%d]" % n, "value": n}
                           for n in range(FIELDS)]
                reasons = ["field_limit"]
            records.append({
                "serialized_file": "WWISE-CAB", "path_id": str(i + 1),
                "status": "parsed", "name": "WwiseObject",
                "numeric_fields": numeric, "numeric_truncation_reasons": reasons,
                "fields_truncated": True,
            })
        records.append({
            "serialized_file": "WWISE-CAB.sharedAssets", "path_id": "-88",
            "status": "unparsed", "error_type": "WwiseMonoObjectBudgetExceeded",
            "numeric_fields": [],
        })
        return {
            "source": BUNDLE, "sha256": SHA, "size_bytes": BYTES,
            "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
            "unityfs_magic": True,
            "objects_by_type": {"AssetBundle": 1, "MonoBehaviour": MONOS},
            "monobehaviours_total": MONOS, "monobehaviours_attempted": MONOS,
            "monobehaviours_parsed": PARSED, "limit_reached": False,
            "selected_path_ids": None, "missing_path_ids": [],
            "complete_numeric_extraction": False, "records": records,
        }

    def test_full_integrated_source_identity_not_numeric_completeness(self):
        self.assertEqual(self.source["numeric_field_cap_records"], CAPS)
        self.assertEqual(self.source["unparsed_records"], 1)
        self.assertEqual(sum(self.source["objects_by_type"].values()), 276)
        self.assertFalse(self.source["bounded_numeric_scan_complete"])

    def test_exact_caps_and_unparsed_without_original_values(self):
        report = build(self.raw(), self.source)
        verify(report, self.source)
        self.assertEqual(len(report["capped_objects"]), CAPS)
        self.assertEqual(len(report["unparsed_objects"]), 1)
        self.assertFalse(report["full_numeric_extraction_complete"])
        self.assertNotIn('"value":', json.dumps(report))
        self.assertNotIn('"numeric_fields":', json.dumps(report))

    def test_forged_source_bounds_or_full_completion_rejected(self):
        for key, wrong in (
                ("source", "other.bundle"), ("sha256", "0" * 64),
                ("size_bytes", BYTES - 1), ("numeric_field_limit", FIELDS + 1),
                ("numeric_depth_limit", DEPTH + 1),
                ("monobehaviours_total", MONOS - 1),
                ("monobehaviours_parsed", MONOS),
                ("objects_by_type", {"MonoBehaviour": MONOS}),
                ("complete_numeric_extraction", True)):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    build({**self.raw(), key: wrong}, self.source)

    def test_missed_duplicate_uncapped_or_forged_unparsed_rejected(self):
        for mode in ("missing", "duplicated", "uncapped", "extra_unparsed",
                     "empty_error", "wrong_status"):
            with self.subTest(mode=mode):
                raw = self.raw()
                if mode == "missing":
                    raw["records"].pop()
                elif mode == "duplicated":
                    raw["records"][1]["path_id"] = "1"
                elif mode == "uncapped":
                    raw["records"][1]["fields_truncated"] = False
                elif mode == "extra_unparsed":
                    raw["records"].append(copy.deepcopy(raw["records"][-1]))
                elif mode == "empty_error":
                    raw["records"][-1]["error_type"] = ""
                else:
                    raw["records"][1]["status"] = "unparsed"
                with self.assertRaises(ValueError):
                    build(raw, self.source)

    def test_reconciliation_rejects_duplicate_or_missing_ids(self):
        original_report = build(self.raw(), self.source)
        for mode in ("missing", "duplicate", "shuffled", "fake_digest",
                     "false_complete", "missing_unparsed"):
            with self.subTest(mode=mode):
                report = copy.deepcopy(original_report)
                if mode == "missing":
                    report["capped_objects"].pop()
                elif mode == "duplicate":
                    report["capped_objects"][1] = report["capped_objects"][0]
                elif mode == "shuffled":
                    report["capped_objects"].reverse()
                elif mode == "fake_digest":
                    report["capped_objects"][0]["numeric_path_sha256"] = "x"
                elif mode == "false_complete":
                    report["full_numeric_extraction_complete"] = True
                else:
                    report["unparsed_objects"] = []
                with self.assertRaises(ValueError):
                    verify(report, self.source)

    def test_modified_original_ledger_is_not_valid(self):
        for k, value in (
                ("sha256", "0" * 64), ("unparsed_records", 0),
                ("numeric_field_cap_records", 273),
                ("numeric_field_limit", 8192)):
            with self.subTest(key=k):
                data = copy.deepcopy(self.ledger)
                row = next(x for x in data["scans"] if x["bundle"] == BUNDLE)
                row[k] = value
                with self.assertRaises(ValueError):
                    evidence(data)

    def test_committed_original_ids_stay_valid_if_present(self):
        path = ROOT / "data/wwise_numeric_cap_identities.json"
        if path.exists():
            verify(json.loads(path.read_text(encoding="utf-8")), self.source)


if __name__ == "__main__":
    unittest.main()
