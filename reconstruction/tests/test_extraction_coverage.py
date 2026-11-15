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
        self.assertEqual(len(LEDGER["scans"]), 328)
        self.assertEqual(sum(entry["monobehaviours_parsed"]
                             for entry in LEDGER["scans"]), 128390)
        self.assertEqual(sum(entry["numeric_field_cap_records"]
                             for entry in LEDGER["scans"]), 76)
        # The new Wwise source adds one explicitly unparsed oversized
        # MonoBehaviour. It must never be counted as a parsed numeric field.
        self.assertEqual(sum(entry.get("unparsed_records", 0)
                             for entry in LEDGER["scans"]), 1)
        self.assertEqual(len(LEDGER["known_lfs_not_yet_scanned"]), 0)
        self.assertIn("GameAssembly.dll", LEDGER["blocking_missing_sources"][0])

        paths = [e["bundle"] for e in LEDGER["scans"]]
        paths.extend(e["bundle"] for e in LEDGER["known_lfs_not_yet_scanned"])
        known, pending = validate_ledger(LEDGER, paths)
        self.assertEqual(len(known), 328)
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
        self.assertEqual(plan["historically_documented_scan_bundles"], 328)

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

    def test_w1i_large_source_provenance_and_unresolved_numeric_cap(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43628460048"
        targets = json.loads(
            (ROOT / "data/large_source_targets.json").read_text(encoding="utf-8")
        )["bundles"]
        sources = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(sources), 3)
        self.assertEqual({e["bundle"] for e in sources}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in sources), 87418232)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in sources), 1151)
        self.assertEqual(sum(e["monobehaviours_total"] for e in sources), 1151)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in sources), 1)
        self.assertEqual(sum(e["unparsed_records"] for e in sources), 0)
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: e["monobehaviours_total"]
             for e in sources},
            {
                "location-settlement-standalone_scenes_settlementadditive_standalone.bundle": 495,
                "space-global_scenes_all.bundle": 603,
                "weapon-apscalar_assets_all.bundle": 53,
            },
        )
        self.assertEqual({
            key: sum(e["candidate_field_counts"][key] for e in sources)
            for key in ("combat", "economy", "progression",
                        "timing_and_world")},
            {"combat": 135, "economy": 217, "progression": 90,
             "timing_and_world": 864},
        )
        self.assertTrue(all(
            20971520 <= e["size_bytes"] <= 67108863 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and len(e["git_blob_sha"]) == 40 and
            e["scan_evidence"] ==
            "GitHub Actions W1-I large-source inventory artifact"
            for e in sources
        ))
        settlement = next(e for e in sources if e["bundle"].endswith(
            "/location-settlement-standalone_scenes_settlementadditive_standalone.bundle"))
        self.assertIs(settlement["bounded_numeric_scan_complete"], False)
        self.assertEqual(settlement["numeric_field_cap_records"], 1)
        self.assertTrue(all(e["bounded_numeric_scan_complete"] is True
                            for e in sources if e is not settlement))

    def test_w1j_verified_large_weapon_inventory_retains_source_provenance(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43629339564"
        manifest = json.loads(
            (ROOT / "data/large_weapon_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 3)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 135500927)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 246)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 246)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["candidate_field_counts"]["combat"]
                             for e in scans), 594)
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: e["monobehaviours_parsed"]
             for e in scans},
            {"weapon-cb45_assets_all.bundle": 56,
             "weapon-drm14_assets_all.bundle": 78,
             "weapon-harris500_assets_all.bundle": 112},
        )
        self.assertTrue(all(
            20971520 <= e["size_bytes"] < 67108864 and
            e["monobehaviours_total"] == e["monobehaviours_parsed"] and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and
            len(e["git_blob_sha"]) == 40 and
            e["bounded_numeric_scan_complete"] is True and
            e["scan_evidence"] ==
            "GitHub Actions W1-J large-weapon source inventory artifact"
            for e in scans
        ))

    def test_w1k_verified_settlement_and_weapon_source_evidence(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43630060068"
        targets = json.loads(
            (ROOT / "data/large_settlement_weapon_source_targets.json").read_text(
                encoding="utf-8"
            )
        )["bundles"]
        actual = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(actual), 3)
        self.assertEqual({e["bundle"] for e in actual}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in actual), 134099202)
        self.assertEqual(sum(e["monobehaviours_total"] for e in actual), 1643)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in actual), 1643)
        self.assertEqual(sum(e["unparsed_records"] for e in actual), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in actual), 2)
        self.assertEqual({
            k: sum(e["candidate_field_counts"][k] for e in actual)
            for k in ("combat", "economy", "progression", "timing_and_world")
        }, {"combat": 330, "economy": 214, "progression": 0,
            "timing_and_world": 540})
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: e["monobehaviours_parsed"]
             for e in actual},
            {"location-settlement2-standalone_scenes_all.bundle": 1506,
             "weapon-jp7_assets_all.bundle": 53,
             "weapon-srreaper_assets_all.bundle": 84},
        )
        self.assertTrue(all(
            20971520 <= e["size_bytes"] < 67108864 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and
            len(e["git_blob_sha"]) == 40 and
            e["monobehaviours_total"] == e["monobehaviours_parsed"] and
            e["scan_evidence"] ==
            "GitHub Actions W1-K large-settlement-weapon inventory artifact"
            for e in actual
        ))
        settlement = next(e for e in actual
                          if e["bundle"].endswith(
                              "/location-settlement2-standalone_scenes_all.bundle"))
        self.assertEqual(settlement["numeric_field_cap_records"], 2)
        self.assertIs(settlement["bounded_numeric_scan_complete"], False)
        self.assertTrue(all(e["numeric_field_cap_records"] == 0 and
                            e["bounded_numeric_scan_complete"] is True
                            for e in actual if e is not settlement))

    def test_w1l_final_large_media_source_zeros_and_wwise_partiality(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43630843839"
        targets = json.loads(
            (ROOT / "data/final_large_media_source_targets.json").read_text(
                encoding="utf-8"
            )
        )["bundles"]
        media = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(media), 3)
        self.assertEqual({e["bundle"] for e in media}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in media), 78857251)
        self.assertEqual(sum(e["monobehaviours_total"] for e in media), 1)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in media), 1)
        self.assertEqual(sum(e["unparsed_records"] for e in media), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in media), 1)
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: e["monobehaviours_parsed"]
             for e in media},
            {
                "ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_all__fullspriteatlas_4k.spriteatlasv2.bundle": 0,
                "ui-spriteatlas_assets_bigimages.bundle": 0,
                "wwisedata_windows_global_assets_all.bundle": 1,
            },
        )
        self.assertTrue(all(
            20971520 <= e["size_bytes"] < 67108864 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and
            len(e["git_blob_sha"]) == 40 and
            e["scan_evidence"] ==
            "GitHub Actions W1-L large-media source inventory artifact" and
            all(e["candidate_field_counts"][k] == 0 for k in (
                "combat", "economy", "progression", "timing_and_world"
            ))
            for e in media
        ))
        atlases = [e for e in media if "ui-spriteatlas" in e["bundle"]]
        self.assertEqual(len(atlases), 2)
        self.assertTrue(all(
            e["monobehaviours_total"] == 0 and
            e["bounded_numeric_scan_complete"] is True and
            e["objects_by_type"].get("Texture2D", 0) > 0
            for e in atlases
        ))
        wwise = next(e for e in media if e["bundle"].endswith(
            "/wwisedata_windows_global_assets_all.bundle"
        ))
        self.assertEqual(wwise["objects_by_type"]["MonoBehaviour"], 1)
        self.assertIs(wwise["bounded_numeric_scan_complete"], False)
        self.assertEqual(wwise["numeric_field_cap_records"], 1)

    def test_w1m_medium_wwise_verified_partial_numeric_sources(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43631572017"
        names = json.loads(
            (ROOT / "data/medium_wwise_source_targets.json").read_text(
                encoding="utf-8"
            )
        )["bundles"]
        actual = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(actual), 3)
        self.assertEqual({e["bundle"] for e in actual}, set(names))
        self.assertEqual(sum(e["size_bytes"] for e in actual), 27353739)
        self.assertEqual(sum(e["monobehaviours_total"] for e in actual), 5)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in actual), 5)
        self.assertEqual(sum(e["unparsed_records"] for e in actual), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in actual), 4)
        self.assertEqual(
            {e["bundle"].rsplit("/", 1)[-1]: (
                e["monobehaviours_parsed"], e["numeric_field_cap_records"]
            ) for e in actual},
            {
                "wwisedata_windows_battle_localized_assets_all.bundle": (2, 2),
                "wwisedata_windows_gamestart_assets_all.bundle": (2, 1),
                "wwisedata_windows_initbank_assets_all.bundle": (1, 1),
            },
        )
        self.assertTrue(all(
            1048576 <= e["size_bytes"] < 20971520 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and len(e["git_blob_sha"]) == 40 and
            e["bounded_numeric_scan_complete"] is False and
            e["scan_evidence"] ==
            "GitHub Actions W1-M medium-wwise source inventory artifact" and
            all(e["candidate_field_counts"][k] == 0 for k in (
                "combat", "economy", "progression", "timing_and_world"
            ))
            for e in actual
        ))

    def test_w1n_police_body_original_source_counts_and_scope(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43632465318"
        targets = json.loads(
            (ROOT / "data/medium_police_body_source_targets.json").read_text(
                encoding="utf-8"
            )
        )["bundles"]
        scanned = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scanned), 7)
        self.assertEqual({e["bundle"] for e in scanned}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in scanned), 62510955)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scanned), 7)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scanned), 7)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scanned), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scanned), 0)
        self.assertEqual(sum(e["objects_by_type"]["Mesh"] for e in scanned), 35)
        self.assertEqual(sum(e["objects_by_type"]["Texture2D"] for e in scanned), 21)
        self.assertTrue(all(
            1048576 <= e["size_bytes"] < 20971520 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and len(e["git_blob_sha"]) == 40 and
            e["bounded_numeric_scan_complete"] is True and
            e["scan_evidence"] ==
            "GitHub Actions W1-N medium-police-body source inventory artifact" and
            e["objects_by_type"] == {
                "AssetBundle": 1, "Material": 1, "Mesh": 5,
                "MonoBehaviour": 1, "Texture2D": 3,
            } and
            all(e["candidate_field_counts"][key] == 0
                for key in ("combat", "economy", "progression",
                            "timing_and_world"))
            for e in scanned
        ))

    def test_w1o_verified_civilian_body_original_source_inventory(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43633293481"
        targets = json.loads(
            (ROOT / "data/medium_player_body_source_targets.json").read_text(
                encoding="utf-8"
            )
        )["bundles"]
        actual = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(actual), 10)
        self.assertEqual({e["bundle"] for e in actual}, set(targets))
        self.assertEqual(sum(e["size_bytes"] for e in actual), 68275606)
        self.assertEqual(sum(e["monobehaviours_total"] for e in actual), 10)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in actual), 10)
        self.assertEqual(sum(e["unparsed_records"] for e in actual), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in actual), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in actual), 14)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in actual), 27)
        self.assertEqual(sum(e["objects_by_type"]["Material"]
                             for e in actual), 10)
        self.assertEqual(sum(e["objects_by_type"]["AssetBundle"]
                             for e in actual), 10)
        self.assertTrue(all(
            1048576 <= e["size_bytes"] < 20971520 and
            e["numeric_field_limit"] == 2048 and
            e["numeric_depth_limit"] == 32 and
            len(e["sha256"]) == 64 and len(e["git_blob_sha"]) == 40 and
            e["bounded_numeric_scan_complete"] is True and
            e["objects_by_type"]["MonoBehaviour"] == 1 and
            e["scan_evidence"] ==
            "GitHub Actions W1-O medium-player-body source inventory artifact" and
            all(e["candidate_field_counts"][k] == 0 for k in (
                "combat", "economy", "progression", "timing_and_world"))
            for e in actual
        ))

    def test_w1p_remaining_civilian_body_exact_measured_metadata(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43634223903"
        manifest = json.loads(
            (ROOT / "data/medium_civilian_remaining_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scanned = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scanned), 8)
        self.assertEqual({e["bundle"] for e in scanned}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scanned), 48780159)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scanned), 8)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scanned), 8)
        self.assertEqual(sum(e["unparsed_records"] for e in scanned), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scanned), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scanned), 20)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scanned), 18)
        self.assertTrue(all(
            e["size_bytes"] == manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["objects_by_type"]["MonoBehaviour"] == 1
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Material"] == 1
            and e["scan_evidence"] ==
            "GitHub Actions W1-P medium-civilian-remaining source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scanned
        ))

    def test_w1q_ten_real_medium_mask_source_inventories(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43635238378"
        manifest = json.loads(
            (ROOT / "data/medium_mask_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 46515488)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 4)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 4)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 8)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 97)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 9)
        self.assertTrue(all(
            e["size_bytes"] == manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["monobehaviours_parsed"] == e["monobehaviours_total"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Texture2D"] > 0
            and e["scan_evidence"] ==
            "GitHub Actions W1-Q medium-mask source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        mask10 = next(e for e in scans if
                      e["bundle"].endswith("/character-mask-10_assets_all.bundle"))
        self.assertEqual(mask10["objects_by_type"]["MonoBehaviour"], 4)
        self.assertEqual(mask10["objects_by_type"]["Mesh"], 8)
        self.assertEqual(mask10["objects_by_type"]["Material"], 6)
        self.assertTrue(all(e["objects_by_type"].get("MonoBehaviour", 0) == 0
                            for e in scans if e is not mask10))

    def test_w1r_ten_exact_mask_originals_have_genuine_zero_monos(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43636004658"
        manifest = json.loads(
            (ROOT / "data/medium_mask_12_21_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 19601935)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 0)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"]["Texture2D"] for e in scans), 35)
        self.assertTrue(all(
            e["size_bytes"] == manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["objects_by_type"].get("AssetBundle") == 1
            and e["objects_by_type"].get("Texture2D", 0) > 0
            and set(e["objects_by_type"]) == {"AssetBundle", "Texture2D"}
            and e["scan_evidence"] ==
            "GitHub Actions W1-R medium-mask-12-21 source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))

    def test_w1s_actual_mask_22_32_original_sources(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43636832117"
        manifest = json.loads(
            (ROOT / "data/medium_mask_22_32_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 30695396)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 4)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 4)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 10)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 58)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 9)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["monobehaviours_parsed"] == e["monobehaviours_total"]
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Texture2D"] > 0
            and e["scan_evidence"] ==
            "GitHub Actions W1-S medium-mask-22-32 source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        mask27 = next(e for e in scans if
                      e["bundle"].endswith("/character-mask-27_assets_all.bundle"))
        self.assertEqual(mask27["objects_by_type"]["MonoBehaviour"], 4)
        self.assertEqual(mask27["objects_by_type"]["Material"], 2)
        self.assertEqual(mask27["objects_by_type"]["Mesh"], 10)
        self.assertTrue(all(
            set(e["objects_by_type"]) == {"AssetBundle", "Texture2D"}
            for e in scans if e is not mask27
        ))

    def test_w1t_ten_original_medium_mask_33_44_inventories(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43637568828"
        manifest = json.loads(
            (ROOT / "data/medium_mask_33_44_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        expected_mono = {34: 2, 38: 4, 41: 2, 44: 6}
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 26313460)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 14)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 14)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 40)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 47)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 6)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["monobehaviours_parsed"] == e["monobehaviours_total"]
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Texture2D"] > 0
            and e["scan_evidence"] ==
            "GitHub Actions W1-T medium-mask-33-44 source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        for e in scans:
            mask_id = int(e["bundle"].rsplit("/", 1)[-1].split("-")[2].split("_")[0])
            expected = expected_mono.get(mask_id, 0)
            self.assertEqual(e["monobehaviours_total"], expected)
            self.assertEqual(e["objects_by_type"].get("MonoBehaviour", 0), expected)
            self.assertEqual(e["objects_by_type"].get("Mesh", 0),
                             10 if expected else 0)
            if not expected:
                self.assertEqual(set(e["objects_by_type"]),
                                 {"AssetBundle", "Texture2D"})

    def test_w1u_real_character_hair_beards_and_shared_sources(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43638364286"
        manifest = json.loads(
            (ROOT / "data/medium_character_cosmetics_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 25339958)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 111)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 111)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 282)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 13)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 2)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["monobehaviours_total"] == e["monobehaviours_parsed"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["scan_evidence"] ==
            "GitHub Actions W1-U medium-character-cosmetics source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        beard = next(e for e in scans if
                     e["bundle"].endswith("/character-beards_assets_all.bundle"))
        self.assertEqual(beard["monobehaviours_parsed"], 55)
        self.assertEqual(beard["objects_by_type"]["Mesh"], 184)
        hair = [e for e in scans if
                "/character-hair-" in e["bundle"] or
                "/character-fhair-" in e["bundle"]]
        self.assertEqual(len(hair), 7)
        self.assertTrue(all(e["monobehaviours_total"] == 8 for e in hair))
        for e in scans:
            if e is beard or e in hair:
                continue
            self.assertEqual(e["monobehaviours_total"], 0)
            self.assertEqual(set(e["objects_by_type"]),
                             {"AssetBundle", "Texture2D"})

    def test_w1v_real_ten_character_head_original_sources(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43639194242"
        manifest = json.loads(
            (ROOT / "data/medium_character_heads_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 50312798)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 10)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 10)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 143)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 49)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 27)
        self.assertTrue(all(
            e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["monobehaviours_total"] == 1
            and e["monobehaviours_parsed"] == 1
            and e["objects_by_type"]["MonoBehaviour"] == 1
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Mesh"] > 0
            and e["objects_by_type"]["Texture2D"] > 0
            and e["objects_by_type"]["Material"] > 0
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["scan_evidence"] ==
            "GitHub Actions W1-V medium-character-heads source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        female = [e for e in scans if
                  "characterfheadsviewdescription_" in e["bundle"]]
        male = [e for e in scans if
                "characterheadsviewdescription_" in e["bundle"]]
        self.assertEqual(len(female), 4)
        self.assertEqual(len(male), 6)

    def test_w1w_ten_original_female_body_source_inventories(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43640115769"
        manifest = json.loads(
            (ROOT / "data/medium_female_bodies_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 68246900)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 10)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 10)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 5)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 27)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 11)
        self.assertTrue(all(
            e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["monobehaviours_total"] == 1
            and e["monobehaviours_parsed"] == 1
            and e["objects_by_type"]["MonoBehaviour"] == 1
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["objects_by_type"]["Texture2D"] > 0
            and e["objects_by_type"]["Material"] > 0
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["scan_evidence"] ==
            "GitHub Actions W1-W medium-female-bodies source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        for e in scans:
            expected = (5 if "f_body_28_type_1_paint_1" in e["bundle"]
                        else 0)
            self.assertEqual(e["objects_by_type"].get("Mesh", 0), expected)

    def test_w1x_ten_real_character_customizer_original_sources(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43641144643"
        manifest = json.loads(
            (ROOT / "data/medium_character_customizer_source_targets.json").read_text(
                encoding="utf-8"
            )
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 74126821)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 24)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 24)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 107)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 74)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 29)
        self.assertTrue(all(
            e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and len(e["sha256"]) == 64
            and e["monobehaviours_total"] == e["monobehaviours_parsed"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["scan_evidence"] ==
            "GitHub Actions W1-X medium-character-customizer source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        keychain = next(
            e for e in scans if e["bundle"].endswith(
                "characterkeychainsviewdescription.bundle"
            )
        )
        self.assertEqual(keychain["monobehaviours_total"], 15)
        self.assertEqual(keychain["objects_by_type"]["Mesh"], 45)
        self.assertEqual(keychain["objects_by_type"]["Texture2D"], 42)
        self.assertEqual(keychain["objects_by_type"]["Material"], 16)
        self.assertEqual(len([
            e for e in scans if e["monobehaviours_total"] == 1
        ]), 9)
        for e in scans:
            if e is keychain:
                continue
            head = "characterheadsviewdescription_" in e["bundle"]
            unmeshed = "f_body_42_type_1_paint_1" in e["bundle"]
            self.assertEqual(
                e["objects_by_type"].get("Mesh", 0),
                16 if head else 0 if unmeshed else 5,
            )


    def test_w1y_original_ui_shaders_atlas_source_conservation(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43646079579"
        manifest = json.loads(
            (ROOT / "data/medium_original_ui_shaders_atlas_source_targets.json")
            .read_text(encoding="utf-8")
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 55587304)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 94)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 94)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Shader", 0)
                             for e in scans), 155)
        self.assertEqual(sum(e["objects_by_type"].get("Sprite", 0)
                             for e in scans), 137)
        self.assertEqual(sum(e["objects_by_type"].get("SpriteAtlas", 0)
                             for e in scans), 8)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 33)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 54)
        self.assertEqual(sum(e["candidate_field_counts"]["progression"]
                             for e in scans), 2)
        self.assertEqual(sum(e["candidate_field_counts"]["timing_and_world"]
                             for e in scans), 103)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 9)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["bounded_numeric_scan_complete"] is True
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["monobehaviours_total"] == e["monobehaviours_parsed"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["scan_evidence"] ==
            "GitHub Actions W1-Y medium-original-ui-shaders-atlas source inventory artifact"
            for e in scans
        ))
        tattoo = next(e for e in scans if
                      e["bundle"].endswith("/tattoo_scenes_tattoounlock.bundle"))
        self.assertEqual(tattoo["monobehaviours_total"], 94)
        self.assertEqual(tattoo["objects_by_type"]["GameObject"], 439)
        self.assertEqual(tattoo["objects_by_type"]["Transform"], 437)
        self.assertEqual(tattoo["objects_by_type"]["MeshRenderer"], 86)
        self.assertEqual(tattoo["objects_by_type"]["SkinnedMeshRenderer"], 32)
        shaders = next(e for e in scans if
                       e["bundle"].endswith("/shaders_assets_all.bundle"))
        self.assertEqual(shaders["objects_by_type"]["Shader"], 155)
        self.assertEqual(shaders["objects_by_type"]["ComputeShader"], 6)
        self.assertEqual(shaders["objects_by_type"]["Material"], 53)


    def test_w1z_tattoo_makeup_character_bag_originals_conserved(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43646936811"
        manifest = json.loads(
            (ROOT / "data/medium_original_tattoo_bags_source_targets.json")
            .read_text(encoding="utf-8")
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 35694961)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 5)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 5)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 9)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 41)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 7)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 5)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["bounded_numeric_scan_complete"] is True
            and e["monobehaviours_parsed"] == e["monobehaviours_total"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["scan_evidence"] ==
            "GitHub Actions W1-Z medium-original-tattoo-bags source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        bags = [e for e in scans if "characterbagsviewdescription_" in e["bundle"]]
        self.assertEqual(len(bags), 5)
        self.assertTrue(all(e["monobehaviours_total"] == 1 for e in bags))
        cop = next(e for e in bags if e["bundle"].endswith("copbag.asset.bundle"))
        self.assertEqual(cop["objects_by_type"]["Mesh"], 4)
        bag21 = next(e for e in bags if "bag_21_type_1_paint_1" in e["bundle"])
        self.assertEqual(bag21["objects_by_type"]["Mesh"], 5)


    def test_w1aa_original_cosmetic_bags_and_atlases_conserved(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43647615982"
        manifest = json.loads(
            (ROOT / "data/medium_original_cosmetic_atlases_source_targets.json")
            .read_text(encoding="utf-8")
        )
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 10)
        self.assertEqual({e["bundle"] for e in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 17121689)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 3)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 3)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("SpriteAtlas", 0)
                             for e in scans), 7)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0)
                             for e in scans), 23)
        self.assertEqual(sum(e["objects_by_type"].get("Material", 0)
                             for e in scans), 3)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in scans), 5)
        self.assertEqual(len([e for e in scans
                              if e["monobehaviours_total"] == 0]), 7)
        self.assertTrue(all(
            e["git_blob_sha"] ==
            manifest["expected_git_blobs"][e["bundle"]]["git_blob_sha"]
            and e["size_bytes"] ==
            manifest["expected_git_blobs"][e["bundle"]]["size_bytes"]
            and len(e["sha256"]) == 64
            and e["numeric_field_limit"] == 2048
            and e["numeric_depth_limit"] == 32
            and e["bounded_numeric_scan_complete"] is True
            and e["monobehaviours_parsed"] == e["monobehaviours_total"]
            and e["objects_by_type"]["AssetBundle"] == 1
            and e["scan_evidence"] ==
            "GitHub Actions W1-AA medium-original-cosmetic-atlases source inventory artifact"
            and all(v == 0 for v in e["candidate_field_counts"].values())
            for e in scans
        ))
        bags = [e for e in scans
                if "characterbagsviewdescription_" in e["bundle"]]
        self.assertEqual(len(bags), 3)
        self.assertTrue(all(e["monobehaviours_total"] == 1 for e in bags))
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0)
                             for e in bags), 5)
        atlas = [e for e in scans if "/ui-spriteatlas_" in e["bundle"]]
        self.assertEqual(len(atlas), 7)
        self.assertTrue(all(
            e["monobehaviours_total"] == 0
            and e["objects_by_type"]["SpriteAtlas"] == 1
            and e["objects_by_type"]["Texture2D"] == 2
            for e in atlas
        ))

    def test_w1ab_two_original_sprite_atlases_measured(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43648244327"
        manifest = json.loads((ROOT / "data/medium_original_final_sprite_atlases_source_targets.json").read_text(encoding="utf-8"))
        scans = [x for x in LEDGER["scans"] if x.get("run_url") == run]
        self.assertEqual(len(scans), 2)
        self.assertEqual({x["bundle"] for x in scans}, set(manifest["bundles"]))
        self.assertEqual(sum(x["size_bytes"] for x in scans), 3419828)
        for x in scans:
            pin = manifest["expected_git_blobs"][x["bundle"]]
            self.assertEqual(x["git_blob_sha"], pin["git_blob_sha"])
            self.assertEqual(x["size_bytes"], pin["size_bytes"])
            self.assertEqual(len(x["sha256"]), 64)
            self.assertEqual(x["objects_by_type"], {"AssetBundle": 1, "SpriteAtlas": 1, "Texture2D": 2})
            self.assertEqual(x["monobehaviours_total"], 0)
            self.assertEqual(x["monobehaviours_parsed"], 0)
            self.assertEqual(x["numeric_field_cap_records"], 0)
            self.assertEqual(x["unparsed_records"], 0)
            self.assertIs(x["bounded_numeric_scan_complete"], True)
            self.assertEqual(x["numeric_field_limit"], 2048)
            self.assertEqual(x["numeric_depth_limit"], 32)
            self.assertTrue(all(value == 0 for value in x["candidate_field_counts"].values()))
            self.assertEqual(x["scan_evidence"], "GitHub Actions W1-AB medium-original-final-sprite-atlases source inventory artifact")

    def test_w1ac_two_original_weapon_lfs_sources_conserved(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43649328171"
        manifest = json.loads((ROOT / "data/weapon_lfs_source_targets.json").read_text(encoding="utf-8"))
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 2)
        pins = {e["bundle"]: e for e in manifest["sources"]}
        self.assertEqual({e["bundle"] for e in scans}, set(pins))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 109658562)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 135)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 135)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0) for e in scans), 51)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0) for e in scans), 69)
        self.assertEqual(sum(e["candidate_field_counts"]["combat"] for e in scans), 330)
        for e in scans:
            source = pins[e["bundle"]]
            self.assertEqual(e["sha256"], source["lfs_oid_sha256"])
            self.assertEqual(e["lfs_oid_sha256"], source["lfs_oid_sha256"])
            self.assertEqual(e["git_blob_sha"], source["git_blob_sha"])
            self.assertEqual(e["size_bytes"], source["size_bytes"])
            self.assertEqual(e["numeric_field_limit"], 2048)
            self.assertEqual(e["numeric_depth_limit"], 32)
            self.assertIs(e["bounded_numeric_scan_complete"], True)
            self.assertEqual(e["scan_evidence"], "GitHub Actions W1-AC original weapon LFS source inventory artifact")

    def test_w1ad_original_equipment_realm_lfs_source_conservation(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43650079085"
        manifest = json.loads((ROOT / "data/equipment_realm_lfs_source_targets.json").read_text(encoding="utf-8"))
        scanned = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        pins = {e["bundle"]: e for e in manifest["sources"]}
        self.assertEqual(len(scanned), 2)
        self.assertEqual({e["bundle"] for e in scanned}, set(pins))
        self.assertEqual(sum(e["size_bytes"] for e in scanned), 128686756)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scanned), 109)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scanned), 109)
        self.assertEqual(sum(e["unparsed_records"] for e in scanned), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scanned), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0) for e in scanned), 171)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0) for e in scanned), 201)
        self.assertEqual(sum(e["objects_by_type"].get("ParticleSystem", 0) for e in scanned), 731)
        self.assertEqual(sum(e["candidate_field_counts"]["timing_and_world"] for e in scanned), 444)
        for e in scanned:
            pin = pins[e["bundle"]]
            self.assertEqual(e["git_blob_sha"], pin["git_blob_sha"])
            self.assertEqual(e["size_bytes"], pin["size_bytes"])
            self.assertEqual(e["lfs_oid_sha256"], pin["lfs_oid_sha256"])
            self.assertEqual(e["sha256"], pin["lfs_oid_sha256"])
            self.assertEqual(e["numeric_field_limit"], 2048)
            self.assertEqual(e["numeric_depth_limit"], 32)
            self.assertIs(e["bounded_numeric_scan_complete"], True)
            self.assertEqual(e["monobehaviours_parsed"], e["monobehaviours_total"])
            self.assertEqual(e["scan_evidence"], "GitHub Actions W1-AD original equipment-realm LFS source inventory artifact")

    def test_w1ae_rc556_tag12k_original_lfs_source_conservation(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43650766303"
        registry = json.loads((ROOT / "data/rc556_tag12k_lfs_source_targets.json").read_text(encoding="utf-8"))
        pinned = {e["bundle"]: e for e in registry["sources"]}
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 2)
        self.assertEqual({e["bundle"] for e in scans}, set(pinned))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 128115372)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 189)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 189)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0) for e in scans), 68)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0) for e in scans), 75)
        self.assertEqual(sum(e["candidate_field_counts"]["combat"] for e in scans), 396)
        self.assertEqual(sum(e["candidate_field_counts"]["timing_and_world"] for e in scans), 36)
        for e in scans:
            expected = pinned[e["bundle"]]
            self.assertEqual(e["sha256"], expected["lfs_oid_sha256"])
            self.assertEqual(e["lfs_oid_sha256"], expected["lfs_oid_sha256"])
            self.assertEqual(e["git_blob_sha"], expected["git_blob_sha"])
            self.assertEqual(e["size_bytes"], expected["size_bytes"])
            self.assertEqual(e["numeric_field_limit"], 2048)
            self.assertEqual(e["numeric_depth_limit"], 32)
            self.assertIs(e["bounded_numeric_scan_complete"], True)
            self.assertEqual(e["monobehaviours_total"], e["monobehaviours_parsed"])
            self.assertEqual(e["scan_evidence"], "GitHub Actions W1-AE original RC556-TAG12K LFS source inventory artifact")

    def test_w1af_original_kl545_character_lfs_sources_conserved(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43651416997"
        registry = json.loads((ROOT / "data/kl545_character_lfs_source_targets.json").read_text(encoding="utf-8"))
        pinned = {e["bundle"]: e for e in registry["sources"]}
        scans = [e for e in LEDGER["scans"] if e.get("run_url") == run]
        self.assertEqual(len(scans), 2)
        self.assertEqual({e["bundle"] for e in scans}, set(pinned))
        self.assertEqual(sum(e["size_bytes"] for e in scans), 202857969)
        self.assertEqual(sum(e["monobehaviours_total"] for e in scans), 4657)
        self.assertEqual(sum(e["monobehaviours_parsed"] for e in scans), 4657)
        self.assertEqual(sum(e["unparsed_records"] for e in scans), 0)
        self.assertEqual(sum(e["numeric_field_cap_records"] for e in scans), 0)
        self.assertEqual(sum(e["objects_by_type"].get("Mesh", 0) for e in scans), 330)
        self.assertEqual(sum(e["objects_by_type"].get("Texture2D", 0) for e in scans), 99)
        self.assertEqual(sum(e["objects_by_type"].get("AnimationClip", 0) for e in scans), 2563)
        self.assertEqual(sum(e["candidate_field_counts"]["combat"] for e in scans), 532)
        self.assertEqual(sum(e["candidate_field_counts"]["timing_and_world"] for e in scans), 5595)
        for e in scans:
            pin = pinned[e["bundle"]]
            self.assertEqual(e["git_blob_sha"], pin["git_blob_sha"])
            self.assertEqual(e["lfs_oid_sha256"], pin["lfs_oid_sha256"])
            self.assertEqual(e["sha256"], pin["lfs_oid_sha256"])
            self.assertEqual(e["size_bytes"], pin["size_bytes"])
            self.assertEqual(e["numeric_field_limit"], 2048)
            self.assertEqual(e["numeric_depth_limit"], 32)
            self.assertIs(e["bounded_numeric_scan_complete"], True)
            self.assertEqual(e["monobehaviours_total"], e["monobehaviours_parsed"])
            self.assertEqual(e["scan_evidence"], "GitHub Actions W1-AF original KL545-character LFS source inventory artifact")

    def test_w1ag_global_space_and_hub_original_source_conservation(self):
        run = "https://github.com/Nippytime/rabron/actions/runs/43652173183"
        registry = json.loads((ROOT / "data/global_hub_lfs_source_targets.json").read_text(encoding="utf-8"))
        pins = {x["bundle"]: x for x in registry["sources"]}
        scans = [x for x in LEDGER["scans"] if x.get("run_url") == run]
        self.assertEqual(len(scans), 2)
        self.assertEqual({x["bundle"] for x in scans}, set(pins))
        self.assertEqual(sum(x["size_bytes"] for x in scans), 239275331)
        self.assertEqual(sum(x["monobehaviours_total"] for x in scans), 38724)
        self.assertEqual(sum(x["monobehaviours_parsed"] for x in scans), 38724)
        self.assertEqual(sum(x["numeric_field_cap_records"] for x in scans), 2)
        self.assertEqual(sum(x["unparsed_records"] for x in scans), 0)
        self.assertEqual(sum(x["objects_by_type"].get("Mesh", 0) for x in scans), 1731)
        self.assertEqual(sum(x["objects_by_type"].get("Texture2D", 0) for x in scans), 310)
        self.assertEqual(sum(x["objects_by_type"].get("CanvasGroup", 0) for x in scans), 1804)
        self.assertEqual(sum(x["candidate_field_counts"]["timing_and_world"] for x in scans), 14525)
        for x in scans:
            original = pins[x["bundle"]]
            self.assertEqual(x["git_blob_sha"], original["git_blob_sha"])
            self.assertEqual(x["lfs_oid_sha256"], original["lfs_oid_sha256"])
            self.assertEqual(x["sha256"], original["lfs_oid_sha256"])
            self.assertEqual(x["size_bytes"], original["size_bytes"])
            self.assertEqual(x["numeric_field_limit"], 2048)
            self.assertEqual(x["numeric_depth_limit"], 32)
            self.assertEqual(x["monobehaviours_total"], x["monobehaviours_parsed"])
            self.assertEqual(x["scan_evidence"], "GitHub Actions W1-AG original global-hub LFS source inventory artifact")
        by_name = {x["bundle"].rsplit("/", 1)[-1]: x for x in scans}
        self.assertEqual(by_name["space-global_assets_all.bundle"]["numeric_field_cap_records"], 0)
        self.assertIs(by_name["space-global_assets_all.bundle"]["bounded_numeric_scan_complete"], True)
        self.assertEqual(by_name["location-hub_standalone_scenes_all.bundle"]["numeric_field_cap_records"], 2)
        self.assertIs(by_name["location-hub_standalone_scenes_all.bundle"]["bounded_numeric_scan_complete"], False)

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
        self.assertEqual(planned["historic_field_capped_records"], 76)
        self.assertEqual(planned["remaining_historic_field_capped_records"], 46)
        statuses = {entry["bundle"]: entry["status"] for entry
                    in planned["backlog"]}
        self.assertEqual(
            statuses[BUNDLE_PREFIX + "inbuild_assets_all.bundle"],
            "historic_caps_resolved_scope_partial",
        )
        self.assertEqual(planned["statuses"]["partial_field_cap"], 22)
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
