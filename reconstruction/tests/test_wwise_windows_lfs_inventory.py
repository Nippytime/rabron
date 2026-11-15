"""W1-AL exact original Wwise singleton: fail-closed source and recheck tests.

Unit fixtures never substitute for a Git LFS original-byte Action.
"""
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
    AL_EVIDENCE, AL_NAMES, AJ_EVIDENCE, DEPTH, FIELDS, load_targets,
    reconcile, scan, source_plan, verify_pointer,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/wwise_windows_lfs_source_targets.json"
WORKFLOW = ".github/workflows/extract-wwise-windows-lfs-sources.yml"
TARGETS = load_targets(MANIFEST)


class WwiseWindowsLfsTests(unittest.TestCase):
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
                           expected_tracked=1, scan_evidence=AL_EVIDENCE)

    def test_exact_single_original_identity_not_pointer_evidence(self):
        self.assertEqual(len(TARGETS), 1)
        self.assertEqual({Path(t["bundle"]).name for t in TARGETS}, AL_NAMES)
        self.assertEqual(self.target["git_blob_sha"],
                         "40324cc5a4281d764319e2291e9fb7c142208c57")
        self.assertEqual(self.target["lfs_oid_sha256"],
                         "d84888fe94f74b5cb817749abbcb1af59225300523ad9a1a14e01f475e08fb35")
        self.assertEqual(self.target["size_bytes"], 170634407)
        data = json.loads((ROOT / "data/extraction_coverage.json").read_text())
        records = [s for s in data["scans"]
                   if s["bundle"] == self.target["bundle"]]
        # Before original-byte CI the record is absent; after measured PR
        # update it must match exact source fingerprint and evidence tag.
        self.assertEqual(len(records), 1)
        self.assertEqual(len(data["scans"]), 329)
        for row in records:
            for key, expected in (
                ("sha256", self.target["lfs_oid_sha256"]),
                ("lfs_oid_sha256", self.target["lfs_oid_sha256"]),
                ("git_blob_sha", self.target["git_blob_sha"]),
                ("size_bytes", self.target["size_bytes"]),
                ("scan_evidence", AL_EVIDENCE),
            ):
                self.assertEqual(row[key], expected)

    def test_measured_original_records_preserve_explicit_numeric_limits(self):
        ledger = json.loads((ROOT / "data/extraction_coverage.json").read_text())
        record = next(s for s in ledger["scans"]
                      if s["bundle"] == self.target["bundle"])
        self.assertEqual(record["monobehaviours_total"], 275)
        self.assertEqual(record["monobehaviours_parsed"], 274)
        self.assertEqual(record["unparsed_records"], 1)
        self.assertEqual(record["numeric_field_cap_records"], 274)
        self.assertIs(record["bounded_numeric_scan_complete"], False)
        self.assertEqual(record["objects_by_type"],
                         {"AssetBundle": 1, "MonoBehaviour": 275})
        self.assertEqual(record["candidate_field_counts"], {
            "combat": 0, "economy": 0, "progression": 0,
            "timing_and_world": 0,
        })
        self.assertEqual(record["numeric_field_limit"], 2048)
        self.assertEqual(record["numeric_depth_limit"], 32)
        self.assertTrue(record["status"].startswith("documented_scan"))
        self.assertEqual(record["run_url"],
                         "https://github.com/Nippytime/rabron/actions/runs/43673281268")

    def test_rejects_other_singletons_and_partial_legacy_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "targets.json"
            data = json.loads(MANIFEST.read_text())
            data["sources"][0]["bundle"] = (
                "StreamingAssets/aa/StandaloneWindows64/not-wwise.bundle"
            )
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Unexpected original"):
                load_targets(path)
            data = json.loads(MANIFEST.read_text())
            data["sources"] *= 2
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Unexpected original"):
                load_targets(path)
        pair = load_targets(ROOT / "data/characters_legacy_props_lfs_source_targets.json")
        entries = {s["bundle"]: {"git_blob_sha": s["git_blob_sha"],
                                 "git_blob_size": 134} for s in pair}
        plan = source_plan(pair, self.ledger, entries, expected_tracked=2,
                           scan_evidence=AJ_EVIDENCE)
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, [self.fake_record()], self.ledger,
                      "https://example.org/run", entries,
                      scan_evidence=AJ_EVIDENCE)

    def test_size_exception_is_exact_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "targets.json"
            data = json.loads(MANIFEST.read_text())
            data["sources"][0]["size_bytes"] = 175000001
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Invalid original"):
                load_targets(path)

    def test_git_pointer_never_meets_binary_integrity_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.bundle"
            content = b"UnityFS" + bytes(range(32))
            digest = hashlib.sha256(content).hexdigest()
            path.write_text(
                "version https://git-lfs.github.com/spec/v1\n"
                f"oid sha256:{digest}\nsize {len(content)}\n",
                encoding="ascii",
            )
            raw = path.read_bytes()
            pointer_sha = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest()
            entry = {"bundle": str(path), "git_blob_sha": pointer_sha,
                     "lfs_oid_sha256": digest, "size_bytes": len(content)}
            verify_pointer(entry)
            with self.assertRaises(ValueError):
                verify_source(path, entry, phase="bytes")

    def fake_record(self):
        item = self.target
        return {
            "bundle": item["bundle"], "git_blob_sha": item["git_blob_sha"],
            "lfs_oid_sha256": item["lfs_oid_sha256"],
            "sha256": item["lfs_oid_sha256"], "size_bytes": item["size_bytes"],
            "scan_evidence": AL_EVIDENCE,
            "run_url": "https://example.org/run",
            "status": "documented_scan_not_fully_verified",
            "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
            "monobehaviours_total": 1, "monobehaviours_parsed": 1,
            "unparsed_records": 0, "numeric_field_cap_records": 0,
            "bounded_numeric_scan_complete": True,
            "objects_by_type": {"MonoBehaviour": 1},
            "candidate_field_counts": {
                "combat": 0, "economy": 0, "progression": 0,
                "timing_and_world": 0,
            },
        }

    def test_singleton_reconciliation_accepts_only_complete_identity(self):
        plan, record = self.plan(), self.fake_record()
        url = record["run_url"]
        report, ledger = reconcile(
            plan, [record], self.ledger, url, self.entries,
            scan_evidence=AL_EVIDENCE,
        )
        self.assertEqual(report["new_documented"], 1)
        self.assertEqual(report["source_reverified"], 0)
        self.assertEqual(len(ledger["scans"]), 1)
        old = self.ledger
        self.ledger = ledger
        recheck = self.plan()
        self.assertEqual(recheck["mode"], "recheck")
        result, stable = reconcile(
            recheck, [record], ledger, url, self.entries,
            scan_evidence=AL_EVIDENCE,
        )
        self.assertEqual(result["new_documented"], 0)
        self.assertEqual(result["source_reverified"], 1)
        self.assertEqual(stable, ledger)
        self.ledger = old

    def test_rejects_missing_duplicate_and_forged_singleton(self):
        plan, record = self.plan(), self.fake_record()
        url = record["run_url"]
        for rows in ([], [record, record]):
            with self.subTest(length=len(rows)):
                with self.assertRaisesRegex(ValueError, "coverage/accounting"):
                    reconcile(plan, rows, self.ledger, url, self.entries,
                              scan_evidence=AL_EVIDENCE)
        forged = {**record, "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "original identity"):
            reconcile(plan, [forged], self.ledger, url, self.entries,
                      scan_evidence=AL_EVIDENCE)
        negative = {**record, "objects_by_type": {"MonoBehaviour": 0}}
        with self.assertRaisesRegex(ValueError, "accounting mismatch"):
            reconcile(plan, [negative], self.ledger, url, self.entries,
                      scan_evidence=AL_EVIDENCE)

    def test_wwise_uses_bounded_stream_without_original_media_export(self):
        fields = {key: {"matching_numeric_fields": 0}
                  for key in ("combat", "economy", "progression",
                              "timing_and_world")}
        validated = {
            "monobehaviours_total": 0, "parsed": 0, "unparsed": 0,
            "truncated": 0, "bounded_mono_numeric_complete": True,
            "object_types": {"AssetBundle": 1},
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
            rec = scan(self.target, "https://example.org/run",
                       scan_evidence=AL_EVIDENCE)
        stream.assert_called_once()
        self.assertEqual(rec["objects_by_type"], {"AssetBundle": 1})
        self.assertEqual(rec["monobehaviours_total"], 0)

    def test_workflow_scoped_original_only_and_nonoptional_reconcile(self):
        yaml = subprocess.check_output(
            ["git", "show", f"HEAD:{WORKFLOW}"], text=True, cwd=ROOT.parent
        )
        for path in (WORKFLOW,
                     "reconstruction/tools/weapon_lfs_inventory.py",
                     "reconstruction/data/extraction_coverage.json",
                     "reconstruction/data/wwise_windows_lfs_source_targets.json",
                     "reconstruction/tests/test_wwise_windows_lfs_inventory.py"):
            self.assertIn(f'      - "{path}"', yaml)
        self.assertEqual(
            yaml.count("StreamingAssets/aa/StandaloneWindows64/"
                       "wwisedata_windows_assets_all.bundle"), 1
        )
        for token in ("max-parallel: 1", "timeout-minutes: 55",
                      "git lfs pull --include=",
                      "if-no-files-found: error",
                      "needs.plan.result == 'success' && needs.inspect.result == 'success'"):
            self.assertIn(token, yaml)


if __name__ == "__main__":
    unittest.main()
