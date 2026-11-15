"""Synthetic fail-closed tests for original city residual structure metadata."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reconstruction.tools.city_cap_index import evidence, verify_index
from reconstruction.tools.city_targeted_numeric_retry import verify_report as verify_retry
from reconstruction.tools.city_residual_structure import (
    EXPECTED_IDS, ROOT_FIELDS, scan_city, summarize, targets, verify_report,
)

ROOT = Path(__file__).resolve().parents[1]


class ResidualCityShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measured = evidence(json.loads(
            (ROOT / "data/extraction_coverage.json").read_text(encoding="utf-8")))
        cls.index = json.loads(
            (ROOT / "data/city_scene_numeric_cap_identities.json").read_text())
        cls.retry = json.loads(
            (ROOT / "data/city_scene_targeted_numeric_retry.json").read_text())
        verify_index(cls.index, cls.measured)
        verify_retry(cls.retry, cls.index)

    def test_only_original_three_unresolved_city_objects_selected(self):
        self.assertEqual(targets(self.index, self.retry), EXPECTED_IDS)
        modified = copy.deepcopy(self.retry)
        modified["outcomes"][0]["status"] = "resolved"
        with self.assertRaisesRegex(ValueError, "identities changed"):
            targets(self.index, modified)

    def test_structure_does_not_export_values_or_raw_text(self):
        parsed = {
            "z": "PRIVATE-TEXT",
            "a": [{"m_PathID": 7821, "Secret": "private-value"},
                  {"m_PathID": 1290}],
            "m_Flag": True,
            "m_V": 3.14159,
            "m_Meta": {"k": 98765},
        }
        result = summarize(parsed)
        self.assertEqual([r["field"] for r in result["fields"]],
                         ["a", "m_Flag", "m_Meta", "m_V", "z"])
        self.assertEqual(result["fields"][0], {
            "field": "a", "kind": "array", "element_count": 2,
            "first_element_members": ["Secret", "m_PathID"],
        })
        text = json.dumps(result)
        for value in ("PRIVATE-TEXT", "private-value", "7821", "1290",
                      "3.14159", "98765"):
            self.assertNotIn(value, text)
        self.assertEqual(result["fields"][4]["kind"], "text")
        self.assertIsNone(result["fields"][4]["element_count"])

    def test_root_limit_is_explicit_not_false_completion(self):
        result = summarize({f"key{i:03}": i for i in range(ROOT_FIELDS + 3)})
        self.assertEqual(result["root_member_count"], ROOT_FIELDS + 3)
        self.assertTrue(result["root_member_names_truncated"])
        self.assertEqual(len(result["fields"]), ROOT_FIELDS)
        with self.assertRaisesRegex(ValueError, "member-name"):
            summarize({1234: "not a field name"})

    def _fake_scan(self):
        class Reader:
            def __init__(self, scope, pid, structure):
                self.type = SimpleNamespace(name="MonoBehaviour")
                self.assets_file = SimpleNamespace(name=scope)
                self.path_id = int(pid)
                self.byte_size = 120
                self.structure = structure
            def parse_as_dict(self):
                return self.structure

        readers = [Reader(scope, pid, {"Blocks": [
            {"m_PathID": 25, "m_FileID": 0}
        ], "m_Name": "NEVER-EXPORT-ME"}) for scope, pid in EXPECTED_IDS]
        readers.append(SimpleNamespace(type=SimpleNamespace(name="Mesh")))
        measured = {"objects_by_type": {"MonoBehaviour": 3, "Mesh": 1}}
        loader = lambda _path: SimpleNamespace(objects=readers)
        with patch("reconstruction.tools.city_residual_structure.MONOS", 3), \
             patch("reconstruction.tools.city_residual_structure.TOTAL_OBJECTS", 4):
            report = scan_city(measured, EXPECTED_IDS, loader=loader)
            verify_report(report, EXPECTED_IDS)
        # Synthetic source headers are small, but standalone reconciliation
        # must use the actual immutable original source header count contract.
        from reconstruction.tools.city_residual_structure import MONOS, TOTAL_OBJECTS
        report["source_monobehaviours"] = MONOS
        report["source_object_count"] = TOTAL_OBJECTS
        verify_report(report, EXPECTED_IDS)
        return report, readers, measured, loader

    def test_bounded_three_scoped_ids_and_complete_header_count(self):
        report, readers, measured, loader = self._fake_scan()
        self.assertEqual(report["numeric_caps_resolved"], 0)
        self.assertIs(report["numeric_extraction_complete"], False)
        self.assertEqual([x["path_id"] for x in report["outcomes"]],
                         [i[1] for i in EXPECTED_IDS])
        self.assertNotIn("NEVER-EXPORT-ME", json.dumps(report))
        with patch("reconstruction.tools.city_residual_structure.MONOS", 3), \
             patch("reconstruction.tools.city_residual_structure.TOTAL_OBJECTS", 4):
            readers[0].byte_size = 8 * 1024 * 1024 + 1
            with self.assertRaisesRegex(ValueError, "8 MiB"):
                scan_city(measured, EXPECTED_IDS, loader=loader)
            readers[0].byte_size = 120
            readers[0].assets_file.name = "wrong-original-file"
            with self.assertRaisesRegex(ValueError, "Missing selected"):
                scan_city(measured, EXPECTED_IDS, loader=loader)
            readers[0].assets_file.name = EXPECTED_IDS[0][0]
            with self.assertRaisesRegex(ValueError, "inventory changed"):
                scan_city({"objects_by_type": {"MonoBehaviour": 4}}, EXPECTED_IDS,
                          loader=loader)

    def test_first_original_source_artifact_exact_and_still_incomplete(self):
        path = ROOT / "data/city_residual_structure.json"
        self.assertTrue(path.is_file(), "Original-byte Action artifact must be committed")
        raw = path.read_bytes()
        self.assertEqual(len(raw), 4755)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "aecf8a6f32b292ba4114aaf0d4126d0a2d007ee4eb7e4f2499565ee7730b857c")
        report = json.loads(raw)
        verify_report(report, EXPECTED_IDS)
        self.assertEqual(report["numeric_caps_resolved"], 0)
        self.assertIs(report["numeric_extraction_complete"], False)
        self.assertEqual([row["root_member_count"] for row in report["outcomes"]],
                         [9, 5, 6])
        self.assertEqual([row["object_byte_size"] for row in report["outcomes"]],
                         [523360, 507228, 673360])
        members = [
            {field["field"]: field["element_count"] for field in row["fields"]}
            for row in report["outcomes"]
        ]
        self.assertEqual(members[0]["<Renderers>k__BackingField"], 41623)
        self.assertEqual(members[0]["<HidingObjectRenderers>k__BackingField"], 1986)
        self.assertEqual(members[1]["<MeshRenderers>k__BackingField"], 42266)
        self.assertEqual(members[2]["Nodes"], 16810)
        self.assertEqual(members[2]["RootNodeIds"], 225)

    def test_strict_source_report_rejects_forgery_and_payload_leaks(self):
        report, *_ = self._fake_scan()
        for field, altered in (
            ("numeric_caps_resolved", 3),
            ("numeric_extraction_complete", True),
            ("source_sha256", "0" * 64),
            ("size_bytes", 0),
            ("selected_count", 2),
        ):
            with self.subTest(field=field):
                corrupted = copy.deepcopy(report)
                corrupted[field] = altered
                with self.assertRaises(ValueError):
                    verify_report(corrupted, EXPECTED_IDS)

        def reject(mutate):
            corrupted = copy.deepcopy(report)
            mutate(corrupted)
            with self.assertRaises((ValueError, TypeError)):
                verify_report(corrupted, EXPECTED_IDS)

        reject(lambda r: r["outcomes"][0].update({"path_id": "344216"}))
        reject(lambda r: r["outcomes"].reverse())
        reject(lambda r: r["outcomes"][0].update({"raw_value": 1000}))
        reject(lambda r: r["outcomes"][0]["fields"][0].update({"value": 70}))
        reject(lambda r: r["outcomes"][0].update({"root_member_names_truncated": True}))
        reject(lambda r: r["outcomes"][0]["fields"][0].update({"element_count": -1}))
        reject(lambda r: r["outcomes"][0]["fields"][0].update({"kind": "unknown"}))
        reject(lambda r: r["outcomes"][0]["fields"][0].update(
            {"first_element_members": ["z", "a"]}))


if __name__ == "__main__":
    unittest.main()
