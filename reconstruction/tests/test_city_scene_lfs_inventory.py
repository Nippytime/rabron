"""W1-AM one original 550 MB city scene: strict source-only provenance tests."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reconstruction.tools.verify_priority_lfs import verify_source
from reconstruction.tools.weapon_lfs_inventory import (
    AL_EVIDENCE, AM_EVIDENCE, AM_NAMES, DEPTH, FIELDS,
    load_targets, reconcile, scan, source_plan, verify_pointer,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/city_scene_lfs_source_target.json"
WORKFLOW = ".github/workflows/extract-city-scene-lfs-source.yml"
TARGETS = load_targets(MANIFEST)


class CitySceneLfsTests(unittest.TestCase):
    def setUp(self):
        self.target = TARGETS[0]
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.entries = {self.target["bundle"]: {
            "git_blob_sha": self.target["git_blob_sha"],
            "git_blob_size": 134,
        }}

    def plan(self):
        return source_plan(TARGETS, self.ledger, self.entries,
                           expected_tracked=1, scan_evidence=AM_EVIDENCE)

    def fake_record(self):
        e = self.target
        return {
            "bundle": e["bundle"], "git_blob_sha": e["git_blob_sha"],
            "lfs_oid_sha256": e["lfs_oid_sha256"],
            "sha256": e["lfs_oid_sha256"], "size_bytes": e["size_bytes"],
            "scan_evidence": AM_EVIDENCE, "run_url": "https://example.org/run",
            "status": "documented_scan_not_fully_verified",
            "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
            "monobehaviours_total": 1, "monobehaviours_parsed": 0,
            "unparsed_records": 1, "numeric_field_cap_records": 0,
            "bounded_numeric_scan_complete": False,
            "objects_by_type": {"MonoBehaviour": 1},
            "candidate_field_counts": {"combat": 0, "economy": 0,
                                       "progression": 0, "timing_and_world": 0},
        }

    def test_original_identity_and_ledger_not_credited_from_pointer(self):
        self.assertEqual(len(TARGETS), 1)
        self.assertEqual({Path(e["bundle"]).name for e in TARGETS}, AM_NAMES)
        self.assertEqual(self.target["git_blob_sha"],
                         "c73e7b84edc6b4e73001923054ff3a29bd540393")
        self.assertEqual(self.target["lfs_oid_sha256"],
                         "5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f")
        self.assertEqual(self.target["size_bytes"], 549566135)
        ledger = json.loads((ROOT / "data/extraction_coverage.json").read_text())
        matches = [x for x in ledger["scans"]
                   if x["bundle"] == self.target["bundle"]]
        # Before actual source CI it must be absent; afterward it must retain
        # exactly measured original SHA, source and incomplete numeric status.
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(ledger["scans"]), 330)
        for item in matches:
            for key, expected in (
                ("sha256", self.target["lfs_oid_sha256"]),
                ("lfs_oid_sha256", self.target["lfs_oid_sha256"]),
                ("git_blob_sha", self.target["git_blob_sha"]),
                ("size_bytes", self.target["size_bytes"]),
                ("scan_evidence", AM_EVIDENCE),
            ):
                self.assertEqual(item[key], expected)

    def test_measured_city_object_and_bounded_numeric_counts(self):
        ledger = json.loads((ROOT / "data/extraction_coverage.json").read_text())
        record = next(x for x in ledger["scans"]
                      if x["bundle"] == self.target["bundle"])
        self.assertEqual(sum(record["objects_by_type"].values()), 366174)
        self.assertEqual(record["objects_by_type"]["MonoBehaviour"], 14467)
        self.assertEqual(record["objects_by_type"]["GameObject"], 97446)
        self.assertEqual(record["objects_by_type"]["Transform"], 97437)
        self.assertEqual(record["monobehaviours_total"], 14467)
        self.assertEqual(record["monobehaviours_parsed"], 14467)
        self.assertEqual(record["unparsed_records"], 0)
        self.assertEqual(record["numeric_field_cap_records"], 5)
        self.assertIs(record["bounded_numeric_scan_complete"], False)
        self.assertEqual(record["candidate_field_counts"], {
            "combat": 195, "economy": 133,
            "progression": 144, "timing_and_world": 8201,
        })
        self.assertEqual(record["numeric_field_limit"], 2048)
        self.assertEqual(record["numeric_depth_limit"], 32)
        self.assertEqual(record["run_url"],
                         "https://github.com/Nippytime/rabron/actions/runs/43675221667")

    def test_only_named_city_and_wwise_singletons_allowed(self):
        self.assertEqual(self.plan()["mode"], "new")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            base = json.loads(MANIFEST.read_text())
            for new_sources in (
                [], [base["sources"][0]] * 2,
                [{**base["sources"][0],
                  "bundle": "StreamingAssets/aa/StandaloneWindows64/other.bundle"}],
            ):
                data = {**base, "sources": new_sources}
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "Unexpected original"):
                    load_targets(path)
        wwise = load_targets(ROOT / "data/wwise_windows_lfs_source_targets.json")
        self.assertEqual(len(wwise), 1)
        self.assertNotEqual(wwise[0]["bundle"], self.target["bundle"])
        self.assertEqual(
            source_plan(wwise, self.ledger, {
                wwise[0]["bundle"]: {"git_blob_sha": wwise[0]["git_blob_sha"],
                                    "git_blob_size": 134}
            }, expected_tracked=1, scan_evidence=AL_EVIDENCE)["mode"], "new",
        )
        # A legacy paired scope must not reconcile a singleton result.
        pair = load_targets(ROOT / "data/characters_legacy_props_lfs_source_targets.json")
        entries = {x["bundle"]: {"git_blob_sha": x["git_blob_sha"],
                                  "git_blob_size": 134} for x in pair}
        plan = source_plan(pair, self.ledger, entries, expected_tracked=2)
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, [self.fake_record()], self.ledger,
                      "https://example.org/run", entries)

    def test_exact_source_size_scope_not_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(MANIFEST.read_text())
            data["sources"][0]["size_bytes"] = 565_000_001
            path = Path(tmp) / "sources.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Invalid original"):
                load_targets(path)
        with self.assertRaisesRegex(ValueError, "count changed"):
            source_plan(TARGETS, self.ledger, self.entries,
                        expected_tracked=330, scan_evidence=AM_EVIDENCE)

    def test_git_pointer_is_not_full_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "pointer.bundle"
            source = b"UnityFS" + bytes(range(32))
            digest = hashlib.sha256(source).hexdigest()
            f.write_text(
                "version https://git-lfs.github.com/spec/v1\n"
                f"oid sha256:{digest}\nsize {len(source)}\n", encoding="ascii"
            )
            pointer = f.read_bytes()
            sha = hashlib.sha1(b"blob " + str(len(pointer)).encode() +
                               b"\0" + pointer).hexdigest()
            entry = {"bundle": str(f), "git_blob_sha": sha,
                     "lfs_oid_sha256": digest, "size_bytes": len(source)}
            verify_pointer(entry)
            with self.assertRaises(ValueError):
                verify_source(f, entry, phase="bytes")

    def test_exact_new_and_recheck_conserve_original_evidence(self):
        plan, record = self.plan(), self.fake_record()
        url = record["run_url"]
        summary, proposed = reconcile(
            plan, [record], self.ledger, url, self.entries,
            scan_evidence=AM_EVIDENCE,
        )
        self.assertEqual(summary["new_documented"], 1)
        self.assertEqual(summary["source_reverified"], 0)
        self.assertEqual(len(proposed["scans"]), 1)
        self.ledger = proposed
        fresh = self.plan()
        self.assertEqual(fresh["mode"], "recheck")
        second, unchanged = reconcile(
            fresh, [record], proposed, url, self.entries,
            scan_evidence=AM_EVIDENCE,
        )
        self.assertEqual(second["new_documented"], 0)
        self.assertEqual(second["source_reverified"], 1)
        self.assertEqual(unchanged, proposed)

    def test_missing_duplicate_forged_or_incomplete_source_rejected(self):
        plan, record = self.plan(), self.fake_record()
        url = record["run_url"]
        for bad in ([], [record, record]):
            with self.assertRaisesRegex(ValueError, "coverage/accounting"):
                reconcile(plan, bad, self.ledger, url, self.entries,
                          scan_evidence=AM_EVIDENCE)
        bad = {**record, "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "original identity"):
            reconcile(plan, [bad], self.ledger, url, self.entries,
                      scan_evidence=AM_EVIDENCE)
        bad = {**record, "bounded_numeric_scan_complete": True}
        with self.assertRaisesRegex(ValueError, "accounting mismatch"):
            reconcile(plan, [bad], self.ledger, url, self.entries,
                      scan_evidence=AM_EVIDENCE)

    def test_city_stream_is_scoped_and_preserves_container(self):
        fields = {k: {"matching_numeric_fields": 0}
                  for k in ("combat", "economy", "progression",
                            "timing_and_world")}
        validated = {
            "monobehaviours_total": 0, "parsed": 0, "unparsed": 0,
            "truncated": 0, "bounded_mono_numeric_complete": True,
            "object_types": {"GameObject": 1},
        }
        with (patch("reconstruction.tools.weapon_lfs_inventory.verify_source",
                    return_value={"sha256": self.target["lfs_oid_sha256"]}),
              patch("reconstruction.tools.weapon_lfs_inventory.scan_bundle",
                    return_value={}),
              patch("reconstruction.tools.weapon_lfs_inventory.summarize",
                    return_value={"candidate_field_groups": fields}),
              patch("reconstruction.tools.weapon_lfs_inventory.validate",
                    return_value=validated),
              patch("reconstruction.tools.streamed_unityfs.streamed_unityfs") as stream):
            record = scan(self.target, "https://example.org/run",
                          scan_evidence=AM_EVIDENCE)
        from reconstruction.tools.streamed_unityfs import MAX_CITY_MONO_OBJECT_BYTES
        stream.assert_called_once_with(
            mono_budget_bytes=MAX_CITY_MONO_OBJECT_BYTES,
            scope="CITY", skip_container_index=False,
        )
        self.assertEqual(record["objects_by_type"], {"GameObject": 1})

    def test_workflow_is_one_original_and_reconcile_is_mandatory(self):
        workflow = subprocess.check_output(
            ["git", "show", f"HEAD:{WORKFLOW}"], text=True, cwd=ROOT.parent
        )
        for path in (
            WORKFLOW,
            "reconstruction/data/city_scene_lfs_source_target.json",
            "reconstruction/data/extraction_coverage.json",
            "reconstruction/tools/weapon_lfs_inventory.py",
            "reconstruction/tools/streamed_unityfs.py",
            "reconstruction/tests/test_city_scene_lfs_inventory.py",
        ):
            self.assertIn(f'      - "{path}"', workflow)
        self.assertEqual(workflow.count(
            "StreamingAssets/aa/StandaloneWindows64/"
            "location-city-standalone_scenes_city_standalone.unity.bundle"
        ), 1)
        for token in ("max-parallel: 1", "timeout-minutes: 55",
                      "git lfs pull --include=", "if-no-files-found: error",
                      "needs.plan.result == 'success' && needs.inspect.result == 'success'"):
            self.assertIn(token, workflow)


if __name__ == "__main__":
    unittest.main()
