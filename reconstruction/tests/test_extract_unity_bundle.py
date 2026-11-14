"""Tests scalar normalization independently of UnityPy or any protected assets."""

import math
import tempfile
import unittest
from pathlib import Path

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

    def test_skips_non_finite_values(self):
        items, truncated = numeric_fields([math.nan, math.inf, -2.5])
        self.assertFalse(truncated)
        self.assertEqual(items, [{"path": "$[2]", "value": -2.5}])

    def test_depth_limit_is_explicit(self):
        values = {"outer": {"inner": 3}}
        self.assertEqual(numeric_fields(values, max_depth=0), ([], False))
        self.assertEqual(numeric_fields(values, max_depth=2),
                         ([{"path": "$.outer.inner", "value": 3}], False))

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

    def test_invalid_bundle_is_rejected_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.bundle"
            path.write_bytes(b"not UnityFS bytes")
            with self.assertRaisesRegex(ValueError, "Not a UnityFS bundle"):
                scan_bundle(path)


if __name__ == "__main__":
    unittest.main()
