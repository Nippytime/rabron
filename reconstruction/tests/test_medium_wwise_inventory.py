"""W1-M exact medium original Wwise source manifest and nonempty recheck."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
LABEL = "GitHub Actions W1-M medium-wwise source inventory artifact"
MIN_SIZE = 1024 * 1024
MAX_SIZE = 20 * 1024 * 1024 - 1


class MediumWwiseInventoryTests(unittest.TestCase):
    def setUp(self):
        manifest = json.loads(
            (ROOT / "data/medium_wwise_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["schema_version"], 1)
        self.targets = manifest["bundles"]
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.sources = {
            p: {"bundle": p, "git_blob_sha": "a" * 40,
                "git_blob_size": 2 * 1024 * 1024}
            for p in self.targets
        }
        self.args = {"targets": self.targets, "expected_tracked": 3,
                     "batch_size": 1, "min_size": MIN_SIZE, "max_size": MAX_SIZE,
                     "scan_evidence": LABEL}

    def test_exact_wwise_scope_and_deterministic_single_source_batches(self):
        self.assertEqual(len(self.targets), 3)
        self.assertEqual(len(set(self.targets)), 3)
        self.assertEqual(
            {p.rsplit("/", 1)[-1] for p in self.targets},
            {
                "wwisedata_windows_battle_localized_assets_all.bundle",
                "wwisedata_windows_gamestart_assets_all.bundle",
                "wwisedata_windows_initbank_assets_all.bundle",
            },
        )
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/")
            for p in self.targets
        ))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 3)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]], [1, 1, 1])
        self.assertEqual(
            {selected_batch(plan, i)[0]["bundle"] for i in range(3)},
            set(self.targets),
        )

    def test_recheck_refuses_missing_or_drifted_source_identity(self):
        entries = [{
            "bundle": p, "sha256": "b" * 64, "git_blob_sha": "a" * 40,
            "size_bytes": 2 * 1024 * 1024,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": LABEL,
        } for p in self.targets]
        plan = make_plan(
            self.sources, {**self.ledger, "scans": entries}, **self.args
        )
        self.assertEqual(plan["mode"], "recheck")
        self.assertEqual(plan["recheck_documented_sources"], 3)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]], [1, 1, 1])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": entries[:2]},
                      **self.args)
        drift = copy.deepcopy(entries)
        drift[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": drift},
                      **self.args)
        wrong = copy.deepcopy(entries)
        wrong[0]["scan_evidence"] = "other scan evidence"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources, {**self.ledger, "scans": wrong},
                      **self.args)

    def test_pointer_missing_duplicate_and_non_medium_sources_fail(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            wrong = copy.deepcopy(self.sources)
            wrong[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                ValueError, "size or LFS"
            ):
                make_plan(wrong, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(
                self.sources, self.ledger,
                **{**self.args, "targets": self.targets + [self.targets[0]]}
            )
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger, **{
                **self.args,
                "targets": self.targets + [
                    "StreamingAssets/aa/StandaloneWindows64/not-found.bundle"
                ],
            })


if __name__ == "__main__":
    unittest.main()
