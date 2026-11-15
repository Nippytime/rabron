"""Source-only original LFS integrity and strict two-source recheck for W1-AI."""
import copy
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.weapon_lfs_inventory import (
    AI_EVIDENCE, AI_NAMES, load_targets, reconcile, source_plan, verify_pointer,
)
from reconstruction.tools.verify_priority_lfs import verify_source

ROOT = Path(__file__).resolve().parents[1]
TARGETS = load_targets(ROOT / "data/sectorcenter_common_lfs_source_targets.json")


class SectorcenterCommonLfsTests(unittest.TestCase):
    def setUp(self):
        self.git = {e["bundle"]: {"git_blob_sha": e["git_blob_sha"],
                                   "git_blob_size": 134} for e in TARGETS}
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}

    def test_original_identity_and_exact_two_source_plan(self):
        self.assertEqual(len(TARGETS), 2)
        self.assertEqual({e["bundle"].split("/")[-1] for e in TARGETS}, AI_NAMES)
        self.assertEqual(sum(e["size_bytes"] for e in TARGETS), 263147663)
        plan = source_plan(TARGETS, self.ledger, self.git,
                           expected_tracked=2, scan_evidence=AI_EVIDENCE)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(plan["documented_before"], 0)
        with self.assertRaisesRegex(ValueError, "count changed"):
            source_plan(TARGETS, self.ledger, self.git,
                        scan_evidence=AI_EVIDENCE)

    def test_workflow_follows_source_and_test_dependencies(self):
        # Both existing Python CI and LFS jobs use sparse checkouts.
        workflow = subprocess.check_output(
            ["git", "show", "HEAD:.github/workflows/"
             "extract-sectorcenter-common-lfs-sources.yml"],
            text=True, cwd=ROOT.parent,
        )
        paths = workflow.split("  pull_request:\n    paths:\n", 1)[1].split(
            "  workflow_dispatch:", 1
        )[0]
        for source in (
            "reconstruction/tools/weapon_lfs_inventory.py",
            "reconstruction/data/sectorcenter_common_lfs_source_targets.json",
            "reconstruction/tests/test_sectorcenter_common_lfs_inventory.py",
            "reconstruction/data/extraction_coverage.json",
        ):
            with self.subTest(path=source):
                self.assertIn(f'      - "{source}"', paths)
        self.assertIn("max-parallel: 2", workflow)
        self.assertIn("timeout-minutes: 55", workflow)
        self.assertIn("git lfs pull --include=", workflow)

    def test_original_pointer_is_not_accepted_as_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "original.bundle"
            data = b"UnityFS" + bytes(range(25))
            sha = hashlib.sha256(data).hexdigest()
            path.write_text(f"version https://git-lfs.github.com/spec/v1\n"
                            f"oid sha256:{sha}\nsize {len(data)}\n", encoding="ascii")
            entry = {
                "bundle": str(path), "lfs_oid_sha256": sha,
                "size_bytes": len(data),
                "git_blob_sha": hashlib.sha1(
                    b"blob " + str(path.stat().st_size).encode()
                    + b"\0" + path.read_bytes()).hexdigest(),
            }
            self.assertTrue(verify_pointer(entry)["verified"])
            with self.assertRaisesRegex(ValueError, "UnityFS"):
                verify_source(path, entry, phase="bytes")
            entry["git_blob_sha"] = "0" * 40
            with self.assertRaisesRegex(ValueError, "SHA-1 mismatch"):
                verify_pointer(entry)

    def test_changed_pointer_and_partial_source_pair_fail_closed(self):
        changed = copy.deepcopy(self.git)
        changed[TARGETS[0]["bundle"]]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "pointer blob fingerprint"):
            source_plan(TARGETS, self.ledger, changed, expected_tracked=2,
                        scan_evidence=AI_EVIDENCE)

    def test_reconcile_requires_two_real_records_then_two_real_rechecks(self):
        plan = source_plan(TARGETS, self.ledger, self.git,
                           expected_tracked=2, scan_evidence=AI_EVIDENCE)
        records = [{
            **e, "sha256": e["lfs_oid_sha256"],
            "scan_evidence": AI_EVIDENCE, "run_url": "test-run",
            "status": "documented_scan_not_fully_verified",
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "unparsed_records": 0,
            "bounded_numeric_scan_complete": True,
            "numeric_field_limit": 2048, "numeric_depth_limit": 32,
            "objects_by_type": {"AssetBundle": 1},
            "candidate_field_counts": {"combat": 0, "economy": 0,
                                       "progression": 0,
                                       "timing_and_world": 0},
        } for e in TARGETS]
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, records[:1], self.ledger, "test-run", self.git,
                      scan_evidence=AI_EVIDENCE)
        bad = copy.deepcopy(records)
        bad[0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "measured original identity"):
            reconcile(plan, bad, self.ledger, "test-run", self.git,
                      scan_evidence=AI_EVIDENCE)
        corrupt = copy.deepcopy(records)
        corrupt[1]["monobehaviours_total"] = 1
        with self.assertRaisesRegex(ValueError, "accounting"):
            reconcile(plan, corrupt, self.ledger, "test-run", self.git,
                      scan_evidence=AI_EVIDENCE)
        partial = copy.deepcopy(records)
        partial[0].update({"monobehaviours_total": 1, "unparsed_records": 1,
                           "objects_by_type": {"AssetBundle": 1,
                                               "MonoBehaviour": 1},
                           "bounded_numeric_scan_complete": False})
        report, proposed = reconcile(plan, partial, self.ledger, "test-run",
                                     self.git, scan_evidence=AI_EVIDENCE)
        self.assertEqual(report["new_documented"], 2)
        self.assertEqual(proposed["scans"][0]["unparsed_records"], 1)
        self.assertFalse(proposed["scans"][0]["bounded_numeric_scan_complete"])
        _, proposed = reconcile(plan, records, self.ledger, "test-run", self.git,
                                scan_evidence=AI_EVIDENCE)
        again = source_plan(TARGETS, proposed, self.git, expected_tracked=2,
                            scan_evidence=AI_EVIDENCE)
        self.assertEqual(again["mode"], "recheck")
        result, same = reconcile(again, records, proposed, "test-run", self.git,
                                 scan_evidence=AI_EVIDENCE)
        self.assertEqual(result["source_reverified"], 2)
        self.assertEqual(result["new_documented"], 0)
        self.assertEqual(len(same["scans"]), 2)
