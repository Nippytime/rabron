"""Fail-closed original LFS source planning and recheck for W1-AJ."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.verify_priority_lfs import verify_source
from reconstruction.tools.weapon_lfs_inventory import (
    AJ_EVIDENCE, AJ_NAMES, DEPTH, FIELDS, load_targets, reconcile,
    source_plan, verify_pointer,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/characters_legacy_props_lfs_source_targets.json"
WORKFLOW = ".github/workflows/extract-characters-legacy-props-lfs-sources.yml"
TARGETS = load_targets(MANIFEST)


class CharactersLegacyPropsLfsTests(unittest.TestCase):
    def setUp(self):
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}
        self.entries = {
            t["bundle"]: {"git_blob_sha": t["git_blob_sha"],
                          "git_blob_size": 134}
            for t in TARGETS
        }

    def plan(self):
        return source_plan(TARGETS, self.ledger, self.entries,
                           expected_tracked=2, scan_evidence=AJ_EVIDENCE)

    def test_two_pinned_original_lfs_targets(self):
        self.assertEqual(len(TARGETS), 2)
        self.assertEqual({Path(t["bundle"]).name for t in TARGETS}, AJ_NAMES)
        self.assertEqual(sum(t["size_bytes"] for t in TARGETS), 348087169)
        ledger = json.loads((ROOT / "data/extraction_coverage.json").read_text())
        records = [s for s in ledger["scans"]
                   if s["bundle"] in {t["bundle"] for t in TARGETS}]
        # Never infer an original scan from a Git LFS pointer.
        self.assertEqual(len(records), 2)
        self.assertEqual(len(ledger["scans"]), 328)
        for row in records:
            target = next(t for t in TARGETS if t["bundle"] == row["bundle"])
            for key, expected in (
                ("sha256", target["lfs_oid_sha256"]),
                ("lfs_oid_sha256", target["lfs_oid_sha256"]),
                ("git_blob_sha", target["git_blob_sha"]),
                ("size_bytes", target["size_bytes"]),
                ("scan_evidence", AJ_EVIDENCE),
            ):
                self.assertEqual(row[key], expected)

    def test_exact_two_source_plan_rejects_drift(self):
        self.assertEqual(self.plan()["mode"], "new")
        with self.assertRaisesRegex(ValueError, "count changed"):
            source_plan(TARGETS, self.ledger, self.entries,
                        scan_evidence=AJ_EVIDENCE)
        bad = copy.deepcopy(self.entries)
        bad[TARGETS[0]["bundle"]]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "fingerprint drift"):
            source_plan(TARGETS, self.ledger, bad, expected_tracked=2,
                        scan_evidence=AJ_EVIDENCE)

    def test_larger_input_exception_is_not_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            data = json.loads(MANIFEST.read_text())
            data["sources"][0]["size_bytes"] = 185_000_001
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Invalid original"):
                load_targets(path)
            data = json.loads(MANIFEST.read_text())
            data["sources"][0]["bundle"] = (
                "StreamingAssets/aa/StandaloneWindows64/"
                "unapproved-original.bundle"
            )
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Unexpected original"):
                load_targets(path)

    def test_git_lfs_pointer_never_satisfies_full_byte_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.bundle"
            payload = b"UnityFS" + bytes(range(32))
            sha = hashlib.sha256(payload).hexdigest()
            path.write_text(
                "version https://git-lfs.github.com/spec/v1\n"
                f"oid sha256:{sha}\nsize {len(payload)}\n", encoding="ascii"
            )
            raw = path.read_bytes()
            git_sha = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest()
            entry = {"bundle": str(path), "git_blob_sha": git_sha,
                     "lfs_oid_sha256": sha, "size_bytes": len(payload)}
            verify_pointer(entry)
            with self.assertRaises(ValueError):
                verify_source(path, entry, phase="bytes")

    def test_strict_reconciliation_rejects_partial_duplicate_forged(self):
        plan = self.plan()
        url = "https://example.org/original-source-run"
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, [], self.ledger, url, self.entries,
                      scan_evidence=AJ_EVIDENCE)
        record = {
            "bundle": TARGETS[0]["bundle"],
            "git_blob_sha": TARGETS[0]["git_blob_sha"],
            "lfs_oid_sha256": TARGETS[0]["lfs_oid_sha256"],
            "sha256": TARGETS[0]["lfs_oid_sha256"],
            "size_bytes": TARGETS[0]["size_bytes"],
            "scan_evidence": AJ_EVIDENCE, "run_url": url,
            "status": "documented_scan_not_fully_verified",
            "numeric_field_limit": FIELDS, "numeric_depth_limit": DEPTH,
            "monobehaviours_total": 1, "monobehaviours_parsed": 1,
            "unparsed_records": 0, "numeric_field_cap_records": 0,
            "bounded_numeric_scan_complete": True,
            "objects_by_type": {"MonoBehaviour": 1},
            "candidate_field_counts": {
                "economy": 0, "combat": 0,
                "progression": 0, "timing_and_world": 0,
            },
        }
        with self.assertRaisesRegex(ValueError, "coverage/accounting"):
            reconcile(plan, [record, record], self.ledger, url,
                      self.entries, scan_evidence=AJ_EVIDENCE)
        other = dict(record)
        other.update(
            bundle=TARGETS[1]["bundle"],
            git_blob_sha=TARGETS[1]["git_blob_sha"],
            lfs_oid_sha256=TARGETS[1]["lfs_oid_sha256"],
            sha256="0" * 64,
            size_bytes=TARGETS[1]["size_bytes"],
        )
        with self.assertRaisesRegex(ValueError, "original identity"):
            reconcile(plan, [record, other], self.ledger, url,
                      self.entries, scan_evidence=AJ_EVIDENCE)

    def test_workflow_checks_exact_sources_and_no_skipped_reconcile(self):
        workflow = subprocess.check_output(
            ["git", "show", f"HEAD:{WORKFLOW}"],
            text=True, cwd=ROOT.parent,
        )
        for path in (
            WORKFLOW,
            "reconstruction/tools/weapon_lfs_inventory.py",
            "reconstruction/data/extraction_coverage.json",
            "reconstruction/data/characters_legacy_props_lfs_source_targets.json",
            "reconstruction/tests/test_characters_legacy_props_lfs_inventory.py",
        ):
            with self.subTest(path=path):
                self.assertIn(f'      - "{path}"', workflow)
        for name in AJ_NAMES:
            self.assertIn("StreamingAssets/aa/StandaloneWindows64/" + name,
                          workflow)
        for token in (
            "max-parallel: 2", "timeout-minutes: 55",
            "git lfs pull --include=", "if-no-files-found: error",
            "needs.plan.result == 'success' && needs.inspect.result == 'success'",
        ):
            self.assertIn(token, workflow)


if __name__ == "__main__":
    unittest.main()
