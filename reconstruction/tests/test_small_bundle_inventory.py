"""W1-F source conservation and fail-closed small-bundle batch regression tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reconstruction.tools.small_bundle_inventory import (
    BUNDLE_PREFIX, MAX_SIZE, MIN_SIZE, consolidate, inspect_source,
    make_plan, parse_tree_response, run_batch, selected_batch, verify_bytes,
)


def path(name):
    return BUNDLE_PREFIX + name + ".bundle"


def entry(name, size=2048, sha="a" * 40):
    return {"bundle": path(name), "git_blob_sha": sha,
            "git_blob_size": size}


class SmallBundleInventoryTests(unittest.TestCase):
    def setUp(self):
        self.ledger = {"schema_version": 1, "scans": [],
                       "known_lfs_not_yet_scanned": []}

    def test_git_api_tree_ignores_catalog_and_rejects_unsafe_truncated_data(self):
        sha = "b" * 40

        def item(p, *, size=2048):
            return {"path": p, "mode": "100644", "type": "blob",
                    "sha": "a" * 40, "size": size}

        def parse(items, **overrides):
            payload = {"sha": sha, "truncated": False, "tree": items}
            payload.update(overrides)
            return parse_tree_response(payload, expected_sha=sha)

        listed = parse([
            item(path("location-test")),
            item(BUNDLE_PREFIX + "catalog_1.bin"),
            item(BUNDLE_PREFIX + "catalog_1.hash"),
        ])
        self.assertEqual(listed[path("location-test")]["git_blob_size"], 2048)
        self.assertEqual(len(listed), 1)
        self.assertIn(path("localization-english(en-us)"),
                      parse([item(path("localization-english(en-us)"))]))
        for invalid in (path("../escape"), path("invalid name")):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse([item(invalid)])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            parse([item(path("same")), item(path("same"))])
        for bad in (
            {"truncated": True}, {"sha": "c" * 40},
            {"tree": None}, {"tree": [item(path("x"), size=-1)]},
            {"tree": [item(path("x"), size=True)]},
            {"tree": [{"path": None}]},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse([item(path("safe"))], **bad)

    def test_dynamic_selection_reconciles_scans_sizes_lfs_and_batches(self):
        existing = entry("already-scanned", 2048)
        self.ledger["scans"] = [{
            "bundle": existing["bundle"], "sha256": "b" * 64,
            "monobehaviours_total": 0, "monobehaviours_parsed": 0,
            "numeric_field_cap_records": 0, "scan_evidence": "test",
        }]
        candidates = [entry("part-%02d" % i) for i in range(21)]
        data = {
            e["bundle"]: e for e in [
                existing, entry("lfs-pointer", 133),
                entry("small-under", MIN_SIZE - 1),
                entry("medium-over", MAX_SIZE + 1), *candidates,
            ]
        }
        plan = make_plan(data, self.ledger, expected_tracked=len(data))
        self.assertEqual(plan["documented_scans_before"], 1)
        self.assertEqual(plan["eligible_small_sources"], 21)
        self.assertEqual([len(x["sources"]) for x in plan["batches"]], [20, 1])
        self.assertEqual(len(set(
            y["bundle"] for group in plan["batches"] for y in group["sources"]
        )), 21)
        self.assertEqual(selected_batch(plan, 1)[0]["bundle"], candidates[-1]["bundle"])
        with self.assertRaises(ValueError):
            make_plan(data, self.ledger, batch_size=21, expected_tracked=len(data))
        with self.assertRaises(ValueError):
            make_plan(data, self.ledger, expected_tracked=len(data) + 1)

    def test_batch_rejects_unsafe_paths_duplicate_ids_and_sizes(self):
        plan = make_plan({path("ok"): entry("ok")}, self.ledger, expected_tracked=1)
        self.assertEqual(len(selected_batch(plan, 0)), 1)
        plan["batches"][0]["sources"].append(entry("ok"))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            selected_batch(plan, 0)
        plan["batches"][0]["sources"] = [entry("bad", size=0)]
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            selected_batch(plan, 0)
        plan["batches"][0]["sources"] = [entry("ok")]
        plan["batches"][0]["id"] = 5
        with self.assertRaisesRegex(ValueError, "non-contiguous"):
            selected_batch(plan, 5)

    def test_source_bytes_must_match_exact_size_magic_and_git_blob(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "test.bundle"
            data = b"UnityFS" + b"\0" * 2048
            source.write_bytes(data)
            blob = hashlib.sha1(
                b"blob " + str(len(data)).encode() + b"\0" + data
            ).hexdigest()
            item = {"git_blob_size": len(data), "git_blob_sha": blob}
            self.assertEqual(verify_bytes(source, item),
                             hashlib.sha256(data).hexdigest())
            with self.assertRaisesRegex(ValueError, "size"):
                verify_bytes(source, {**item, "git_blob_size": len(data) + 1})
            with self.assertRaisesRegex(ValueError, "SHA-1"):
                verify_bytes(source, {**item, "git_blob_sha": "0" * 40})
            source.write_bytes(b"version https://git-lfs.github.com/spec/v1")
            with self.assertRaises(ValueError):
                verify_bytes(source, item)
            source.unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                verify_bytes(source, item)

    def test_zero_behaviour_and_truncated_source_remain_truthful(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "batch-00.json"
            zero = {**entry("zero"), "sha256": "b" * 64,
                    "source_status": "bounded_mono_numeric_complete",
                    "monobehaviours_total": 0, "monobehaviours_parsed": 0,
                    "unparsed_records": 0, "numeric_field_cap_records": 0,
                    "bounded_numeric_scan_complete": True,
                    "numeric_field_limit": 2048, "numeric_depth_limit": 32,
                    "path_ids": [], "objects_by_type": {"Sprite": 1},
                    "candidate_field_counts": {"economy": 0}}
            capped = {**entry("capped"), "sha256": "c" * 64,
                      "source_status": "partial_mono_numeric",
                      "monobehaviours_total": 1, "monobehaviours_parsed": 1,
                      "unparsed_records": 0, "numeric_field_cap_records": 1,
                      "bounded_numeric_scan_complete": False,
                      "numeric_field_limit": 2048, "numeric_depth_limit": 32,
                      "path_ids": [{"id": "12", "status": "parsed",
                                    "truncation": ["field_limit"]}],
                      "objects_by_type": {"MonoBehaviour": 1},
                      "candidate_field_counts": {"economy": 2}}
            plan = make_plan({x["bundle"]: x for x in (zero, capped)},
                             self.ledger, expected_tracked=2)
            # Consolidation must accept real zeros without inventing numeric data.
            group = [next(e for e in (zero, capped) if e["bundle"] == x["bundle"])
                     for x in plan["batches"][0]["sources"]]
            output.write_text(json.dumps({
                "schema_version": 1, "batch_id": 0, "sources": group,
            }))
            report, proposal = consolidate(plan, Path(folder), self.ledger,
                                           run_url="https://github.com/Nippytime/rabron/actions/runs/1")
            self.assertEqual(report["new_documented"], 2)
            self.assertEqual(report["unscanned_after"], 0)
            self.assertEqual(proposal["scans"][0]["monobehaviours_total"], 1
                             if group[0]["bundle"] == capped["bundle"] else 0)
            self.assertTrue(any(e["numeric_field_cap_records"] == 1
                                for e in proposal["scans"]))
            # Committing measured evidence must not create an empty green
            # matrix: next run rechecks exact original bytes and identities.
            recheck = make_plan(
                {e["bundle"]: e for e in (zero, capped)},
                proposal, expected_tracked=2,
            )
            self.assertEqual(recheck["mode"], "recheck")
            self.assertEqual(recheck["eligible_small_sources"], 0)
            self.assertEqual(recheck["recheck_documented_sources"], 2)
            second, preserved = consolidate(
                recheck, Path(folder), proposal, run_url="new-run",
            )
            self.assertEqual(second["new_documented"], 0)
            self.assertEqual(second["source_reverified"], 2)
            self.assertEqual(preserved, proposal)
            altered = [dict(row) for row in group]
            altered[0]["sha256"] = "f" * 64
            output.write_text(json.dumps({
                "batch_id": 0, "sources": altered,
            }))
            with self.assertRaisesRegex(ValueError, "evidence drift"):
                consolidate(recheck, Path(folder), proposal, run_url="new-run")
            group.pop()
            output.write_text(json.dumps({"batch_id": 0, "sources": group}))
            with self.assertRaisesRegex(ValueError, "Missing"):
                consolidate(plan, Path(folder), self.ledger, run_url="test")

    def test_unparseable_source_is_not_promoted_to_zero_behaviours(self):
        bad = {**entry("unparseable"), "sha256": "d" * 64,
               "source_status": "unparseable", "parse_error_type": "TypeTreeError",
               "monobehaviours_total": None, "monobehaviours_parsed": None,
               "numeric_field_cap_records": None}
        plan = make_plan({bad["bundle"]: bad}, self.ledger, expected_tracked=1)
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "batch-00.json").write_text(json.dumps({
                "batch_id": 0, "sources": [bad],
            }))
            report, proposal = consolidate(plan, Path(folder), self.ledger,
                                           run_url="test")
            self.assertEqual(report["new_documented"], 0)
            self.assertEqual(report["unscanned_after"], 1)
            self.assertEqual(len(proposal["scans"]), 0)
            self.assertEqual(report["unparseable_attempts"][0]["error"],
                             "TypeTreeError")

    def test_valid_scan_with_inconsistent_accounting_fails_ci(self):
        item = entry("verified")
        with patch("reconstruction.tools.small_bundle_inventory.verify_bytes",
                   return_value="a" * 64), patch(
                "reconstruction.tools.small_bundle_inventory.scan_bundle",
                return_value={"tool_version": "1.25.4"}), patch(
                "reconstruction.tools.small_bundle_inventory.summarize",
                return_value={}), patch(
                "reconstruction.tools.small_bundle_inventory.validate",
                side_effect=ValueError("MonoBehaviour counts do not reconcile")):
            with self.assertRaisesRegex(ValueError, "counts do not reconcile"):
                inspect_source(item)

    def test_unparseable_actual_bundle_keeps_error_type_without_zero_counts(self):
        item = entry("schema-missing")
        with patch("reconstruction.tools.small_bundle_inventory.verify_bytes",
                   return_value="a" * 64), patch(
                "reconstruction.tools.small_bundle_inventory.scan_bundle",
                side_effect=ValueError("Unknown Unity schema")):
            result = inspect_source(item)
        self.assertEqual(result["source_status"], "unparseable")
        self.assertEqual(result["parse_error_type"], "ValueError")
        self.assertIsNone(result["monobehaviours_total"])

    def test_batch_worker_persists_results_but_never_swallows_missing_source(self):
        plan = make_plan({path("one"): entry("one")}, self.ledger,
                         expected_tracked=1)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "batch-00.json"
            with patch("reconstruction.tools.small_bundle_inventory.inspect_source",
                       return_value={"source_status": "partial_mono_numeric"}):
                results = run_batch(plan, 0, target)
            self.assertEqual(len(results), 1)
            self.assertTrue(target.is_file())
            with patch("reconstruction.tools.small_bundle_inventory.inspect_source",
                       side_effect=ValueError("Missing original source")):
                with self.assertRaisesRegex(ValueError, "Missing"):
                    run_batch(plan, 0, target)


if __name__ == "__main__":
    unittest.main()
