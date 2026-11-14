"""Source-integrity regression tests for two original shared environment props and Wwise battle LFS bundles."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.weapon_lfs_inventory import (
    AH_EVIDENCE, AH_NAMES, load_targets, reconcile, source_plan, verify_pointer,
)
from reconstruction.tools.verify_priority_lfs import verify_source

ROOT = Path(__file__).resolve().parents[1]
TARGETS = load_targets(ROOT / "data/shared_props_wwise_lfs_source_targets.json")


class SharedPropsWwiseLfsTests(unittest.TestCase):
    def setUp(self):
        self.git = {e["bundle"]: {"git_blob_sha": e["git_blob_sha"],
                                 "git_blob_size": 133} for e in TARGETS}
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}

    def test_original_pointer_pins_and_two_source_plan(self):
        self.assertEqual(len(TARGETS), 2)
        self.assertEqual(
            {x["bundle"].rsplit("/", 1)[-1] for x in TARGETS}, AH_NAMES,
        )
        self.assertEqual(sum(x["size_bytes"] for x in TARGETS), 222568838)
        plan = source_plan(TARGETS, self.ledger, self.git,
                           expected_tracked=2, scan_evidence=AH_EVIDENCE)
        self.assertEqual(plan["mode"], "new")
        self.assertEqual(len(plan["sources"]), 2)

    def test_changed_pointer_and_partially_documented_sources_fail(self):
        with self.assertRaisesRegex(ValueError, "count changed"):
            source_plan(TARGETS, self.ledger, self.git, scan_evidence=AH_EVIDENCE)
        changed = copy.deepcopy(self.git)
        changed[TARGETS[0]["bundle"]]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "pointer blob fingerprint"):
            source_plan(TARGETS, self.ledger, changed, expected_tracked=2,
                        scan_evidence=AH_EVIDENCE)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "original.bundle"
            data = b"UnityFS" + bytes(range(25))
            sha = hashlib.sha256(data).hexdigest()
            pointer = (f"version https://git-lfs.github.com/spec/v1\n"
                       f"oid sha256:{sha}\nsize {len(data)}\n")
            path.write_text(pointer, encoding="ascii")
            original = {
                "bundle": path.as_posix(), "lfs_oid_sha256": sha,
                "size_bytes": len(data),
                "git_blob_sha": hashlib.sha1(
                    b"blob " + str(path.stat().st_size).encode() +
                    b"\0" + path.read_bytes()
                ).hexdigest(),
            }
            self.assertTrue(verify_pointer(original)["verified"])
            with self.assertRaisesRegex(ValueError, "UnityFS"):
                verify_source(path, original, phase="bytes")
            original["git_blob_sha"] = "0" * 40
            with self.assertRaisesRegex(ValueError, "SHA-1 mismatch"):
                verify_pointer(original)

    def test_two_source_reconcile_new_then_nonempty_recheck(self):
        plan = source_plan(TARGETS, self.ledger, self.git,
                           expected_tracked=2, scan_evidence=AH_EVIDENCE)
        records = [{
            **e, "sha256": e["lfs_oid_sha256"],
            "scan_evidence": AH_EVIDENCE, "run_url": "test-run",
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
            reconcile(plan, records[:1], self.ledger, "test-run", self.git,
                      scan_evidence=AH_EVIDENCE)
        bad = copy.deepcopy(records)
        bad[0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "measured original identity"):
            reconcile(plan, bad, self.ledger, "test-run", self.git,
                      scan_evidence=AH_EVIDENCE)
        # Reconciliation must reject contradictory measured metadata, even
        # when the original SHA/OID/byte fingerprints themselves match.
        mutations = (
            ("monobehaviours_total", 1),
            ("monobehaviours_parsed", 1),
            ("unparsed_records", 1),
            ("numeric_field_cap_records", 1),
            ("bounded_numeric_scan_complete", False),
            ("objects_by_type", {"AssetBundle": 1, "MonoBehaviour": 1}),
            ("objects_by_type", {"AssetBundle": 0}),
            ("candidate_field_counts", {"combat": -1, "economy": 0,
                                        "progression": 0, "timing_and_world": 0}),
        )
        for field, value in mutations:
            corrupt = copy.deepcopy(records)
            corrupt[0][field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(ValueError, "accounting"):
                    reconcile(plan, corrupt, self.ledger, "test-run", self.git,
                              scan_evidence=AH_EVIDENCE)

        # Real source inventories may legitimately have unparsed records and
        # numeric caps; preserve these explicitly instead of claiming success.
        partial = copy.deepcopy(records)
        partial[0].update({
            "monobehaviours_total": 3, "monobehaviours_parsed": 2,
            "unparsed_records": 1, "numeric_field_cap_records": 1,
            "bounded_numeric_scan_complete": False,
            "objects_by_type": {"AssetBundle": 1, "MonoBehaviour": 3},
        })
        partial_report, partial_ledger = reconcile(
            plan, partial, self.ledger, "test-run", self.git,
            scan_evidence=AH_EVIDENCE,
        )
        self.assertEqual(partial_report["new_documented"], 2)
        self.assertEqual(partial_ledger["scans"][0]["unparsed_records"], 1)
        self.assertEqual(partial_ledger["scans"][0]["numeric_field_cap_records"], 1)
        report, proposed = reconcile(
            plan, records, self.ledger, "test-run", self.git,
            scan_evidence=AH_EVIDENCE,
        )
        self.assertEqual(report["new_documented"], 2)
        self.assertEqual(len(proposed["scans"]), 2)
        again = source_plan(
            TARGETS, proposed, self.git, expected_tracked=2,
            scan_evidence=AH_EVIDENCE,
        )
        self.assertEqual(again["mode"], "recheck")
        rechecked, same = reconcile(
            again, records, proposed, "test-run", self.git,
            scan_evidence=AH_EVIDENCE,
        )
        self.assertEqual(rechecked["source_reverified"], 2)
        self.assertEqual(len(same["scans"]), 2)
