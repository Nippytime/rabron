"""W1-Q exact original medium character-mask source identity and recheck tests."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/medium_mask_source_targets.json").read_text())
EVIDENCE = "GitHub Actions W1-Q medium-mask source inventory artifact"
MIN_SIZE = 1048576
MAX_SIZE = 20971519
SOURCE_IDS = (1, 2, 3, 4, 5, 6, 7, 9, 10, 11)


class MediumMaskInventoryTests(unittest.TestCase):
    def setUp(self):
        self.targets = MANIFEST["bundles"]
        self.expected = MANIFEST["expected_git_blobs"]
        self.sources = {
            path: {"bundle": path, "git_blob_sha": info["git_blob_sha"],
                   "git_blob_size": info["size_bytes"]}
            for path, info in self.expected.items()
        }
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.args = {"targets": self.targets, "expected_tracked": 10,
                     "batch_size": 2, "min_size": MIN_SIZE,
                     "max_size": MAX_SIZE, "scan_evidence": EVIDENCE}

    def test_exact_pinned_ten_originals_and_five_two_source_batches(self):
        self.assertEqual(MANIFEST["schema_version"], 1)
        self.assertEqual(len(self.targets), 10)
        self.assertEqual(set(self.targets), set(self.expected))
        self.assertEqual(
            {path.rsplit("/", 1)[-1] for path in self.targets},
            {f"character-mask-{i}_assets_all.bundle" for i in SOURCE_IDS},
        )
        self.assertEqual(sum(i["size_bytes"] for i in self.expected.values()),
                         46515488)
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/")
            and MIN_SIZE <= i["size_bytes"] <= MAX_SIZE
            and len(i["git_blob_sha"]) == 40
            for p, i in self.expected.items()
        ))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 10)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2, 2])
        self.assertEqual(
            {e["bundle"] for i in range(5) for e in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_full_source_recheck_and_partial_or_drift_fail(self):
        scans = [{
            "bundle": p, "git_blob_sha": x["git_blob_sha"],
            "size_bytes": x["git_blob_size"], "sha256": "b" * 64,
            "scan_evidence": EVIDENCE, "monobehaviours_total": 0,
            "monobehaviours_parsed": 0, "numeric_field_cap_records": 0,
        } for p, x in self.sources.items()]
        recheck = make_plan(self.sources, {**self.ledger, "scans": scans},
                            **self.args)
        self.assertEqual(recheck["mode"], "recheck")
        self.assertEqual(recheck["recheck_documented_sources"], 10)
        self.assertEqual([len(b["sources"]) for b in recheck["batches"]],
                         [2, 2, 2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": scans[:-1]},
                      **self.args)
        mismatched = copy.deepcopy(scans)
        mismatched[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": mismatched},
                      **self.args)
        unverified = copy.deepcopy(scans)
        unverified[0]["scan_evidence"] = "unsupported"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources, {**self.ledger, "scans": unverified},
                      **self.args)

    def test_missing_duplicate_lfs_and_wrong_size_are_rejected(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            broken = copy.deepcopy(self.sources)
            broken[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                    ValueError, "size or LFS"):
                make_plan(broken, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.sources, self.ledger, **{
                **self.args, "targets": self.targets + self.targets[:1],
            })
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger, **{
                **self.args, "targets": self.targets + [
                    "StreamingAssets/aa/StandaloneWindows64/missing.bundle",
                ],
            })


if __name__ == "__main__":
    unittest.main()
