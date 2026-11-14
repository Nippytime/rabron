"""Synthetic-source integrity and strict scope tests for two weapon Git LFS originals."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.weapon_lfs_inventory import (
    NAMES, load_targets, reconcile, source_plan, verify_pointer, EVIDENCE
)

ROOT = Path(__file__).resolve().parents[1]
TARGETS = load_targets(ROOT / "data/weapon_lfs_source_targets.json")


class WeaponLfsInventoryTests(unittest.TestCase):
    def setUp(self):
        self.entries = {
            e["bundle"]: {"git_blob_sha": e["git_blob_sha"], "git_blob_size": 134}
            for e in TARGETS
        }
        self.ledger = {"schema_version": 1, "scans": [], "known_lfs_not_yet_scanned": []}

    def test_exact_original_pointer_pins_and_bounded_scope(self):
        self.assertEqual(len(TARGETS), 2)
        self.assertEqual({x["bundle"].rsplit("/", 1)[-1] for x in TARGETS}, NAMES)
        self.assertEqual(sum(e["size_bytes"] for e in TARGETS), 109658562)
        self.assertTrue(all(len(e["lfs_oid_sha256"]) == 64 and
                            len(e["git_blob_sha"]) == 40 for e in TARGETS))
        plan = source_plan(TARGETS, self.ledger, self.entries, expected_tracked=2)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(len(plan["sources"]), 2)

    def test_missing_pointer_and_partial_recheck_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "count changed"):
            source_plan(TARGETS, self.ledger, self.entries)
        changed = copy.deepcopy(self.entries)
        changed.pop(TARGETS[0]["bundle"])
        with self.assertRaisesRegex(ValueError, "pointer blob fingerprint"):
            source_plan(TARGETS, self.ledger, changed, expected_tracked=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.bundle"
            data = b"UnityFS" + bytes(range(24))
            sha = hashlib.sha256(data).hexdigest()
            pointer = (f"version https://git-lfs.github.com/spec/v1\n"
                       f"oid sha256:{sha}\nsize {len(data)}\n")
            path.write_text(pointer, encoding="ascii")
            original = {"bundle": path.as_posix(), "lfs_oid_sha256": sha,
                        "size_bytes": len(data),
                        "git_blob_sha": hashlib.sha1(
                            b"blob " + str(path.stat().st_size).encode() +
                            b"\0" + path.read_bytes()).hexdigest()}
            self.assertTrue(verify_pointer(original)["verified"])
            original["git_blob_sha"] = "0" * 40
            with self.assertRaisesRegex(ValueError, "SHA-1 mismatch"):
                verify_pointer(original)

    def test_reconcile_rejects_partial_or_unverified_records(self):
        plan = source_plan(TARGETS, self.ledger, self.entries, expected_tracked=2)
        records = [{
            **e, "sha256": e["lfs_oid_sha256"], "run_url": "test-run",
            "scan_evidence": EVIDENCE,
            "status": "documented_scan_not_fully_verified",
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "unparsed_records": 0,
            "bounded_numeric_scan_complete": True,
            "numeric_field_limit": 2048, "numeric_depth_limit": 32,
            "objects_by_type": {"AssetBundle": 1},
            "candidate_field_counts": {"combat": 0, "economy": 0,
                                       "progression": 0, "timing_and_world": 0},
        } for e in TARGETS]
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, records[:1], self.ledger, "test-run", self.entries)
        altered = copy.deepcopy(records)
        altered[0]["sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "measured original identity"):
            reconcile(plan, altered, self.ledger, "test-run", self.entries)
        report, proposed = reconcile(plan, records, self.ledger,
                                     "test-run", self.entries)
        self.assertEqual(report["new_documented"], 2)
        self.assertEqual(len(proposed["scans"]), 2)
        after = source_plan(TARGETS, proposed, self.entries, expected_tracked=2)
        self.assertEqual(after["mode"], "recheck")
        second, same = reconcile(after, records, proposed, "test-run", self.entries)
        self.assertEqual(second["source_reverified"], 2)
        self.assertEqual(len(same["scans"]), 2)
