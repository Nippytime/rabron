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
        self.assertEqual(len(LEDGER["scans"]), 158)
        self.assertEqual(sum(entry["monobehaviours_parsed"]
                             for entry in LEDGER["scans"]), 78783)
        self.assertEqual(sum(entry["numeric_field_cap_records"]
                             for entry in LEDGER["scans"]), 64)
        self.assertEqual(len(LEDGER["known_lfs_not_yet_scanned"]), 0)
        self.assertIn("GameAssembly.dll", LEDGER["blocking_missing_sources"][0])

        paths = [e["bundle"] for e in LEDGER["scans"]]
        paths.extend(e["bundle"] for e in LEDGER["known_lfs_not_yet_scanned"])
        known, pending = validate_ledger(LEDGER, paths)
        self.assertEqual(len(known), 158)
        self.assertEqual(len(pending), 0)

    def test_actual_npc_and_tutorial_source_inventory_is_scoped(self):
        npc = next(e for e in LEDGER["scans"]
                   if e["bundle"].endswith("/npc_assets_all.bundle"))
        tutorial = next(e for e in LEDGER["scans"]
                        if e["bundle"].endswith("/tutorial_assets_all.bundle"))
        self.assertEqual(npc["sha256"], npc["lfs_oid_sha256"])
        self.assertEqual(npc["size_bytes"], 98896651)
        self.assertEqual(npc["monobehaviours_total"], 374)
        self.assertEqual(npc["monobehaviours_parsed"], 374)
        self.assertEqual(npc["numeric_field_cap_records"], 0)
        self.assertEqual(npc["objects_by_type"]["AnimationClip"], 88)
        self.assertEqual(npc["objects_by_type"]["GameObject"], 7386)
        self.assertEqual(npc["candidate_field_counts"]["combat"], 36)
        self.assertEqual(npc["candidate_field_counts"]["timing_and_world"], 568)

        self.assertEqual(tutorial["sha256"], tutorial["lfs_oid_sha256"])
        self.assertEqual(tutorial["size_bytes"], 84166120)
        self.assertEqual(tutorial["monobehaviours_total"], 0)
        self.assertEqual(tutorial["monobehaviours_parsed"], 0)
        self.assertEqual(tutorial["numeric_field_cap_records"], 0)
        self.assertEqual(tutorial["objects_by_type"]["Sprite"], 113)
        self.assertEqual(tutorial["objects_by_type"]["Texture2D"], 113)
        self.assertEqual(tutorial["status"], "documented_no_monobehaviours_media_only")
        self.assertTrue(all(e["run_url"].endswith("/43587524219")
                            for e in (npc, tutorial)))

        paths = [e["bundle"] for e in LEDGER["scans"]]
        plan = plan_scans(paths, LEDGER)
        statuses = {e["bundle"]: e["status"] for e in plan["backlog"]}
        self.assertEqual(statuses[tutorial["bundle"]],
                         "inspected_no_monobehaviours")
        self.assertEqual(plan["historically_documented_scan_bundles"], 158)

    def test_six_actual_gameplay_scans_have_source_ids_and_declared_limits(self):
        recent = [entry for entry in LEDGER["scans"]
                  if entry.get("scan_evidence") == "reconstruction/docs/gameplay-bundle-batch-1.md"]
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

    def test_eight_real_weapon_vehicle_prison_scans_are_source_anchored(self):
        recent = [
            e for e in LEDGER["scans"]
            if e.get("scan_evidence") ==
            "reconstruction/docs/weapon-vehicle-prison-batch.md"
        ]
        self.assertEqual(len(recent), 8)
        expected = {
            "weapons_assets_assets_content_equipment_weapons__sharedsources.bundle": 71,
            "weapons_assets_assets_content_equipment_weapons__modules.bundle": 128,
            "weapon-lmg_assets_all.bundle": 19,
            "weapon-lbr44_assets_all.bundle": 80,
            "vehicle-car-longhorn_guard_assets_all.bundle": 50,
            "vehicle-car-longhorn_van_assets_all.bundle": 456,
            "vehicle-car-longhorn_outrider_assets_all.bundle": 50,
            "location-prison-standalone_scenes_all.bundle": 248,
        }
        self.assertEqual(
            {e["bundle"].split("/")[-1]: e["monobehaviours_parsed"]
             for e in recent}, expected,
        )
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in recent), 1102)
        self.assertTrue(all(e["run_url"].endswith("/43588642907")
                            for e in recent))
        self.assertTrue(all(e["monobehaviours_parsed"] ==
                            e["monobehaviours_total"] for e in recent))
        self.assertTrue(all(e["unparsed_records"] == 0 and
                            e["numeric_field_cap_records"] == 0 and
                            e["bounded_numeric_scan_complete"] is True
                            for e in recent))
        self.assertTrue(all(e["numeric_field_limit"] == 2048 and
                            e["numeric_depth_limit"] == 32 and
                            e["size_bytes"] > 0 for e in recent))
        self.assertTrue(all(len(e["sha256"]) == 64 for e in recent))
        self.assertEqual(
            sum(e["candidate_field_counts"]["combat"] for e in recent), 264
        )
        self.assertEqual(
            sum(e["candidate_field_counts"]["timing_and_world"]
                for e in recent), 828,
        )
        prison = next(e for e in recent if e["bundle"].endswith(
            "/location-prison-standalone_scenes_all.bundle"))
        self.assertEqual(prison["objects_by_type"]["GameObject"], 3622)
        self.assertEqual(prison["objects_by_type"]["MeshCollider"], 257)

    def test_measured_w1f_small_sources_keep_verifiable_provenance(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43590995615"
        new = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(new), 117)
        self.assertEqual(sum(e["monobehaviours_total"] for e in new), 4272)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in new), 4272)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in new), 7)
        self.assertEqual(sum(e["unparsed_records"] for e in new), 0)
        self.assertEqual(sum(e["monobehaviours_total"] == 0 for e in new), 73)
        self.assertTrue(all(e["bounded_numeric_scan_complete"] is
                            (e["numeric_field_cap_records"] == 0)
                            for e in new))
        self.assertTrue(all(1024 <= e["size_bytes"] <= 999999 and
                            len(e["sha256"]) == 64 and
                            len(e["git_blob_sha"]) == 40 and
                            e["numeric_field_limit"] == 2048 and
                            e["numeric_depth_limit"] == 32
                            for e in new))
        self.assertEqual(
            sum(e["candidate_field_counts"]["economy"] for e in new), 23
        )
        self.assertEqual(
            sum(e["candidate_field_counts"]["combat"] for e in new), 1
        )

    def test_w1g_ten_real_medium_sources_are_source_anchored(self):
        source_run = "https://github.com/Nippytime/rabron/actions/runs/43592228322"
        targets = json.loads((ROOT / "data/medium_source_targets.json").read_text(
            encoding="utf-8"
        ))["bundles"]
        measured = [e for e in LEDGER["scans"] if e.get("run_url") == source_run]
        self.assertEqual(len(measured), 10)
        self.assertEqual({e["bundle"] for e in measured}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in measured), 72243123)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in measured), 2733)
        self.assertEqual(sum(e["monobehaviours_total"] for e in measured), 2733)
        self.assertEqual(sum(e["unparsed_records"] for e in measured), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in measured), 0)
        self.assertEqual(sum(e["candidate_field_counts"]["combat"]
                             for e in measured), 440)
        self.assertEqual(sum(e["candidate_field_counts"]["timing_and_world"]
                             for e in measured), 1144)
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: e["monobehaviours_parsed"]
             for e in measured},
            {
                "vehicle-car-buletti_soltempra_assets_all.bundle": 328,
                "vehicle-car-fukurou_spark_assets_all.bundle": 232,
                "vehicle-car-fukurou_tensa_assets_all.bundle": 364,
                "vehicle-car-longhorn_titan_assets_all.bundle": 456,
                "vehicle-car-longhorn_wild_assets_all.bundle": 390,
                "vehicle-car-royal_e_assets_all.bundle": 434,
                "vehicle-car-royal_j_assets_all.bundle": 360,
                "weapon-dp9_assets_all.bundle": 60,
                "weapon-ordr12_assets_all.bundle": 56,
                "weapon-starh_assets_all.bundle": 53,
            },
        )
        self.assertTrue(all(
            1048576 <= e["size_bytes"] < 20971520 and
            e["bounded_numeric_scan_complete"] is True and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["git_blob_sha"]) == 40 and len(e["sha256"]) == 64 and
            e["scan_evidence"] ==
            "GitHub Actions W1-G medium-source inventory artifact"
            for e in measured
        ))

    def test_w1h_world_scans_have_real_source_ids_and_explicit_partiality(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43627300176"
        manifest = json.loads(
            (ROOT / "data/world_source_targets.json").read_text(encoding="utf-8")
        )
        sources = [entry for entry in LEDGER["scans"]
                   if entry.get("run_url") == run]
        self.assertEqual(len(sources), 6)
        self.assertEqual({e["bundle"] for e in sources}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in sources), 54306812)
        self.assertEqual(sum(e["monobehaviours_total"] for e in sources), 61195)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in sources), 61195)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in sources), 1)
        self.assertEqual(sum(e["unparsed_records"] for e in sources), 0)
        self.assertEqual(sum(e["monobehaviours_total"] == 0
                             for e in sources), 1)
        expected = {
            "environment-interactive_assets_all.bundle": 655,
            "environment_assets_all.bundle": 63,
            "shared-environment-city_assets_all.bundle": 0,
            "space-battle_assets_all.bundle": 52685,
            "space-mainmenu_scenes_all.bundle": 187,
            "space-realm_assets_all.bundle": 7605,
        }
        self.assertEqual(
            {e["bundle"].split("/")[-1]: e["monobehaviours_parsed"]
             for e in sources}, expected,
        )
        self.assertEqual(
            {category: sum(e["candidate_field_counts"][category]
                           for e in sources)
             for category in ("combat", "economy", "progression",
                              "timing_and_world")},
            {"combat": 16, "economy": 36, "progression": 61,
             "timing_and_world": 19453},
        )
        self.assertTrue(all(
            1048576 <= e["size_bytes"] < 20971520 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            e["monobehaviours_total"] == e["monobehaviours_parsed"] and
            len(e["sha256"]) == 64 and len(e["git_blob_sha"]) == 40 and
            e["scan_evidence"] ==
            "GitHub Actions W1-H world-environment source inventory artifact"
            for e in sources
        ))
        realm = next(e for e in sources if e["bundle"].endswith(
            "/space-realm_assets_all.bundle"))
        self.assertEqual(realm["numeric_field_cap_records"], 1)
        self.assertIs(realm["bounded_numeric_scan_complete"], False)
        city = next(e for e in sources if e["bundle"].endswith(
            "/shared-environment-city_assets_all.bundle"))
        self.assertEqual(city["objects_by_type"].get("MonoBehaviour", 0), 0)
        self.assertIs(city["bounded_numeric_scan_complete"], True)

    def test_verified_selected_path_ids_and_remaining_caps(self):
        recovery = json.loads((ROOT / "data/targeted_numeric_recovery.json").read_text(
            encoding="utf-8"
        ))
        self.assertEqual(recovery["schema_version"], 1)
        self.assertEqual(len(recovery["bundles"]), 7)
        self.assertEqual(recovery["record_counts"], {
            "historical": 56, "resolved": 30,
            "unresolved": 26, "adaptive_retried": 36,
        })
        total = [0, 0, 0]
        for bundle in recovery["bundles"]:
            path = bundle["bundle"]
            evidence = next(e for e in LEDGER["scans"]
                            if e["bundle"].endswith("/" + path))
            resolved = bundle["resolved_path_ids"]
            unresolved = bundle["unresolved_path_ids"]
            self.assertEqual(bundle["source_sha256"], evidence["sha256"])
            self.assertEqual(len(resolved) + len(unresolved),
                             evidence["numeric_field_cap_records"])
            self.assertEqual(len(set(resolved + unresolved)),
                             len(resolved) + len(unresolved))
            self.assertTrue(all(str(int(value)) == value
                                for value in resolved + unresolved))
            targeted = evidence["targeted_rescan"]
            self.assertEqual(targeted["resolved_count"], len(resolved))
            self.assertEqual(targeted["unresolved_count"], len(unresolved))
            self.assertEqual(targeted["complete_historical_field_caps"],
                             len(unresolved) == 0)
            total[0] += len(resolved)
            total[1] += len(unresolved)
            total[2] += bundle["adaptive_retry_count"]
        self.assertEqual(total, [30, 26, 36])

        paths = [entry["bundle"] for entry in LEDGER["scans"]]
        paths.extend(entry["bundle"] for entry in
                     LEDGER["known_lfs_not_yet_scanned"])
        planned = plan_scans(paths, LEDGER)
        self.assertEqual(planned["historic_field_capped_records"], 64)
        self.assertEqual(planned["remaining_historic_field_capped_records"], 34)
        statuses = {entry["bundle"]: entry["status"] for entry
                    in planned["backlog"]}
        self.assertEqual(
            statuses[BUNDLE_PREFIX + "inbuild_assets_all.bundle"],
            "historic_caps_resolved_scope_partial",
        )
        self.assertEqual(planned["statuses"]["partial_field_cap"], 14)
        self.assertEqual(planned["statuses"][
            "historic_caps_resolved_scope_partial"], 1)

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
                    {key: e[key] for e in LEDGER["scans"]
                     if e["bundle"].endswith("/npc_assets_all.bundle")
                     for key in ("bundle", "lfs_oid_sha256", "size_bytes")},
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
                    {key: e[key] for e in LEDGER["scans"]
                     if e["bundle"].endswith("/npc_assets_all.bundle")
                     for key in ("bundle", "lfs_oid_sha256", "size_bytes")},
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
