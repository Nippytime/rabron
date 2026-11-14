"""W1-P exact original medium civilian-body provenance and recheck gates."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/medium_civilian_remaining_source_targets.json").read_text())
EVIDENCE = "GitHub Actions W1-P medium-civilian-remaining source inventory artifact"
MIN_SIZE = 1048576
MAX_SIZE = 20971519


class MediumCivilianRemainingInventoryTests(unittest.TestCase):
    def setUp(self):
        self.targets = MANIFEST["bundles"]
        self.expected = MANIFEST["expected_git_blobs"]
        self.sources = {
            path: {"bundle": path, "git_blob_sha": data["git_blob_sha"],
                   "git_blob_size": data["size_bytes"]}
            for path, data in self.expected.items()
        }
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.args = {"targets": self.targets, "expected_tracked": 8,
                     "batch_size": 2, "min_size": MIN_SIZE,
                     "max_size": MAX_SIZE, "scan_evidence": EVIDENCE}

    def test_exact_eight_pinned_sources_and_four_two_source_batches(self):
        self.assertEqual(MANIFEST["schema_version"], 1)
        self.assertEqual(len(self.targets), 8)
        self.assertEqual(set(self.targets), set(self.expected))
        self.assertEqual(sum(x["size_bytes"] for x in self.expected.values()), 48780159)
        self.assertTrue(all(
            path.startswith("StreamingAssets/aa/StandaloneWindows64/")
            and "characterbodiesviewdescription_body_" in path
            and path.endswith(".asset.bundle")
            and MIN_SIZE <= x["size_bytes"] <= MAX_SIZE
            and len(x["git_blob_sha"]) == 40
            for path, x in self.expected.items()
        ))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 8)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2])
        self.assertEqual(
            {e["bundle"] for i in range(4) for e in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_full_recheck_required_and_partial_or_drift_fails(self):
        scans = [{
            "bundle": path, "git_blob_sha": source["git_blob_sha"],
            "size_bytes": source["git_blob_size"], "sha256": "b" * 64,
            "scan_evidence": EVIDENCE, "monobehaviours_total": 0,
            "monobehaviours_parsed": 0, "numeric_field_cap_records": 0,
        } for path, source in self.sources.items()]
        plan = make_plan(self.sources, {**self.ledger, "scans": scans},
                         **self.args)
        self.assertEqual(plan["mode"], "recheck")
        self.assertEqual(plan["recheck_documented_sources"], 8)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": scans[:-1]},
                      **self.args)
        mutated = copy.deepcopy(scans)
        mutated[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": mutated},
                      **self.args)
        mutated = copy.deepcopy(scans)
        mutated[0]["scan_evidence"] = "unverified"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources, {**self.ledger, "scans": mutated},
                      **self.args)

    def test_duplicate_missing_lfs_and_wrong_size_fail_closed(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            entries = copy.deepcopy(self.sources)
            entries[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                    ValueError, "size or LFS"):
                make_plan(entries, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + self.targets[:1]})
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger,
                      **{**self.args, "targets": self.targets + [
                          "StreamingAssets/aa/StandaloneWindows64/missing.bundle"]})


if __name__ == "__main__":
    unittest.main()
