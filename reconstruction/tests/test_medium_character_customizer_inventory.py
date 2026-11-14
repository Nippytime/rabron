"""W1-X original medium body, prison, head and customizer UnityFS sources."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "data/medium_character_customizer_source_targets.json").read_text(
        encoding="utf-8"
    )
)
EVIDENCE = "GitHub Actions W1-X medium-character-customizer source inventory artifact"
MIN_SIZE = 1048576
MAX_SIZE = 20971519
EXACT_NAMES = {
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_body_31_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_body_31_type_2_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_body_33_type_2_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_body_5_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_prisonbody_2.asset.bundle",
    "character-separeted_assets_scriptableobjects_skincenter_customizercontent_characterfbodiesviewdescription_f_body_42_type_1_paint_1.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterbodiesviewdescription_prisonbody_2.asset.bundle",
    "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_characterheadsviewdescription_head_8.asset.bundle",
    "character-separeted_assets_scriptableobjects_skincenter_customizercontent_characterheadsviewdescription_head_5.asset.bundle",
    "character-separeted_assets_customizercontent_characterkeychainsviewdescription.bundle",
}


class MediumCharacterCustomizerInventoryTests(unittest.TestCase):
    def setUp(self):
        self.targets = MANIFEST["bundles"]
        self.pins = MANIFEST["expected_git_blobs"]
        self.sources = {
            p: {"bundle": p, "git_blob_sha": x["git_blob_sha"],
                "git_blob_size": x["size_bytes"]}
            for p, x in self.pins.items()
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
                         EXACT_NAMES)
        self.assertEqual(sum(x["size_bytes"] for x in self.pins.values()),
                         74126821)
        self.assertTrue(all(
            p.startswith("StreamingAssets/aa/StandaloneWindows64/")
            and MIN_SIZE <= x["size_bytes"] <= MAX_SIZE
            and len(x["git_blob_sha"]) == 40
            for p, x in self.pins.items()
        ))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 10)
        self.assertEqual([len(batch["sources"]) for batch in plan["batches"]],
                         [2, 2, 2, 2, 2])
        self.assertEqual(
            {x["bundle"] for i in range(5) for x in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_nonempty_complete_recheck_and_drift_fail_closed(self):
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
        self.assertEqual([len(batch["sources"]) for batch in plan["batches"]],
                         [2, 2, 2, 2, 2])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources, {**self.ledger, "scans": scans[:-1]},
                      **self.args)
        drift = copy.deepcopy(scans)
        drift[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources, {**self.ledger, "scans": drift},
                      **self.args)
        no_evidence = copy.deepcopy(scans)
        no_evidence[0]["scan_evidence"] = "unverified"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources, {**self.ledger, "scans": no_evidence},
                      **self.args)

    def test_missing_duplicate_lfs_pointer_and_size_fail_closed(self):
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
                          "StreamingAssets/aa/StandaloneWindows64/missing.bundle"
                      ]})


if __name__ == "__main__":
    unittest.main()
