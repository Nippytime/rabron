"""Fixture tests for the reproducible, read-only build auditor."""

import json
import tempfile
import unittest
from pathlib import Path

from reconstruction.tools.audit_build import audit


class BuildAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "StreamingAssets/aa/AddressablesLink").mkdir(parents=True)
        (self.root / "StreamingAssets/aa/StandaloneWindows64").mkdir(parents=True)
        (self.root / "il2cpp_data/Metadata").mkdir(parents=True)
        (self.root / "reconstruction").mkdir()
        (self.root / ".git").mkdir()
        (self.root / "ScriptingAssemblies.json").write_text(
            json.dumps({"names": ["Battle.dll", "Models.dll", "Other.dll"]}),
            encoding="utf-8",
        )
        (self.root / "RuntimeInitializeOnLoads.json").write_text(
            json.dumps({"root": [{"className": "X", "methodName": "Init"}]}),
            encoding="utf-8",
        )
        (self.root / "StreamingAssets/aa/AddressablesLink/link.xml").write_text(
            '<linker><assembly fullname="Battle">'
            '<type fullname="Game.Battle.GrandHeist.GrandHeistViewDescription"/>'
            '<type fullname="Game.Battle.Entities.Plot.Dialog.MoneyLaunderingDialogView"/>'
            '<type fullname="Example.UnrelatedClass"/>'
            '</assembly></linker>',
            encoding="utf-8",
        )
        (self.root / "StreamingAssets/aa/StandaloneWindows64/"
                     "location-city_scenes_all.bundle").write_bytes(b"scene")
        (self.root / "StreamingAssets/aa/StandaloneWindows64/"
                     "weapon-test_assets_all.bundle").write_bytes(b"asset")
        (self.root / "il2cpp_data/Metadata/global-metadata.dat").write_bytes(b"meta")
        (self.root / "app.info").write_text("Kefir\nROB RUN\n", encoding="utf-8")
        (self.root / "reconstruction/ignore.bundle").write_bytes(b"artifact")
        (self.root / ".git/objects.bundle").write_bytes(b"artifact")

    def test_counts_types_and_bundles(self):
        result = audit(self.root)
        self.assertTrue(result["evidence_only"])
        self.assertEqual(result["game"], ["Kefir", "ROB RUN"])
        self.assertEqual(result["bundles"], 2)
        self.assertEqual(result["bundle_groups"], {"location": 1, "weapon": 1})
        self.assertEqual(result["raw_files"], 7)
        self.assertEqual(result["runtime_initializer_count"], 1)
        self.assertEqual(result["scripting_assemblies"]["count"], 3)
        self.assertEqual(result["scripting_assemblies"]["gameplay_modules"],
                         ["Battle.dll", "Models.dll"])
        self.assertEqual(result["addressables_referenced_type_count"], 3)
        self.assertEqual(result["systems"]["heists"]["count"], 1)
        self.assertEqual(result["systems"]["money_laundering"]["count"], 1)
        self.assertEqual(result["systems"]["vehicles"]["count"], 0)
        self.assertEqual(result["scene_bundles"], [
            "StreamingAssets/aa/StandaloneWindows64/location-city_scenes_all.bundle"
        ])

    def test_binary_presence_is_reported_without_decompilation(self):
        result = audit(self.root)
        self.assertTrue(result["il2cpp_metadata"]["present"])
        self.assertEqual(result["il2cpp_metadata"]["size_on_disk"], 4)
        self.assertFalse(result["game_assembly_binary_present"])

    def test_output_is_stable(self):
        first = audit(self.root)
        second = audit(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["raw_file_bytes_on_disk"],
                         sum(p.stat().st_size for p in self.root.rglob("*")
                             if p.is_file()
                             and p.relative_to(self.root).parts[0]
                             not in {".git", ".github", "reconstruction"}))


if __name__ == "__main__":
    unittest.main()
