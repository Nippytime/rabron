"""Fail-closed tests for five original city-scene capped object IDs."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.city_cap_index import (
    BYTES, CAPS, CITY, DEPTH, FIELDS, MONOS, SHA, TOTAL_OBJECTS,
    build_index, evidence, verify_index,
)

ROOT = Path(__file__).resolve().parents[1]
CITY_LEDGER = ROOT / "data/extraction_coverage.json"


def city_record():
    data = json.loads(CITY_LEDGER.read_text(encoding="utf-8"))
    return evidence(data)


def raw_fixture(source):
    records = []
    for i in range(MONOS):
        reasons = ["field_limit"] if i < CAPS else []
        records.append({
            "serialized_file": "city-main", "path_id": str(i + 1),
            "status": "parsed", "name": f"CityItem_{i + 1}",
            "fields_truncated": bool(reasons),
            "numeric_truncation_reasons": reasons,
            "numeric_fields": [{"path": "$.value", "value": i}] if i < CAPS else [],
        })
    return {
        "source": CITY, "sha256": SHA, "size_bytes": BYTES,
        "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
        "monobehaviours_total": MONOS, "monobehaviours_attempted": MONOS,
        "monobehaviours_parsed": MONOS, "limit_reached": False,
        "complete_numeric_extraction": False, "unityfs_magic": True,
        "selected_path_ids": None, "missing_path_ids": [],
        "objects_by_type": source["objects_by_type"],
        "records": records,
    }


class CityCapIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = city_record()
        cls.fixture = raw_fixture(cls.source)

    def test_integrated_original_baseline_is_exact(self):
        self.assertEqual(self.source["numeric_field_cap_records"], 5)
        self.assertEqual(self.source["monobehaviours_total"], 14467)
        self.assertEqual(sum(self.source["objects_by_type"].values()), 366174)
        self.assertEqual(self.source["lfs_oid_sha256"], SHA)

    def test_reports_only_five_scoped_capped_identities_no_values(self):
        index = build_index(self.fixture, self.source)
        verify_index(index, self.source)
        self.assertEqual(index["capped_count"], CAPS)
        self.assertEqual(len(index["capped_objects"]), CAPS)
        self.assertEqual(index["capped_objects"][0]["path_id"], "1")
        self.assertEqual(index["capped_objects"][0]["serialized_file"], "city-main")
        self.assertFalse(index["full_numeric_extraction_complete"])
        self.assertNotIn("numeric_fields", json.dumps(index))
        self.assertNotIn('"value":', json.dumps(index))

    def test_wrong_binary_identity_source_or_bounded_limits_fail(self):
        for key, wrong in (
                ("source", "other.bundle"), ("sha256", "0" * 64),
                ("size_bytes", BYTES - 1), ("numeric_field_limit", FIELDS + 1),
                ("numeric_depth_limit", DEPTH + 1),
                ("complete_numeric_extraction", True),
                ("monobehaviours_total", MONOS - 1),
                ("objects_by_type", {"MonoBehaviour": MONOS})):
            with self.subTest(key=key):
                raw = {**self.fixture, key: wrong}
                with self.assertRaises(ValueError):
                    build_index(raw, self.source)

    def test_zero_missing_extra_or_unparsed_caps_fail(self):
        for mutation in ("none", "six", "unparsed", "inconsistent", "missing_id"):
            with self.subTest(mutation=mutation):
                raw = copy.deepcopy(self.fixture)
                row = raw["records"][0]
                if mutation == "none":
                    row["fields_truncated"] = False
                    row["numeric_truncation_reasons"] = []
                elif mutation == "six":
                    raw["records"][CAPS]["fields_truncated"] = True
                    raw["records"][CAPS]["numeric_truncation_reasons"] = ["field_limit"]
                elif mutation == "unparsed":
                    row["status"] = "unparsed"
                elif mutation == "inconsistent":
                    row["fields_truncated"] = False
                else:
                    row.pop("serialized_file")
                with self.assertRaises(ValueError):
                    build_index(raw, self.source)

    def test_duplicate_identity_within_same_file_rejected(self):
        raw = copy.deepcopy(self.fixture)
        raw["records"][1]["path_id"] = raw["records"][0]["path_id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_index(raw, self.source)

    def test_composite_id_allows_cross_file_same_path_id(self):
        raw = copy.deepcopy(self.fixture)
        raw["records"][1]["path_id"] = raw["records"][0]["path_id"]
        raw["records"][1]["serialized_file"] = "another-city-file"
        index = build_index(raw, self.source)
        self.assertEqual(len(index["capped_objects"]), CAPS)
        verify_index(index, self.source)

    def test_reconcile_rejects_forged_missing_and_unsorted(self):
        baseline = build_index(self.fixture, self.source)
        for key, replacement in (
                ("capped_count", 4), ("full_numeric_extraction_complete", True),
                ("source_sha256", "0" * 64)):
            with self.subTest(key=key):
                altered = {**baseline, key: replacement}
                with self.assertRaises(ValueError):
                    verify_index(altered, self.source)
        for mutate in ("empty", "duplicate", "unsorted", "bad_status"):
            with self.subTest(mutate=mutate):
                altered = copy.deepcopy(baseline)
                if mutate == "empty":
                    altered["capped_objects"] = []
                elif mutate == "duplicate":
                    altered["capped_objects"][1] = altered["capped_objects"][0]
                elif mutate == "unsorted":
                    altered["capped_objects"].reverse()
                else:
                    altered["capped_objects"][0]["status"] = "resolved"
                with self.assertRaises(ValueError):
                    verify_index(altered, self.source)

    def test_committed_five_original_cap_ids_match_measured_evidence(self):
        path = ROOT / "data/city_scene_numeric_cap_identities.json"
        self.assertTrue(path.is_file(), "Actual first-source artifact must be committed")
        index = json.loads(path.read_text(encoding="utf-8"))
        verify_index(index, self.source)
        self.assertEqual(
            [(item["serialized_file"], item["path_id"])
             for item in index["capped_objects"]],
            [
                ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344196"),
                ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344216"),
                ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344248"),
                ("CAB-198a5be741d1a7bef84198e0c583d1cf", "344310"),
                ("CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets", "7968"),
            ],
        )
        self.assertTrue(all(
            item["truncation_reasons"] == ["field_limit"] and
            item["visible_numeric_field_count"] == FIELDS and
            item["status"] == "capped"
            for item in index["capped_objects"]
        ))
        self.assertEqual(index["capped_objects"][-1]["display_name"],
                         "WaterQuadTreeData")
        self.assertFalse(index["full_numeric_extraction_complete"])

    def test_original_record_tampering_rejected(self):
        real = json.loads(CITY_LEDGER.read_text(encoding="utf-8"))
        source = next(x for x in real["scans"] if x["bundle"] == CITY)
        for key, wrong in (
                ("numeric_field_cap_records", 0), ("sha256", "0" * 64),
                ("unparsed_records", 1), ("numeric_field_limit", 8192)):
            with self.subTest(key=key):
                bad = copy.deepcopy(real)
                row = next(x for x in bad["scans"] if x["bundle"] == CITY)
                row[key] = wrong
                with self.assertRaises(ValueError):
                    evidence(bad)


if __name__ == "__main__":
    unittest.main()
