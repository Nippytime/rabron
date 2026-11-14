"""Validate a small, bounded, source-anchored gameplay bundle extraction matrix."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / ".github/workflows/extract-gameplay-bundles.yml"

BUNDLES = (
    "vehicle-cars_assets_all.bundle",
    "equipement_assets_usableitem.bundle",
    "shared-environment-plot_assets_all.bundle",
    "vehicles-helicopters_assets_all.bundle",
    "weapon-vulture50_assets_all.bundle",
    "location-settlement-standalone_scenes_settlement_standalone.bundle",
)


class GameplayBundleBatchTests(unittest.TestCase):
    def test_explicit_six_asset_batch_is_bounded_and_source_anchored(self):
        source = FLOW.read_text(encoding="utf-8")
        for name in BUNDLES:
            self.assertIn("          - " + name, source)
        self.assertEqual(source.count("          - "), len(BUNDLES))
        self.assertIn("max-parallel: 3", source)
        self.assertIn("timeout-minutes: 20", source)
        self.assertIn("filter: blob:none", source)
        self.assertIn("lfs: false", source)
        self.assertIn("StreamingAssets/aa/StandaloneWindows64/$" +
                      "{{ matrix.bundle }}", source)
        self.assertIn("UnityPy==1.25.4", source)
        self.assertIn("--max-fields 8192 --max-depth 32", source)
        self.assertIn("extract_unity_bundle.py", source)
        self.assertIn("summarize_numeric_evidence.py", source)
        self.assertIn("upload-artifact@v4", source)
        self.assertIn("retention-days: 30", source)
        self.assertIn("if-no-files-found: warn", source)
        self.assertNotIn("GameAssembly.dll", source)
        self.assertNotIn("git lfs pull", source)
        self.assertNotIn("ignorecompilererrors", source)


if __name__ == "__main__":
    unittest.main()
