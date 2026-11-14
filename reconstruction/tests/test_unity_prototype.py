"""Static Unity project integration checks; does not pretend to compile Unity APIs.

Editor/PlayMode verification is a separate acceptance gate because CI has no
licensed Unity Editor. These tests catch package paths, missing stations and
accidental use of the legacy Input API or game bundles.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNITY = ROOT / "unity-prototype"
SCRIPTS = UNITY / "Assets/Scripts"


def read(name):
    return (SCRIPTS / name).read_text(encoding="utf-8")


class UnityPrototypeStructureTests(unittest.TestCase):
    def test_manifest_and_package_are_single_source_of_truth(self):
        project = json.loads((UNITY / "Packages/manifest.json").read_text(
            encoding="utf-8"
        ))
        packages = project["dependencies"]
        self.assertEqual(packages["com.unity.inputsystem"], "1.20.1")
        # These are opt-in built-in modules; the procedural world uses all three.
        for builtin in ("audio", "physics", "uielements"):
            self.assertEqual(
                packages[f"com.unity.modules.{builtin}"], "1.0.0"
            )
        relative = packages["com.rabron.reconstruction-core"]
        self.assertTrue(relative.startswith("file:"))
        core = (UNITY / "Packages" / relative[5:]).resolve()
        self.assertEqual(core, (ROOT / "game/Core").resolve())
        self.assertTrue((core / "HeistSession.cs").is_file())
        self.assertTrue((core / "package.json").is_file())

        runtime_assembly = json.loads((core / "Rabron.GameCore.asmdef").read_text(
            encoding="utf-8"
        ))
        prototype_assembly = json.loads(
            (SCRIPTS / "Rabron.Prototype.asmdef").read_text(encoding="utf-8")
        )
        self.assertEqual(runtime_assembly["name"], "Rabron.GameCore")
        self.assertIn("Rabron.GameCore", prototype_assembly["references"])
        self.assertIn("Unity.InputSystem", prototype_assembly["references"])
        self.assertEqual((UNITY / "ProjectSettings/ProjectVersion.txt")
                         .read_text(encoding="utf-8").strip(),
                         "m_EditorVersion: 6000.3.18f1")

    def test_every_station_is_implemented_and_placed_in_the_world(self):
        marker = read("InteractionMarker.cs")
        section = marker.split("public enum StationAction", 1)[1].split("}", 1)[0]
        enum_cases = set(re.findall(r"\b[A-Z][A-Za-z0-9]+\b", section))
        enum_cases.discard("StationAction")

        director = read("PrototypeDirector.cs")
        world = read("PrototypeWorld.cs")
        dispatch = set(re.findall(r"case StationAction\.(\w+)", director))
        available = set(re.findall(r"StationAction\.(\w+)\s*=>", director))
        placed = set(re.findall(r"StationAction\.(\w+),\s*\"", world))
        self.assertEqual(enum_cases, dispatch)
        self.assertEqual(enum_cases, available)
        self.assertEqual(enum_cases, placed)
        self.assertEqual(len(enum_cases), 15)

    def test_play_mode_bootstrap_and_editor_scene(self):
        boot = read("PrototypeBoot.cs")
        installer = (UNITY / "Assets/Editor/PrototypeSceneInstaller.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn("RuntimeInitializeLoadType.AfterSceneLoad", boot)
        self.assertIn("AddComponent<PrototypeDirector>()", boot)
        self.assertIn("EditorSceneManager.SaveScene", installer)
        self.assertIn("EditorBuildSettingsScene", installer)
        self.assertIn('PlayerSettings.companyName = "RabronReconstruction"', installer)
        self.assertIn('PlayerSettings.productName = "RabronPrototype"', installer)
        self.assertIn("BuildPipeline.BuildPlayer", installer)
        self.assertIn("BuildTarget.StandaloneWindows64", installer)
        self.assertIn("AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath)", installer)
        self.assertIn('AssetDatabase.CreateFolder("Assets", "Scenes")', installer)
        self.assertIn('Application.dataPath, "..", "Builds"', installer)
        self.assertNotIn('Directory.CreateDirectory("Assets/Scenes")', installer)
        self.assertNotIn('const string output = "Builds/', installer)

    def test_original_game_assets_are_not_embedded(self):
        artifacts = tuple(p for p in UNITY.rglob("*") if p.is_file()
                          and p.suffix.lower() in {
                              ".bundle", ".resS", ".dat", ".dll", ".fbx", ".png",
                          })
        self.assertEqual(artifacts, ())

    def test_actual_editor_validation_is_explicit_and_not_falsely_green(self):
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        runner = (UNITY / "Tools/Verify-Unity.ps1").read_text(
            encoding="utf-8"
        )
        world = read("PrototypeWorld.cs")

        self.assertIn("ValidateProject()", editor)
        self.assertIn("ValidateAndBuildWindows()", editor)
        self.assertIn("PrototypeWorld.Create(", editor)
        self.assertIn("PrototypeSceneInstaller.BuildWindows()", editor)
        self.assertIn("RABRON_UNITY_EDITOR_SMOKE_PASS", editor)
        self.assertIn("RABRON_UNITY_WINDOWS_BUILD_PASS", editor)
        self.assertIn("RabronPrototype.exe", editor)
        self.assertIn("#if !ENABLE_INPUT_SYSTEM", editor)
        self.assertIn("Input System backend is disabled", editor)
        self.assertIn('Application.dataPath, "..", "Builds"', editor)
        self.assertNotIn('Path.GetFullPath("Builds/', editor)
        self.assertIn("UnityEngine.Object.DestroyImmediate(root)", editor)
        self.assertIn("controller.stepOffset = 0.65f", world)
        self.assertIn("Object.DestroyImmediate(bodyCollider)", world)

        self.assertIn("'-executeMethod', $method", runner)
        self.assertIn("'-buildTarget', 'StandaloneWindows64'", runner)
        self.assertIn("$exitCode -ne 0", runner)
        self.assertIn("$logText.Contains($token)", runner)
        self.assertIn("Test-Path -LiteralPath $exe", runner)
        self.assertNotIn("ignorecompilererrors", runner.lower())

    def test_fence_cash_is_physical_but_only_session_credits_money(self):
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        presenter = read("CashPilePresenter.cs")
        smoke = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )

        self.assertIn("out CashPilePresenter cashPile", world)
        self.assertIn('new GameObject("Fence cash waiting on counter")', world)
        self.assertIn("bundle.GetComponent<Collider>().enabled = false", world)
        self.assertIn("cashPile.SetAmount(0);", world)
        self.assertIn("_cashPile.SetAmount(_session.CounterCash)", director)
        self.assertIn("public void SetAmount(long counterCash)", presenter)
        self.assertIn("bool visible = counterCash > 0", presenter)
        self.assertIn("cashPile.SetAmount(200)", smoke)
        self.assertIn("cashPile.SetAmount(0)", smoke)
        self.assertIn("Uncollected cash must be physically visible", smoke)
        self.assertIn("Collected cash must disappear", smoke)
        self.assertNotIn("DirtyCash =", presenter)
        self.assertNotIn("BankBalance =", presenter)

    def test_interactions_and_camera_obey_world_colliders(self):
        director = read("PrototypeDirector.cs")
        motor = read("ThirdPersonMotor.cs")
        query = read("WorldOcclusion.cs")
        smoke = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )

        self.assertIn("distance < best && CanReachStation(marker)", director)
        self.assertIn("WorldOcclusion.HasClearLine(", director)
        self.assertIn("WorldOcclusion.ClampCamera(", motor)
        self.assertIn("Physics.RaycastNonAlloc(", query)
        self.assertIn("Physics.SphereCastNonAlloc(", query)
        self.assertIn("QueryTriggerInteraction.Ignore", query)
        self.assertIn("hit.collider.transform.IsChildOf(ignore)", query)
        self.assertIn("count == hits.Length", query)
        self.assertIn("Physics.SyncTransforms()", smoke)
        self.assertIn("Warehouse wall must block interactions", smoke)
        self.assertIn("Artwork must be interactable from inside", smoke)
        self.assertIn("Cash counter must block collection from its front", smoke)
        self.assertIn("Cash must be reachable from behind the counter", smoke)
        self.assertIn("Follow camera must remain on the near side", smoke)
        self.assertNotIn("Physics.RaycastAll(", query)
        self.assertNotIn("Physics.SphereCastAll(", query)

    def test_guard_raises_alarm_and_staff_control_is_a_gameplay_rule(self):
        sensor = read("GuardSensor.cs")
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        smoke = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8"
        )

        self.assertIn("public void ControlStaff()", core)
        self.assertIn("public bool StaffControlled", core)
        self.assertIn("StaffControlled = false;", core)
        self.assertIn("WorldOcclusion.HasClearLine(", sensor)
        self.assertIn("Vector3.Angle(", sensor)
        self.assertIn("DemoSightRange", sensor)
        self.assertIn("DemoHalfSightAngle", sensor)
        self.assertIn("out GuardSensor guard", world)
        self.assertIn('new GameObject("Warehouse guard")', world)
        self.assertIn("StationAction.ControlStaff", world)
        self.assertIn("_guard.CanSee(_player.transform)", director)
        self.assertIn("_session.RaiseAlarm()", director)
        self.assertIn("_session.ControlStaff()", director)
        self.assertIn("Guard should see a player directly ahead", smoke)
        self.assertIn("Guard should not see a player directly behind", smoke)
        self.assertIn("session.ControlStaff();", smoke)

    def test_local_save_is_versioned_validated_and_written_after_actions(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(encoding="utf-8")
        model = (ROOT / "game/Core/HeistSessionSnapshot.cs").read_text(
            encoding="utf-8"
        )
        director = read("PrototypeDirector.cs")
        store = read("PrototypeSaveStore.cs")
        manifest = json.loads((UNITY / "Packages/manifest.json").read_text(
            encoding="utf-8"
        ))

        self.assertEqual(
            manifest["dependencies"]["com.unity.modules.jsonserialize"], "1.0.0"
        )
        self.assertIn("[Serializable]", model)
        self.assertIn("public const int CurrentVersion = 1;", model)
        self.assertIn("public long LaunderingReadyAt;", model)
        self.assertIn("public string[] LootIds", model)
        self.assertIn("HeistSessionSnapshot ExportSnapshot()", core)
        self.assertIn("static HeistSession FromSnapshot(", core)
        self.assertIn("Enum.IsDefined", core)
        self.assertIn("invalid or duplicate loot", core)
        self.assertIn("Save contains inconsistent heist state", core)
        self.assertIn("JsonUtility.ToJson(session.ExportSnapshot())", store)
        self.assertIn("JsonUtility.FromJson<HeistSessionSnapshot>", store)
        self.assertIn("HeistSession.FromSnapshot(checkpoint)", store)
        self.assertIn("File.Replace(temporary, target, target + \".bak\")", store)
        self.assertIn("Application.persistentDataPath", store)
        self.assertIn("PrototypeSaveStore.Load(out string startupMessage)", director)
        self.assertIn("_cashPile.SetAmount(_session.CounterCash)", director)
        self.assertIn("SaveProgress();", director)
        self.assertIn("OnApplicationQuit()", director)
        self.assertNotIn("JsonUtility", core)
        self.assertNotIn("UnityEngine", core)
        self.assertNotIn("BankBalance =", store)

    def test_controls_and_game_logic_are_not_duplicated(self):
        motor = read("ThirdPersonMotor.cs")
        director = read("PrototypeDirector.cs")
        self.assertIn("UnityEngine.InputSystem", motor)
        self.assertNotRegex(motor, r"\bInput\.Get(?:Key|Axis|Button)")
        self.assertIn("PrototypeSaveStore.Load(out string startupMessage)", director)
        self.assertIn("_session.SellLoot(", director)
        self.assertIn("_session.CollectCounterCash()", director)
        self.assertIn("_session.StartLaundering(", director)
        self.assertIn("_session.DepositCleanCash(", director)
        self.assertIn("GameObject.CreatePrimitive", read("PrototypeWorld.cs"))


if __name__ == "__main__":
    unittest.main()
