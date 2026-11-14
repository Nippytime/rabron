"""Truthful extraction queue and historic scan evidence tests, no game binaries."""

import copy
import json
import unittest
from pathlib import Path

from reconstruction.tools.plan_bundle_scans import (
    BUNDLE_PREFIX, plan_scans, priority, validate_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = json.loads((ROOT / "data/extraction_coverage.json").read_text(
    encoding="utf-8"
))


def bundle(name):
    return BUNDLE_PREFIX + name + ".bundle"


class ExtractionCoverageTests(unittest.TestCase):
    def test_documented_scans_account_for_verified_passes_and_older_caps(self):
        self.assertEqual(LEDGER["schema_version"], 1)
        self.assertEqual(len(LEDGER["scans"]), 15)
        self.assertEqual(sum(entry["monobehaviours_parsed"]
                             for entry in LEDGER["scans"]), 9107)
        self.assertEqual(sum(entry["numeric_field_cap_records"]
                             for entry in LEDGER["scans"]), 56)
        self.assertEqual(len(LEDGER["known_lfs_not_yet_scanned"]), 2)
        self.assertIn("GameAssembly.dll", LEDGER["blocking_missing_sources"][0])

        paths = [e["bundle"] for e in LEDGER["scans"]]
        paths.extend(e["bundle"] for e in LEDGER["known_lfs_not_yet_scanned"])
        known, pending = validate_ledger(LEDGER, paths)
        self.assertEqual(len(known), 15)
        self.assertEqual(len(pending), 2)

    def test_six_actual_gameplay_scans_have_source_ids_and_declared_limits(self):
        recent = [entry for entry in LEDGER["scans"]
                  if entry.get("status") == "documented_bounded_scan_no_reported_field_limits"]
        self.assertEqual(len(recent), 6)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in recent), 1320)
        self.assertTrue(all(e["numeric_field_cap_records"] == 0 for e in recent))
        self.assertTrue(all(e["run_url"].endswith("/43584959275")
                            for e in recent))
        self.assertTrue(all(e["candidate_field_counts"]["economy"] == 0
                            for e in recent))
        self.assertTrue(all("Unity object kinds" in e["scope"]
                            for e in recent))
        self.assertTrue(all(e["scan_evidence"] ==
                            "reconstruction/docs/gameplay-bundle-batch-1.md"
                            for e in recent))

    def test_queue_does_not_call_any_historical_scan_complete(self):
        report = plan_scans(
            [bundle("random-decoration"), bundle("npc_assets_all"),
             bundle("location-city-data_assets_all"),
             bundle("scriptableobjects_assets_all")],
            {
                "schema_version": 1,
                "scans": [
                    dict(LEDGER["scans"][0]),
                    next(e for e in LEDGER["scans"] if
                         e["bundle"].endswith("/location-city-data_assets_all.bundle")),
                ],
                "known_lfs_not_yet_scanned": [
                    next(e for e in LEDGER["known_lfs_not_yet_scanned"] if
                         e["bundle"].endswith("/npc_assets_all.bundle")),
                ],
            },
        )
        self.assertEqual(report["tracked_bundles"], 4)
        self.assertEqual(report["historically_documented_scan_bundles"], 2)
        self.assertEqual(report["documented_monobehaviours_parsed"], 3956)
        self.assertEqual(report["historic_field_capped_records"], 27)
        statuses = {x["bundle"]: x["status"] for x in report["backlog"]}
        self.assertEqual(statuses[bundle("npc_assets_all")], "needs_lfs_bytes")
        self.assertEqual(statuses[bundle("scriptableobjects_assets_all")],
                         "partial_field_cap")
        self.assertEqual(statuses[bundle("random-decoration")],
                         "not_documented_scanned")
        self.assertNotIn("complete", statuses.values())
        self.assertEqual(report, plan_scans(
            list(reversed([x["bundle"] for x in report["backlog"]])),
            {
                "schema_version": 1,
                "scans": [
                    dict(LEDGER["scans"][0]),
                    next(e for e in LEDGER["scans"] if
                         e["bundle"].endswith("/location-city-data_assets_all.bundle")),
                ],
                "known_lfs_not_yet_scanned": [
                    next(e for e in LEDGER["known_lfs_not_yet_scanned"] if
                         e["bundle"].endswith("/npc_assets_all.bundle")),
                ],
            },
        ))

    def test_rejects_ledger_corruption_and_untracked_claims(self):
        path = bundle("test")
        good = {
            "schema_version": 1,
            "scans": [{
                "bundle": path,
                "sha256": "a" * 64,
                "monobehaviours_total": 3,
                "monobehaviours_parsed": 2,
                "numeric_field_cap_records": 1,
                "scan_evidence": "sample",
            }],
        }
        self.assertEqual(len(validate_ledger(good, [path])[0]), 1)

        invalid = copy.deepcopy(good)
        invalid["scans"][0]["sha256"] = "not-a-sha256"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate_ledger(invalid, [path])

        invalid = copy.deepcopy(good)
        invalid["scans"][0]["numeric_field_cap_records"] = 3
        with self.assertRaisesRegex(ValueError, "scan counts"):
            validate_ledger(invalid, [path])

        invalid = copy.deepcopy(good)
        invalid["scans"].append(copy.deepcopy(invalid["scans"][0]))
        with self.assertRaisesRegex(ValueError, "Unknown/duplicate"):
            validate_ledger(invalid, [path])

        with self.assertRaisesRegex(ValueError, "Unknown/duplicate"):
            validate_ledger(good, [bundle("different")])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_ledger({"schema_version": 1, "scans": []}, [path, path])

        invalid = copy.deepcopy(good)
        invalid["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "version"):
            validate_ledger(invalid, [path])

    def test_research_priorities_are_only_heuristics_not_game_formulas(self):
        self.assertEqual(priority(bundle("npc_assets_all")), "high")
        self.assertEqual(priority(bundle("location-city-data_assets_all")), "high")
        self.assertEqual(priority(bundle("character-mask-1_assets_all")), "medium")
        self.assertEqual(priority(bundle("decor-1_assets_all")), "low")


if __name__ == "__main__":
    unittest.main()
