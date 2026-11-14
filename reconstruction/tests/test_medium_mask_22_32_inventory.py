"""W1-S exact original medium character-mask variants 22–29 and 31–32."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/medium_mask_22_32_source_targets.json").read_text())
EVIDENCE = "GitHub Actions W1-S medium-mask-22-32 source inventory artifact"
MIN_SIZE = 1048576
MAX_SIZE = 20971519
IDS = (22, 23, 24, 25, 26, 27, 28, 29, 31, 32)


class MediumMask2232InventoryTests(unittest.TestCase):
    def setUp(self):
        self.targets = MANIFEST["bundles"]
        self.pins = MANIFEST["expected_git_blobs"]
        self.sources = {
            path: {"bundle": path, "git_blob_sha": x["git_blob_sha"],
                   "git_blob_size": x["size_bytes"]}
            for path, x in self.pins.items()
        }
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.args = {"targets": self.targets, "expected_tracked": 10,
                     "batch_size": 2, "min_size": MIN_SIZE,
                     "max_size": MAX_SIZE, "scan_evidence": EVIDENCE}

    def test_exact_pins_and_five_bounded_batches(self):
        self.assertEqual(MANIFEST["schema_version"], 1)
        self.assertEqual(len(self.targets), 10)
        self.assertEqual(set(self.targets), set(self.pins))
        self.assertEqual({p.rsplit("/", 1)[-1] for p in self.targets},
                         {f"character-mask-{i}_assets_all.bundle" for i in IDS})
        self.assertEqual(sum(x["size_bytes"] for x in self.pins.values()), 30695396)
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/")
            and MIN_SIZE <= x["size_bytes"] <= MAX_SIZE
            and len(x["git_blob_sha"]) == 40
            for p, x in self.pins.items()
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

    def test_complete_recheck_and_source_drift_fail_closed(self):
        scans = [{
            "bundle": p, "git_blob_sha": x["git_blob_sha"],
            "size_bytes": x["git_blob_size"], "sha256": "b" * 64,
            "scan_evidence": EVIDENCE, "monobehaviours_total": 0,
            "monobehaviours_parsed": 0, "numeric_field_cap_records": 0,
        } for p, x in self.sources.items()]
        plan = make_plan(self.sources, {**self.ledger, "scans": scans},
                         **self.args)
        self.assertEqual(plan["mode"], "recheck")
        self.assertEqual(plan["recheck_documented_sources"], 10)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": scans[:-1]},
                      **self.args)
        wrong = copy.deepcopy(scans)
        wrong[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": wrong},
                      **self.args)
        no_evidence = copy.deepcopy(scans)
        no_evidence[0]["scan_evidence"] = "unverified"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources, {**self.ledger, "scans": no_evidence},
                      **self.args)

    def test_missing_duplicate_lfs_and_out_of_bounds_fail(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            changed = copy.deepcopy(self.sources)
            changed[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                    ValueError, "size or LFS"):
                make_plan(changed, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + self.targets[:1]})
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + [
                          "StreamingAssets/aa/StandaloneWindows64/missing.bundle",
                      ]})


if __name__ == "__main__":
    unittest.main()
