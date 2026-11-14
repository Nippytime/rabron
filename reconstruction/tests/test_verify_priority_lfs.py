"""Checks real Git LFS source registry and fail-closed pointer/binary verification."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.verify_priority_lfs import source_entry, verify_source

ROOT = Path(__file__).resolve().parents[1]
LEDGER = json.loads((ROOT / "data/extraction_coverage.json").read_text(
    encoding="utf-8"
))
PREFIX = "StreamingAssets/aa/StandaloneWindows64/"
EXPECTED = {
    "npc_assets_all.bundle": (
        "aacec65903186775c8b834ba89cbbc0fea1419d857f14a0d95943732f12a0d69",
        98896651,
    ),
    "tutorial_assets_all.bundle": (
        "56f1993ad49ac265c3268667557b0ec13c1c0f39fb7ada94ae4251e4328ac691",
        84166120,
    ),
}


class PriorityLfsRegistryTests(unittest.TestCase):
    def test_registry_is_exactly_two_original_tracked_sources(self):
        self.assertEqual(len(LEDGER["known_lfs_not_yet_scanned"]), 2)
        for name, (digest, size) in EXPECTED.items():
            item = source_entry(LEDGER, PREFIX + name)
            self.assertEqual(item["lfs_oid_sha256"], digest)
            self.assertEqual(item["size_bytes"], size)
            self.assertEqual(item["bundle"], PREFIX + name)

    def test_unregistered_or_ambiguous_sources_fail(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            source_entry(LEDGER, PREFIX + "unknown_assets_all.bundle")
        with self.assertRaisesRegex(ValueError, "Unrecognized"):
            source_entry(LEDGER, "../../other.bundle")

        item = LEDGER["known_lfs_not_yet_scanned"][0]
        copy = {**LEDGER, "known_lfs_not_yet_scanned": [item, item]}
        with self.assertRaisesRegex(ValueError, "exactly one"):
            source_entry(copy, item["bundle"])

    def test_registry_still_valid_after_successful_source_scan(self):
        item = LEDGER["known_lfs_not_yet_scanned"][0]
        scanned = {**item, "sha256": item["lfs_oid_sha256"]}
        copy = {**LEDGER,
                "known_lfs_not_yet_scanned": LEDGER[
                    "known_lfs_not_yet_scanned"][1:],
                "scans": [*LEDGER["scans"], scanned]}
        self.assertEqual(
            source_entry(copy, item["bundle"])["lfs_oid_sha256"],
            item["lfs_oid_sha256"],
        )
        scanned["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "differs"):
            source_entry(copy, item["bundle"])


class SourceVerificationTests(unittest.TestCase):
    def test_original_pointer_rejects_mismatch_and_nonpointer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.bundle"
            data = b"UnityFSdemo fixture, not a real game file"
            sha = hashlib.sha256(data).hexdigest()
            evidence = {"bundle": path.as_posix(), "lfs_oid_sha256": sha,
                        "size_bytes": len(data)}
            pointer = (f"version https://git-lfs.github.com/spec/v1\n"
                       f"oid sha256:{sha}\nsize {len(data)}\n")
            path.write_text(pointer, encoding="ascii")
            self.assertTrue(verify_source(path, evidence, phase="pointer")[
                "verified"])
            with self.assertRaisesRegex(ValueError, "Expected downloaded"):
                verify_source(path, evidence, phase="bytes")

            path.write_text(pointer.replace(sha, "0" * 64), encoding="ascii")
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_source(path, evidence, phase="pointer")

            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "Expected original"):
                verify_source(path, evidence, phase="pointer")

    def test_downloaded_unityfs_bytes_are_exactly_sha_and_size_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.bundle"
            data = b"UnityFS" + bytes(range(32))
            path.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            evidence = {"bundle": path.as_posix(), "lfs_oid_sha256": digest,
                        "size_bytes": len(data)}
            verified = verify_source(path, evidence, phase="bytes")
            self.assertTrue(verified["verified"])
            self.assertEqual(verified["sha256"], digest)

            with self.assertRaisesRegex(ValueError, "size differs"):
                verify_source(path, {**evidence, "size_bytes": len(data) + 1},
                              phase="bytes")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                verify_source(path, {**evidence, "lfs_oid_sha256": "0" * 64},
                              phase="bytes")
            path.write_bytes(b"wrong content")
            with self.assertRaisesRegex(ValueError, "Expected downloaded"):
                verify_source(path, evidence, phase="bytes")

    def test_wrong_bundle_path_and_phase_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.bundle"
            path.write_bytes(b"UnityFS123")
            evidence = {"bundle": "different.bundle",
                        "lfs_oid_sha256": "0" * 64, "size_bytes": 10}
            with self.assertRaisesRegex(ValueError, "path differs"):
                verify_source(path, evidence, phase="bytes")
            with self.assertRaisesRegex(ValueError, "phase"):
                verify_source(path, evidence, phase="unknown")


if __name__ == "__main__":
    unittest.main()
