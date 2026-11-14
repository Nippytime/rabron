"""Pure tests for source-verified, selected path-ID overflow recovery."""

import unittest
from pathlib import Path

from reconstruction.tools.rescan_capped_fields import (
    HISTORIC_FIELD_LIMITS, historical_entry, rescan,
)

SOURCE = "StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle"
SHA = "f" * 64
OLD = {
    "bundle": SOURCE,
    "sha256": SHA,
    "monobehaviours_total": 2,
    "monobehaviours_parsed": 2,
    "numeric_field_cap_records": 1,
    "scan_evidence": "historic-scan.md",
}


def record(path_id, reasons=()):
    return {
        "path_id": str(path_id), "status": "parsed", "name": "Test config",
        "numeric_fields": [{"path": "$.counter", "value": 7}],
        "fields_truncated": bool(reasons),
        "numeric_truncation_reasons": list(reasons),
    }


class RecordingScanner:
    def __init__(self, *, retry_needed=False, missing=False, wrong_sha=False):
        self.calls = []
        self.retry_needed = retry_needed
        self.missing = missing
        self.wrong_sha = wrong_sha

    def __call__(self, path, *, expected_sha256, max_fields, max_depth,
                 path_ids=None):
        self.calls.append((max_fields, max_depth, path_ids))
        if path_ids is None:
            records = [record(111, ("field_limit",)), record(222)]
            total = 2
        else:
            assert set(path_ids) == {"111"}, path_ids
            total = 2
            records = [] if self.missing else [
                record(111, ("field_limit",))
                if self.retry_needed and max_fields == 8192 else record(111)
            ]
        return {
            "sha256": "a" * 64 if self.wrong_sha else expected_sha256,
            "monobehaviours_total": total,
            "monobehaviours_parsed": 2 if path_ids is None else len(records),
            "limit_reached": False,
            "missing_path_ids": ["111"] if self.missing and path_ids else [],
            "records": records,
        }


class TargetedRecoveryTests(unittest.TestCase):
    def test_historical_fields_limits_are_explicit(self):
        self.assertEqual(HISTORIC_FIELD_LIMITS[
            "scriptableobjects_assets_all.bundle"], 4096)
        self.assertEqual(HISTORIC_FIELD_LIMITS[
            "location-settlement-data_assets_all.bundle"], 512)
        self.assertEqual(HISTORIC_FIELD_LIMITS["inbuild_assets_all.bundle"], 256)
        self.assertEqual(len(HISTORIC_FIELD_LIMITS), 7)

    def test_selects_only_historically_field_capped_record(self):
        scanner = RecordingScanner()
        result = rescan(Path(SOURCE), OLD, first_limit=4096,
                        scanner=scanner)
        self.assertEqual(result["historical_field_cap_records_reproduced"], 1)
        self.assertEqual(result["targeted_path_ids"], ["111"])
        self.assertEqual(result["resolved_records"], 1)
        self.assertEqual(result["unresolved_records"], 0)
        self.assertTrue(result["targeted_numeric_extraction_complete"])
        self.assertFalse(result["full_bundle_numeric_extraction_complete"])
        self.assertEqual(scanner.calls, [
            (4096, 16, None), (8192, 32, {"111"})
        ])

    def test_retries_unresolved_only_with_hard_limit(self):
        scanner = RecordingScanner(retry_needed=True)
        result = rescan(Path(SOURCE), OLD, first_limit=4096,
                        scanner=scanner)
        self.assertEqual(result["adaptive_retried_records"], 1)
        self.assertEqual(result["resolved_records"], 1)
        self.assertEqual(scanner.calls[-1], (16384, 48, {"111"}))

    def test_missing_selected_source_is_not_silently_accepted(self):
        scanner = RecordingScanner(missing=True)
        with self.assertRaisesRegex(ValueError, "lost selected"):
            rescan(Path(SOURCE), OLD, first_limit=4096, scanner=scanner)

    def test_source_fingerprint_difference_is_fatal(self):
        scanner = RecordingScanner(wrong_sha=True)
        with self.assertRaisesRegex(ValueError, "Source differs"):
            rescan(Path(SOURCE), OLD, first_limit=4096, scanner=scanner)

    def test_historical_ledger_mismatch_is_fatal(self):
        bad = {**OLD, "numeric_field_cap_records": 2}
        with self.assertRaisesRegex(ValueError, "do not reproduce"):
            rescan(Path(SOURCE), bad, first_limit=4096,
                   scanner=RecordingScanner())

    def test_rejects_invalid_limits_or_unknown_historic_source(self):
        with self.assertRaisesRegex(ValueError, "Invalid bounded"):
            rescan(Path(SOURCE), OLD, first_limit=4096,
                   target_limit=3000, scanner=RecordingScanner())
        with self.assertRaisesRegex(ValueError, "documented historical scan"):
            historical_entry({"schema_version": 1, "scans": []}, SOURCE)
        self.assertEqual(historical_entry(
            {"schema_version": 1, "scans": [OLD]}, SOURCE), OLD)


if __name__ == "__main__":
    unittest.main()
