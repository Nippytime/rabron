"""Behavior and evidence tests for per-bundle numeric field categorization."""

import unittest

from reconstruction.tools.summarize_numeric_evidence import (
    classify_asset, classify_field, summarize,
)


class FieldClassifierTests(unittest.TestCase):
    def test_references_localization_and_curves_do_not_become_gameplay_values(self):
        ignored = (
            "$.m_Script.m_PathID",
            "$.<Coin>k__BackingField.m_TableEntryReference.m_KeyId",
            "$.<Cash>k__BackingField.idInternal",
            "$.<Weapon>k__BackingField.m_Curve[1].value",
            "$.<Tax>k__BackingField._localizedString.m_FallbackState",
            "$.references.version",
        )
        for path in ignored:
            with self.subTest(path=path):
                self.assertIsNone(classify_field(path))

    def test_interprets_only_actual_scalar_path(self):
        self.assertEqual(classify_field("$.<TaxRate>k__BackingField"), "economy")
        self.assertEqual(classify_field("$.HealthDamage"), "combat")
        self.assertEqual(classify_field("$.SkillLevel"), "progression")
        self.assertEqual(classify_field("$.Speed"), "timing_and_world")
        self.assertIsNone(classify_field("$.m_Enabled"))

    def test_asset_kind_is_not_evidence_of_server_ownership(self):
        self.assertEqual(classify_asset("MoneyWorkbenchViewDescription"),
                         "client_presentation")
        self.assertEqual(classify_asset("WeaponViewConfiguration"),
                         "client_configuration")
        self.assertEqual(classify_asset("CarStatsPreset"), "client_configuration")
        self.assertEqual(classify_asset("GenericScriptableObject"), "unclassified")


class SummaryTests(unittest.TestCase):
    def manifest(self):
        return {
            "source": "StreamingAssets/aa/sample.bundle",
            "sha256": "a" * 64,
            "objects_by_type": {"MonoBehaviour": 2},
            "monobehaviours_total": 2,
            "monobehaviours_attempted": 2,
            "monobehaviours_parsed": 2,
            "complete_numeric_extraction": False,
            "records": [
                {
                    "path_id": "-1",
                    "name": "CashViewDescription",
                    "fields_truncated": True,
                    "numeric_fields": [
                        {"path": "$.UserTaxRate", "value": 0.2},
                        {"path": "$.m_Script.m_PathID", "value": 12345},
                        {"path": "$.AmmoDamage", "value": 9},
                    ],
                },
                {
                    "path_id": "-2",
                    "name": "WorldSettings",
                    "fields_truncated": False,
                    "numeric_fields": [
                        {"path": "$.UserTaxRate", "value": 0.5},
                        {"path": "$.MoveSpeed", "value": 7},
                    ],
                },
            ],
        }

    def test_summary_is_deterministic_and_provenance_is_preserved(self):
        summary = summarize(self.manifest(), samples_per_category=5)
        self.assertEqual(summary, summarize(self.manifest(), samples_per_category=5))
        self.assertEqual(summary["source_sha256"], "a" * 64)
        self.assertFalse(summary["complete_numeric_extraction"])
        self.assertEqual(summary["records_with_truncated_numeric_fields"], 1)
        self.assertEqual(summary["asset_category_counts"], {
            "client_configuration": 1,
            "client_presentation": 1,
        })
        group = summary["candidate_field_groups"]["economy"]
        self.assertEqual(group["matching_numeric_fields"], 2)
        self.assertEqual(group["examples"][0], {
            "asset": "WorldSettings",
            "asset_kind": "client_configuration",
            "path_id": "-2",
            "field": "$.UserTaxRate",
            "value": 0.5,
        })
        self.assertEqual(summary["candidate_field_groups"]["combat"]
                         ["matching_numeric_fields"], 1)
        self.assertEqual(summary["candidate_field_groups"]["timing_and_world"]
                         ["matching_numeric_fields"], 1)

    def test_zero_sample_limit_still_preserves_candidate_counts(self):
        summary = summarize(self.manifest(), samples_per_category=0)
        group = summary["candidate_field_groups"]["economy"]
        self.assertEqual(group["matching_numeric_fields"], 2)
        self.assertEqual(group["examples"], [])
        with self.assertRaises(ValueError):
            summarize(self.manifest(), samples_per_category=-1)

    def test_missing_required_provenance_rejected(self):
        manifest = self.manifest()
        del manifest["sha256"]
        with self.assertRaisesRegex(ValueError, "missing sha256"):
            summarize(manifest)


if __name__ == "__main__":
    unittest.main()
