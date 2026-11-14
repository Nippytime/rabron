"""W1-O original civilian body source plan and exact recheck tests."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "GitHub Actions W1-O medium-player-body source inventory artifact"
MIN_SIZE = 1024 * 1024
MAX_SIZE = 20 * 1024 * 1024 - 1
EXPECTED_NAMES = [
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_12_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_2.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_16_type_1_paint_3.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_2.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_3.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_18_type_1_paint_4.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_28_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_body_30_type_1_paint_1.asset.bundle"
]


class MediumPlayerBodyInventoryTests(unittest.TestCase):
    def setUp(self):
        manifest = json.loads(
            (ROOT / "data/medium_player_body_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["schema_version"], 1)
        self.targets = manifest["bundles"]
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.sources = {
            p: {"bundle": p, "git_blob_sha": "a" * 40,
                "git_blob_size": 8 * 1024 * 1024}
            for p in self.targets
        }
        self.args = {"targets": self.targets, "expected_tracked": 10,
                     "batch_size": 2, "min_size": MIN_SIZE, "max_size": MAX_SIZE,
                     "scan_evidence": EVIDENCE}

    def test_exact_ten_civilian_originals_in_five_bounded_batches(self):
        self.assertEqual(len(self.targets), 10)
        self.assertEqual(len(set(self.targets)), 10)
        self.assertEqual({p.rsplit("/", 1)[-1] for p in self.targets},
                         set(EXPECTED_NAMES))
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/")
            and "characterbodiesviewdescription_body_" in p
            and p.endswith(".bundle") for p in self.targets
        ))
        self.assertFalse(any("copbodies" in p for p in self.targets))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 10)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2, 2])
        self.assertEqual(
            {e["bundle"] for i in range(5)
             for e in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_all_ten_documented_originals_trigger_full_recheck(self):
        evidence = [{
            "bundle": p, "sha256": "b" * 64, "git_blob_sha": "a" * 40,
            "size_bytes": 8 * 1024 * 1024,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": EVIDENCE,
        } for p in self.targets]
        plan = make_plan(self.sources,
                         {**self.ledger, "scans": evidence}, **self.args)
        self.assertEqual(plan["mode"], "recheck")
        self.assertEqual(plan["recheck_documented_sources"], 10)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources,
                      {**self.ledger, "scans": evidence[:9]}, **self.args)
        drift = copy.deepcopy(evidence)
        drift[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources,
                      {**self.ledger, "scans": drift}, **self.args)
        wrong = copy.deepcopy(evidence)
        wrong[0]["scan_evidence"] = "unverified"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources,
                      {**self.ledger, "scans": wrong}, **self.args)

    def test_missing_duplicate_lfs_pointer_and_out_of_range_fail(self):
        for size in (133, MIN_SIZE - 1, MAX_SIZE + 1):
            sources = copy.deepcopy(self.sources)
            sources[self.targets[0]]["git_blob_size"] = size
            with self.subTest(size=size), self.assertRaisesRegex(
                ValueError, "size or LFS"
            ):
                make_plan(sources, self.ledger, **self.args)
        with self.assertRaisesRegex(ValueError, "unique"):
            make_plan(self.sources, self.ledger, **{
                **self.args, "targets": self.targets + self.targets[:1],
            })
        with self.assertRaisesRegex(ValueError, "missing"):
            make_plan(self.sources, self.ledger, **{
                **self.args, "targets": self.targets + [
                    "StreamingAssets/aa/StandaloneWindows64/missing.bundle"
                ],
            })


if __name__ == "__main__":
    unittest.main()
