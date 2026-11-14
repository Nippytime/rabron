"""Tests scalar normalization independently of UnityPy or any protected assets."""

import hashlib
import math
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from reconstruction.tools.extract_unity_bundle import numeric_fields, scan_bundle


class NumericFieldsTests(unittest.TestCase):
    def test_nested_deterministic_paths(self):
        value = {
            "damage": 23.5,
            "flags": [True, False],
            "weights": [{"chance": 0.1}, {"chance": 0.9}],
            "value": 0,
            "name": "Player",
            "references": None,
        }
        items, truncated = numeric_fields(value)
        self.assertFalse(truncated)
        self.assertEqual(items, [
            {"path": "$.damage", "value": 23.5},
            {"path": "$.value", "value": 0},
            {"path": "$.weights[0].chance", "value": 0.1},
            {"path": "$.weights[1].chance", "value": 0.9},
        ])
        self.assertEqual(numeric_fields(value), (items, False))

    def test_limit_preserves_partial_flag(self):
        items, truncated = numeric_fields({"a": 1, "b": 2}, max_fields=1)
        self.assertTrue(truncated)
        self.assertEqual(items, [{"path": "$.a", "value": 1}])

    def test_explicit_field_and_depth_truncation_reasons(self):
        fields, reasons = numeric_fields({"outer": {"inner": 42}, "top": 7},
                                         max_fields=1, max_depth=1,
                                         return_reasons=True)
        self.assertEqual(fields, [{"path": "$.top", "value": 7}])
        self.assertEqual(reasons, ["depth_limit"])

        fields, reasons = numeric_fields({"first": 1, "second": 2},
                                         max_fields=1, return_reasons=True)
        self.assertEqual(fields, [{"path": "$.first", "value": 1}])
        self.assertEqual(reasons, ["field_limit"])
        fields, reasons = numeric_fields({"safe": 1},
                                         return_reasons=True)
        self.assertEqual(reasons, [])

    def test_skips_non_finite_values(self):
        items, truncated = numeric_fields([math.nan, math.inf, -2.5])
        self.assertFalse(truncated)
        self.assertEqual(items, [{"path": "$[2]", "value": -2.5}])

    def test_depth_limit_is_explicit(self):
        values = {"outer": {"inner": 3}}
        # A depth cutoff hid an entire nested subtree in the old scanner.
        # The returned fields may be empty but the scan is NOT complete.
        self.assertEqual(numeric_fields(values, max_depth=0), ([], True))
        self.assertEqual(numeric_fields(values, max_depth=1), ([], True))
        self.assertEqual(numeric_fields(values, max_depth=2),
                         ([{"path": "$.outer.inner", "value": 3}], False))
        self.assertEqual(numeric_fields({"empty": {}}, max_depth=1),
                         ([], False))
        self.assertEqual(numeric_fields([], max_depth=0), ([], False))
        self.assertEqual(numeric_fields([{"a": 1}], max_depth=0),
                         ([], True))

    def test_depth_limit_does_not_drop_visible_siblings(self):
        values = {"inside": {"nested": {"v": 4}}, "outside": 7}
        fields, truncated = numeric_fields(values, max_depth=1)
        self.assertTrue(truncated)
        self.assertEqual(fields, [{"path": "$.outside", "value": 7}])

    def test_rejects_invalid_limits(self):
        with self.assertRaises(ValueError):
            numeric_fields({"a": 1}, max_fields=0)
        with self.assertRaises(ValueError):
            numeric_fields({"a": 1}, max_depth=-1)


class BundleFormatTests(unittest.TestCase):
    def test_git_lfs_pointer_is_not_misreported_as_emptied_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.bundle"
            path.write_bytes(
                b"version https://git-lfs.github.com/spec/v1\n"
                b"oid sha256:" + b"0" * 64 + b"\nsize 1234\n"
            )
            with self.assertRaisesRegex(ValueError, "Git LFS pointer"):
                scan_bundle(path)

    def test_path_id_selection_preserves_full_bundle_uncertainty(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.bundle"
            path.write_bytes(b"UnityFS" + bytes(48))
            expected = hashlib.sha256(path.read_bytes()).hexdigest()

            class Reader:
                def __init__(self, path_id, values):
                    self.type = types.SimpleNamespace(name="MonoBehaviour")
                    self.path_id = path_id
                    self.values = values

                def parse_as_dict(self):
                    return self.values

            fake = types.ModuleType("UnityPy")
            fake.__version__ = "fake"
            fake.load = lambda _: types.SimpleNamespace(objects=[
                Reader(100, {"m_Name": "alpha", "amount": 10}),
                Reader(200, {"m_Name": "beta", "nested": {"amount": 20}}),
            ])
            helpers = types.ModuleType("UnityPy.helpers")
            helpers.TypeTreeHelper = types.SimpleNamespace(
                read_typetree_boost=True)
            with patch.dict(sys.modules, {
                "UnityPy": fake, "UnityPy.helpers": helpers,
            }):
                report = scan_bundle(path, path_ids={"200"},
                                     expected_sha256=expected,
                                     max_fields=10, max_depth=1)
                self.assertEqual(report["monobehaviours_total"], 2)
                self.assertEqual(report["monobehaviours_attempted"], 1)
                self.assertEqual(report["selected_path_ids"], ["200"])
                self.assertEqual(report["missing_path_ids"], [])
                self.assertEqual(report["records"][0]["path_id"], "200")
                self.assertEqual(report["records"][0][
                    "numeric_truncation_reasons"], ["depth_limit"])
                self.assertFalse(report["selected_numeric_extraction_complete"])
                self.assertFalse(report["complete_numeric_extraction"])

                full = scan_bundle(path, expected_sha256=expected,
                                   max_depth=2)
                self.assertTrue(full["complete_numeric_extraction"])

                missing = scan_bundle(path, path_ids={"300"},
                                      expected_sha256=expected)
                self.assertEqual(missing["missing_path_ids"], ["300"])
                self.assertFalse(missing["selected_numeric_extraction_complete"])

                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    scan_bundle(path, expected_sha256="0" * 64)
                with self.assertRaisesRegex(ValueError, "must not be empty"):
                    scan_bundle(path, path_ids=set())

    def test_invalid_bundle_is_rejected_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.bundle"
            path.write_bytes(b"not UnityFS bytes")
            with self.assertRaisesRegex(ValueError, "Not a UnityFS bundle"):
                scan_bundle(path)


if __name__ == "__main__":
    unittest.main()
