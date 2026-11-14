"""Validate observed visual intervals without inferring laundering formulas."""

import json
import unittest
from pathlib import Path


DATA = (Path(__file__).resolve().parents[1] /
        "data/settlement_cash_pile_thresholds.json")


class SettlementThresholdEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_provenance_and_qualifications(self):
        self.assertEqual(self.data["source_sha256"],
                         "43018ce5ec95c4dfdd433b71d1460ada17cf4dbd79d8abbd70c2bf00b5c83534")
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(self.data["classification"],
                         "client_presentation_not_authoritative_economy")
        self.assertEqual(len(self.data["records"]), 3)
        self.assertTrue(all("MoneyWorkbenchCashPileSizeIntervals" in
                            r["field"] for r in self.data["records"]))

    def test_exact_source_values_and_no_inferred_rates(self):
        base = [0, 1, 1000, 5000, 10000, 25000, 50000, 100000, 250000,
                500000, 1000000]
        cases = {
            "-3521504050020868324": base + [2000000, 5000000, 15000000,
                                              30000000, 50000000],
            "1509660387188884686": base,
            "5308116492309360796": base + [2000000, 5000000, 15000000],
        }
        self.assertEqual({record["path_id"]: record["thresholds"] for record
                          in self.data["records"]}, cases)
        for values in cases.values():
            self.assertEqual(values, sorted(set(values)))
        for forbidden in ("laundering_rate", "cash_to_clean_conversion",
                          "bribe_price", "tax_rate"):
            self.assertNotIn(forbidden, self.data)


if __name__ == "__main__":
    unittest.main()
