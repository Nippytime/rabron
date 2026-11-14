"""Regression tests for bounded UnityFS inventory and evidence gate."""

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.validate_source_inventory import validate


class SourceInventoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / "sample.bundle"
        self.source.write_bytes(b"UnityFS" + bytes(range(32)))
        self.size = self.source.stat().st_size
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.records = [{
            "path_id": "100", "status": "parsed",
            "numeric_truncation_reasons": [], "fields_truncated": False,
            "numeric_fields": [{"path": "$.power", "value": 42}],
        }]
        self.manifest = {
            "source": str(self.source), "sha256": self.sha,
            "size_bytes": self.size, "objects_by_type": {
                "AssetBundle": 1, "MonoBehaviour": 1,
            },
            "numeric_field_limit": 2048, "numeric_depth_limit": 32,
            "monobehaviours_total": 1,
            "monobehaviours_attempted": 1,
            "monobehaviours_parsed": 1,
            "limit_reached": False, "selected_path_ids": None,
            "complete_numeric_extraction": True,
            "records": self.records,
        }
        self.summary = {
            "source": str(self.source), "source_sha256": self.sha,
            "object_counts": self.manifest["objects_by_type"],
            "monobehaviours_total": 1, "monobehaviours_attempted": 1,
            "monobehaviours_parsed": 1,
            "records_with_truncated_numeric_fields": 0,
            "complete_numeric_extraction": True,
        }

    def check(self, manifest=None, summary=None, **kwargs):
        args = {"source": str(self.source), "expected_size": self.size,
                "max_fields": 2048, "max_depth": 32}
        args.update(kwargs)
        return validate(manifest if manifest is not None else self.manifest,
                        summary if summary is not None else self.summary,
                        **args)

    def test_valid_original_source_and_full_numeric_records(self):
        result = self.check()
        self.assertEqual(result["sha256"], self.sha)
        self.assertEqual(result["parsed"], 1)
        self.assertTrue(result["bounded_mono_numeric_complete"])

    def test_zero_monobehaviour_media_source_is_valid_but_not_game_logic(self):
        manifest = copy.deepcopy(self.manifest)
        summary = copy.deepcopy(self.summary)
        manifest["records"] = []
        manifest["objects_by_type"] = {"AssetBundle": 1, "Sprite": 2}
        manifest["monobehaviours_total"] = 0
        manifest["monobehaviours_attempted"] = 0
        manifest["monobehaviours_parsed"] = 0
        summary["object_counts"] = manifest["objects_by_type"]
        summary["monobehaviours_total"] = 0
        summary["monobehaviours_attempted"] = 0
        summary["monobehaviours_parsed"] = 0
        result = self.check(manifest, summary)
        self.assertEqual(result["parsed"], 0)
        self.assertEqual(result["object_types"]["Sprite"], 2)

    def test_partial_numeric_fields_are_accepted_only_when_flagged(self):
        manifest = copy.deepcopy(self.manifest)
        summary = copy.deepcopy(self.summary)
        manifest["records"][0]["numeric_truncation_reasons"] = ["field_limit"]
        manifest["records"][0]["fields_truncated"] = True
        manifest["complete_numeric_extraction"] = False
        summary["records_with_truncated_numeric_fields"] = 1
        summary["complete_numeric_extraction"] = False
        result = self.check(manifest, summary)
        self.assertEqual(result["truncated"], 1)
        self.assertFalse(result["bounded_mono_numeric_complete"])
        manifest["complete_numeric_extraction"] = True
        with self.assertRaisesRegex(ValueError, "completeness"):
            self.check(manifest, summary)

    def test_unparsed_typetree_is_not_silently_completed(self):
        manifest = copy.deepcopy(self.manifest)
        summary = copy.deepcopy(self.summary)
        manifest["records"][0]["status"] = "unparsed"
        manifest["monobehaviours_parsed"] = 0
        manifest["complete_numeric_extraction"] = False
        summary["monobehaviours_parsed"] = 0
        summary["complete_numeric_extraction"] = False
        result = self.check(manifest, summary)
        self.assertEqual(result["unparsed"], 1)
        self.assertFalse(result["bounded_mono_numeric_complete"])

    def test_distinct_serialized_files_can_share_path_id_without_losing_identity(self):
        manifest = copy.deepcopy(self.manifest)
        summary = copy.deepcopy(self.summary)
        first = manifest["records"][0]
        first["serialized_file"] = "level0"
        second = copy.deepcopy(first)
        second["serialized_file"] = "sharedassets0.assets"
        manifest["records"] = [first, second]
        manifest["monobehaviours_total"] = 2
        manifest["monobehaviours_attempted"] = 2
        manifest["monobehaviours_parsed"] = 2
        manifest["objects_by_type"]["MonoBehaviour"] = 2
        summary["object_counts"] = manifest["objects_by_type"]
        summary["monobehaviours_total"] = 2
        summary["monobehaviours_attempted"] = 2
        summary["monobehaviours_parsed"] = 2
        result = self.check(manifest, summary)
        self.assertEqual(result["parsed"], 2)
        self.assertTrue(result["bounded_mono_numeric_complete"])
        # Duplicate within one serialized file remains a validation failure.
        manifest["records"][1]["serialized_file"] = "level0"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.check(manifest, summary)
        # Cannot pass if a repeated path ID loses its serialized-file scope.
        del manifest["records"][1]["serialized_file"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.check(manifest, summary)

    def test_missing_or_mutated_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "byte size"):
            self.check(expected_size=self.size + 1)
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.check(manifest={**self.manifest, "sha256": "0" * 64})
        self.source.write_bytes(b"NotAUnityBinary")
        with self.assertRaisesRegex(ValueError, "byte size"):
            self.check()

    def test_duplicate_missing_or_unexpected_records_are_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["records"].append(copy.deepcopy(manifest["records"][0]))
        manifest["monobehaviours_total"] = 2
        manifest["monobehaviours_attempted"] = 2
        manifest["monobehaviours_parsed"] = 2
        manifest["objects_by_type"]["MonoBehaviour"] = 2
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summary = copy.deepcopy(self.summary)
            summary.update({
                "monobehaviours_total": 2, "monobehaviours_attempted": 2,
                "monobehaviours_parsed": 2,
                "object_counts": manifest["objects_by_type"],
            })
            self.check(manifest, summary)

        manifest = copy.deepcopy(self.manifest)
        manifest["limit_reached"] = True
        with self.assertRaisesRegex(ValueError, "unrestricted"):
            self.check(manifest=manifest)

        manifest = copy.deepcopy(self.manifest)
        manifest["monobehaviours_total"] = 3
        with self.assertRaisesRegex(ValueError, "counts"):
            self.check(manifest=manifest)


if __name__ == "__main__":
    unittest.main()
