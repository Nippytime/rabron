"""W1-H exact world-source scope and fail-closed recheck requirements."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.plan_bundle_scans import validate_ledger
from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
LABEL = "GitHub Actions W1-H world-environment source inventory artifact"
MIN = 1024 * 1024
MAX = 20 * 1024 * 1024 - 1


class WorldSourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(
            (ROOT / "data/world_source_targets.json").read_text(encoding="utf-8")
        )
        self.targets = self.manifest["bundles"]
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.entries = {
            p: {"bundle": p, "git_blob_sha": "a" * 40,
                "git_blob_size": 2 * 1024 * 1024}
            for p in self.targets
        }
        self.options = {
            "targets": self.targets, "expected_tracked": 6,
            "batch_size": 2, "min_size": MIN, "max_size": MAX,
            "scan_evidence": LABEL,
        }

    def test_manifest_has_six_unambiguous_original_source_paths(self):
        self.assertEqual(self.manifest["schema_version"], 1)
        self.assertEqual(len(self.targets), 6)
        self.assertEqual(len(set(self.targets)), 6)
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/") and
            p.endswith(".bundle") for p in self.targets
        ))

    def test_new_selection_is_six_with_three_bounded_batches(self):
        plan = make_plan(self.entries, self.ledger, **self.options)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 6)
        self.assertEqual([len(g["sources"]) for g in plan["batches"]], [2, 2, 2])
        self.assertEqual(
            {x["bundle"] for i in range(3) for x in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_recheck_requires_all_six_original_verified_entries(self):
        evidence = [{
            "bundle": p, "sha256": "b" * 64,
            "git_blob_sha": "a" * 40, "size_bytes": 2 * 1024 * 1024,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": LABEL,
        } for p in self.targets]
        full = {**self.ledger, "scans": evidence}
        validate_ledger(full, self.targets)
        plan = make_plan(self.entries, full, **self.options)
        self.assertEqual(plan["mode"], "recheck")
        self.assertEqual(plan["recheck_documented_sources"], 6)
        self.assertEqual([len(x["sources"]) for x in plan["batches"]], [2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.entries, {**full, "scans": evidence[:-1]},
                      **self.options)
        wrong_label = copy.deepcopy(full)
        wrong_label["scans"][0]["scan_evidence"] = "unrelated"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.entries, wrong_label, **self.options)
        altered = copy.deepcopy(full)
        altered["scans"][0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.entries, altered, **self.options)

    def test_rejects_missing_duplicate_and_pointer_sources(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.entries, self.ledger,
                      **{**self.options, "targets": [
                          *self.targets, "StreamingAssets/aa/StandaloneWindows64/no-such.bundle"
                      ]})
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.entries, self.ledger,
                      **{**self.options, "targets": [
                          *self.targets, self.targets[0]
                      ]})
        pointer = copy.deepcopy(self.entries)
        pointer[self.targets[0]]["git_blob_size"] = 133
        with self.assertRaisesRegex(ValueError, "size or LFS"):
            make_plan(pointer, self.ledger, **self.options)


if __name__ == "__main__":
    unittest.main()
