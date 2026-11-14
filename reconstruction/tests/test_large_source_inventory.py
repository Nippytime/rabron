"""Bounded W1-I large original UnityFS target, recheck, and source scope tests."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import (
    MAX_SOURCE_SIZE, make_plan, selected_batch,
)

ROOT = Path(__file__).resolve().parents[1]
LABEL = "GitHub Actions W1-I large-source inventory artifact"
MIN_SIZE = 20 * 1024 * 1024
MAX_SIZE = 64 * 1024 * 1024 - 1


class LargeSourceInventoryTests(unittest.TestCase):
    def setUp(self):
        manifest = json.loads(
            (ROOT / "data/large_source_targets.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema_version"], 1)
        self.targets = manifest["bundles"]
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.sources = {
            p: {"bundle": p, "git_blob_sha": "a" * 40,
                "git_blob_size": 32 * 1024 * 1024}
            for p in self.targets
        }
        self.args = {"targets": self.targets, "expected_tracked": 3,
                     "batch_size": 1, "min_size": MIN_SIZE, "max_size": MAX_SIZE,
                     "scan_evidence": LABEL}

    def test_exact_source_list_bounded_individual_batches(self):
        self.assertEqual(MAX_SOURCE_SIZE, MAX_SIZE)
        self.assertEqual(len(set(self.targets)), 3)
        self.assertEqual(len(self.targets), 3)
        self.assertTrue(all(p.startswith("StreamingAssets/aa/StandaloneWindows64/")
                            and p.endswith(".bundle") for p in self.targets))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 3)
        self.assertEqual([len(x["sources"]) for x in plan["batches"]], [1, 1, 1])
        self.assertEqual({selected_batch(plan, i)[0]["bundle"] for i in range(3)},
                         set(self.targets))

    def test_source_recheck_requires_three_verified_original_blobs(self):
        evidence = [{
            "bundle": p, "sha256": "b" * 64, "git_blob_sha": "a" * 40,
            "size_bytes": 32 * 1024 * 1024,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": LABEL,
        } for p in self.targets]
        recheck = make_plan(self.sources, {**self.ledger, "scans": evidence},
                            **self.args)
        self.assertEqual(recheck["mode"], "recheck")
        self.assertEqual(recheck["recheck_documented_sources"], 3)
        self.assertEqual([len(x["sources"]) for x in recheck["batches"]],
                         [1, 1, 1])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": evidence[:1]},
                      **self.args)
        changed = copy.deepcopy(evidence)
        changed[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": changed},
                      **self.args)

    def test_missing_oversized_pointer_and_duplicate_sources_fail(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            changed = copy.deepcopy(self.sources)
            changed[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                    ValueError, "size or LFS"):
                make_plan(changed, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + [self.targets[0]]})
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + [
                        "StreamingAssets/aa/StandaloneWindows64/not-found.bundle"]})


if __name__ == "__main__":
    unittest.main()
