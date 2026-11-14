"""W1-N original police body source selection and full recheck tests."""
import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.small_bundle_inventory import make_plan, selected_batch

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "GitHub Actions W1-N medium-police-body source inventory artifact"
MIN_SIZE = 1024 * 1024
MAX_SIZE = 20 * 1024 * 1024 - 1


class MediumPoliceBodyInventoryTests(unittest.TestCase):
    def setUp(self):
        manifest = json.loads(
            (ROOT / "data/medium_police_body_source_targets.json").read_text(
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
        self.args = {"targets": self.targets, "expected_tracked": 7,
                     "batch_size": 2, "min_size": MIN_SIZE, "max_size": MAX_SIZE,
                     "scan_evidence": EVIDENCE}

    def test_exact_seven_original_police_bodies_in_four_bounded_batches(self):
        self.assertEqual(len(self.targets), 7)
        self.assertEqual(len(set(self.targets)), 7)
        self.assertEqual(
            {p.rsplit("/", 1)[-1] for p in self.targets},
            {
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_1_manpolicebody.asset.bundle",
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_1_womanpolicebody.asset.bundle",
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_2_manpolicebody.asset.bundle",
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_2_womanpolicebody.asset.bundle",
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_3_manpolicebody.asset.bundle",
                      "character-separeted_assets_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_3_womanpolicebody.asset.bundle",
                      "character-separeted_assets_scriptableobjects_skincenter_customizercontent_charactercopbodiesviewdescription_0_womanpolicebody.asset.bundle"
            },
        )
        self.assertTrue(all(p.startswith(
            "StreamingAssets/aa/StandaloneWindows64/"
        ) and p.endswith(".bundle") for p in self.targets))
        self.assertTrue(all("policebody" in p for p in self.targets))
        self.assertTrue(all("policemask" not in p for p in self.targets))
        self.assertFalse(any("0_manpolicebody" in p for p in self.targets))
        plan = make_plan(self.sources, self.ledger, **self.args)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["eligible_small_sources"], 7)
        self.assertEqual([len(b["sources"]) for b in plan["batches"]],
                         [2, 2, 2, 1])
        self.assertEqual(
            {x["bundle"] for i in range(4)
             for x in selected_batch(plan, i)},
            set(self.targets),
        )

    def test_complete_original_source_recheck_never_returns_no_jobs(self):
        originals = [{
            "bundle": p, "sha256": "b" * 64,
            "git_blob_sha": "a" * 40, "size_bytes": 8 * 1024 * 1024,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": EVIDENCE,
        } for p in self.targets]
        recheck = make_plan(
            self.sources, {**self.ledger, "scans": originals}, **self.args
        )
        self.assertEqual(recheck["mode"], "recheck")
        self.assertEqual(recheck["recheck_documented_sources"], 7)
        self.assertEqual([len(b["sources"]) for b in recheck["batches"]],
                         [2, 2, 2, 1])
        with self.assertRaisesRegex(ValueError, "partly documented"):
            make_plan(self.sources,
                      {**self.ledger, "scans": originals[:6]}, **self.args)
        drift = copy.deepcopy(originals)
        drift[0]["git_blob_sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "Git source changed"):
            make_plan(self.sources,
                      {**self.ledger, "scans": drift}, **self.args)
        wrong = copy.deepcopy(originals)
        wrong[0]["scan_evidence"] = "unverified"
        with self.assertRaisesRegex(ValueError, "lacks complete matching"):
            make_plan(self.sources,
                      {**self.ledger, "scans": wrong}, **self.args)

    def test_missing_duplicate_pointer_and_out_of_range_inputs_fail(self):
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
                    "StreamingAssets/aa/StandaloneWindows64/nonexistent.bundle"
                ],
            })


if __name__ == "__main__":
    unittest.main()
