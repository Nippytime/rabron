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
        self.assertEqual(len(enum_cases), 19)

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

    def test_real_playmode_discovers_inactive_counter_cash(self):
        world = read("PrototypeWorld.cs")
        presenter = read("CashPilePresenter.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")

        # A zero balance deactivates the actor; it must remain discoverable
        # in the real Play Mode test without enabling it artificially.
        self.assertIn("cashPile.SetAmount(0);", world)
        self.assertIn("gameObject.SetActive(visible);", presenter)
        self.assertIn("FindObjectsByType<CashPilePresenter>(", playmode)
        self.assertIn("FindObjectsInactive.Include, FindObjectsSortMode.None", playmode)
        self.assertIn("presenters.Length, Is.EqualTo(1)", playmode)
        self.assertIn("return presenters[0];", playmode)
        self.assertEqual(playmode.count("var cash = FindCashPresenter();"), 2)
        self.assertNotIn("FindFirstObjectByType<CashPilePresenter>()", playmode)
        self.assertIn("cash.IsVisible, Is.EqualTo(saved.CounterCash > 0L)", playmode)
        self.assertIn("cash.SetAmount(0);", playmode)
        self.assertIn("FindCashPresenter(), Is.SameAs(cash)", playmode)
        self.assertIn("cash.IsVisible, Is.True", playmode)
        self.assertIn("cash.IsVisible, Is.False", playmode)

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
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
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
        self.assertIn("JsonUtility.ToJson(session.ExportSnapshot())", editor)
        self.assertIn("HeistSession.FromSnapshot(JsonUtility.FromJson", editor)
        self.assertIn("File.Replace(temporary, target, target + \".bak\")", store)
        self.assertIn("Application.persistentDataPath", store)
        self.assertIn("PrototypeSaveStore.Load(out string startupMessage)", director)
        self.assertIn("_cashPile.SetAmount(_session.CounterCash)", director)
        self.assertIn("SaveProgress();", director)
        self.assertIn("OnApplicationQuit()", director)
        self.assertNotIn("JsonUtility", core)
        self.assertNotIn("UnityEngine", core)
        self.assertNotIn("BankBalance =", store)

    def test_real_playmode_suite_requires_nunit_results_not_source_only(self):
        manifest = json.loads((UNITY / "Packages/manifest.json").read_text(
            encoding="utf-8"
        ))["dependencies"]
        asmdef = json.loads((UNITY / "Assets/Tests/PlayMode/"
                             "Rabron.Prototype.PlayModeTests.asmdef").read_text(
                                 encoding="utf-8"
                             ))
        tests = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        runner = (UNITY / "Tools/Verify-PlayMode.ps1").read_text(
            encoding="utf-8"
        )
        validator = (UNITY / "Tools/Assert-PlayModeResults.ps1").read_text(
            encoding="utf-8"
        )
        validator_tests = (UNITY / "Tools/Test-PlayModeResults.ps1").read_text(
            encoding="utf-8"
        )
        save = read("PrototypeSaveStore.cs")

        self.assertEqual(manifest["com.unity.test-framework"], "1.6.0")
        self.assertEqual(asmdef["name"], "Rabron.Prototype.PlayModeTests")
        self.assertIn("Rabron.Prototype", asmdef["references"])
        self.assertIn("Rabron.GameCore", asmdef["references"])
        self.assertIn("UnityEngine.TestRunner", asmdef["references"])
        self.assertIn("UnityEditor.TestRunner", asmdef["references"])
        self.assertEqual(asmdef["includePlatforms"], ["Editor"])
        self.assertIn("nunit.framework.dll", asmdef["precompiledReferences"])
        self.assertIn("TestAssemblies", asmdef["optionalUnityReferences"])

        self.assertIn('[Category("RabronPlayMode")]', tests)
        self.assertEqual(tests.count("[UnityTest]"), 2)
        self.assertIn("SceneBootCreatesRuntimePlayerCameraHudAndStations", tests)
        self.assertIn("HeistMarkersDriveFullLoopAndPhysicalCounterMoney", tests)
        self.assertIn("FindFirstObjectByType<PrototypeDirector>()", tests)
        self.assertIn("Perform", tests)
        self.assertIn("StationAction.CollectCash", tests)
        self.assertIn("StationAction.Deposit", tests)
        self.assertIn("Is.EqualTo(HeistPhase.Idle)", tests)
        self.assertIn("field.SetValue(director, original)", tests)
        self.assertIn("Is.EqualTo(19)", tests)

        self.assertIn("'-runTests'", runner)
        self.assertIn("'-testPlatform', 'PlayMode'", runner)
        self.assertIn("'-testCategory', 'RabronPlayMode'", runner)
        self.assertIn("'-testResults', $results", runner)
        self.assertIn("Assert-PlayModeResults.ps1", runner)
        self.assertIn("-ResultsPath $results -UnityExitCode $exitCode", runner)
        self.assertIn("SelectSingleNode('/test-run')", validator)
        self.assertIn("$total -lt $expected.Count", validator)
        self.assertIn("$failed -ne 0", validator)
        self.assertIn("$missing.Count -gt 0", validator)
        self.assertIn("$duplicates.Count -gt 0", validator)
        self.assertIn("$UnityExitCode -ne 0", validator)
        self.assertIn("Assert-Accepted", validator_tests)
        self.assertIn("Assert-Rejected", validator_tests)
        self.assertIn("zero-test run", validator_tests)
        self.assertIn("duplicate expected case", validator_tests)
        self.assertIn("malformed NUnit XML", validator_tests)
        self.assertNotIn("'-quit'", runner)
        self.assertIn('arg, "-runTests"', save)
        self.assertIn("Application.temporaryCachePath", save)
        self.assertIn("Application.persistentDataPath", save)

    def test_lawful_courier_has_one_core_faucet_and_restorable_markers(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(encoding="utf-8")
        snapshot = (ROOT / "game/Core/HeistSessionSnapshot.cs").read_text(
            encoding="utf-8")
        director = read("PrototypeDirector.cs")
        world = read("PrototypeWorld.cs")
        balance = read("PrototypeBalance.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")

        self.assertIn("public bool CarryingCourierParcel;", snapshot)
        self.assertIn("public void PickUpCourierParcel()", core)
        self.assertIn("public void DeliverCourierParcel(long verifiedCleanPayout)", core)
        self.assertIn("long next = checked(CleanCash + verifiedCleanPayout);", core)
        self.assertIn("CarryingCourierParcel = false;", core)
        self.assertIn("snapshot.CarryingCourierParcel", core)
        self.assertIn("StationAction.CourierPickup", world)
        self.assertIn("StationAction.CourierDropoff", world)
        self.assertIn("new List<InteractionMarker>(19)", world)
        self.assertIn("_session.PickUpCourierParcel()", director)
        self.assertIn("_session.DeliverCourierParcel(_balance.CourierReward)", director)
        self.assertIn("public int CourierReward = 35", balance)
        self.assertIn("courier.PickUpCourierParcel();", editor)
        self.assertIn("JsonUtility.ToJson(courier.ExportSnapshot())", editor)
        self.assertIn("Interact(StationAction.CourierPickup)", playmode)
        self.assertIn("Interact(StationAction.CourierDropoff)", playmode)
        self.assertIn("Interact(StationAction.CourierCancel)", playmode)
        self.assertIn("Interact(StationAction.Deposit)", playmode)
        self.assertNotIn("CleanCash =", director)
        self.assertNotIn("BankBalance =", director)

    def test_courier_recovery_has_physical_feedback_and_no_duplicate_faucet(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8")
        presenter = read("CourierParcelPresenter.cs")
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        hud = read("PrototypeHud.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")

        self.assertIn("public void CancelCourierParcel()", core)
        self.assertIn("CarryingCourierParcel = false;", core)
        self.assertIn("CourierCancel", read("InteractionMarker.cs"))
        self.assertIn("StationAction.CourierCancel", world)
        self.assertIn("_session.CancelCourierParcel()", director)
        self.assertIn("GetComponentInChildren<CourierParcelPresenter>(true)", director)
        self.assertEqual(director.count(
            "_courierParcel.SetCarrying(_session.CarryingCourierParcel);"), 2)
        self.assertIn("Courier: ", hud)
        self.assertIn("state.CarryingCourierParcel", hud)
        self.assertIn("parcel.GetComponent<Collider>().enabled = false;", world)
        self.assertIn('parcel.name = "Carried courier parcel (visual only)"', world)
        self.assertIn("parcel.AddComponent<CourierParcelPresenter>()", world)
        self.assertIn("public void SetCarrying(bool carrying)", presenter)
        self.assertNotIn("CleanCash", presenter)
        self.assertNotIn("BankBalance", presenter)
        self.assertNotIn("PickUpCourierParcel()", presenter)
        self.assertIn("parcel.SetCarrying(true);", editor)
        self.assertIn("courier.CancelCourierParcel();", editor)
        self.assertIn("Interact(StationAction.CourierCancel)", playmode)
        self.assertIn("parcel.IsVisible, Is.True", playmode)
        self.assertIn("parcel.IsVisible, Is.False", playmode)

    def test_grounded_jump_preserves_interact_and_handles_ceiling(self):
        motor = read("ThirdPersonMotor.cs")
        hud = read("PrototypeHud.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertEqual(motor.count('new InputAction("Jump"'), 1)
        self.assertIn('_jump.AddBinding("<Keyboard>/space")', motor)
        self.assertIn('_jump.AddBinding("<Gamepad>/buttonNorth")', motor)
        self.assertIn('_interact.AddBinding("<Gamepad>/buttonSouth")', motor)
        for action in ("Enable", "Disable", "Dispose"):
            self.assertIn(f"_jump?.{action}();", motor)
        self.assertIn("_character.isGrounded, _jump.WasPressedThisFrame()", motor)
        self.assertIn("private static float IntegrateVertical(", motor)
        self.assertIn("if (grounded)", motor)
        self.assertIn("jumpPressed ? Mathf.Sqrt(2f * DemoGravity * DemoJumpHeight)", motor)
        self.assertIn("DemoGravity * deltaSeconds", motor)
        self.assertIn("CollisionFlags collision = _character.Move(", motor)
        self.assertIn("ResolveCeiling(_verticalVelocity, collision)", motor)
        self.assertIn("(collision & CollisionFlags.Above) != 0", motor)
        self.assertIn("_verticalVelocity = 0f;", motor)  # Warp resets velocity.
        self.assertNotRegex(motor, r"\bInput\.Get(?:Button|Key|Axis)")
        self.assertIn("Space / Y: jump", hud)
        self.assertIn("Jump (grounded only)", guide)
        self.assertIn("IntegrateVertical", editor)
        self.assertIn("CollisionFlags.Above", editor)
        self.assertIn('jump.enabled, Is.True', playmode)
        self.assertIn('"<Keyboard>/space"', playmode)
        self.assertIn('"<Gamepad>/buttonNorth"', playmode)
        self.assertIn('"No airborne double-jump"', playmode)
        self.assertIn('"Ceiling collision must cancel ascent"', playmode)

    def test_real_unity_acceptance_evidence_is_fail_closed_and_git_bound(self):
        runner = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
            encoding="utf-8")
        fixture = (UNITY / "Tools/Test-AcceptanceGate.ps1").read_text(
            encoding="utf-8")
        workflow = (ROOT.parent / ".github/workflows/reconstruction-tests.yml").read_text(
            encoding="utf-8")

        # First require actual Windows Unity; never fill in a fake pass for CI.
        self.assertIn("[PlatformID]::Win32NT", runner)
        self.assertIn("Unity Editor missing:", runner)
        self.assertIn("rev-parse --verify HEAD", runner)
        self.assertIn("status --porcelain --untracked-files=no -- reconstruction", runner)
        self.assertIn("Tracked reconstruction source is dirty", runner)
        self.assertIn("Unity modified tracked reconstruction files", runner)
        self.assertIn("Remove-Item -LiteralPath $EvidencePath -Force", runner)

        # Three genuine existing validators, strictly ordered and sequential.
        first = runner.index("'Verify-Unity.ps1') -EditorPath $EditorPath\n")
        second = runner.index("'Verify-PlayMode.ps1') -EditorPath $EditorPath\n")
        third = runner.index(
            "'Verify-Unity.ps1') -EditorPath $EditorPath -BuildWindows")
        manifest = runner.index("Move-Item -LiteralPath $temp -Destination $EvidencePath")
        self.assertLess(first, second)
        self.assertLess(second, third)
        self.assertLess(third, manifest)
        for name in ("editor_smoke_log", "playmode_nunit_xml", "playmode_editor_log",
                     "windows_build_log", "windows_executable", "git_revision",
                     "playmode_passed", "sha256", "schema_version"):
            self.assertIn(name, runner)
        self.assertIn("manual_playthrough_verified = $false", runner)
        self.assertIn("Windows executable was not regenerated", runner)
        self.assertIn("data directory is absent or empty", runner)

        # A negative test can run in hosted CI without a Unity license.
        self.assertIn("'nonexistent-unity-editor.exe'", fixture)
        self.assertIn("Stale green Unity acceptance evidence survived", fixture)
        self.assertIn("Test-AcceptanceGate.ps1", workflow)
        self.assertIn("Verify-Acceptance.ps1", workflow)

    def test_guard_alarm_has_confiscation_custody_and_recoverable_release(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8")
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        marker = read("InteractionMarker.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("Laundered, Arrested", core)
        self.assertIn("public void ArrestAfterAlarm()", core)
        self.assertIn("public void ReleaseFromCustody()", core)
        self.assertIn("_loot.Clear();", core)
        self.assertIn("DirtyCash = 0;", core)
        self.assertIn("Phase = HeistPhase.Arrested;", core)
        self.assertIn("snapshot.Phase == HeistPhase.Arrested", core)
        self.assertIn("unreachable arrest state", core)
        self.assertIn("Phase != HeistPhase.Arrested", core)
        self.assertIn("ReleaseCustody", marker)
        self.assertIn("StationAction.ReleaseCustody", world)
        self.assertIn('new List<InteractionMarker>(19)', world)
        self.assertIn("_session.ArrestAfterAlarm();", director)
        self.assertIn("_session.ReleaseFromCustody();", director)
        self.assertIn("_guard.CanSee(_player.transform)", director)
        self.assertIn("ArrestProximity", director)
        self.assertIn("HeistPhase.Arrested", director)
        self.assertIn("Unity JSON lost the alarm/custody confiscation", editor)
        self.assertIn("Interact(StationAction.ReleaseCustody)", playmode)
        self.assertIn('"Visible close guard must cause confiscation', playmode)
        self.assertIn("police custody", guide.lower())
        self.assertNotIn("BankBalance =", director)
        self.assertNotIn("DirtyCash =", director)

    def test_batch_playmode_checkpoints_are_unique_per_editor_invocation(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # Each batch-mode test process must not inherit another invocation's
        # arrest/courier checkpoint. Normal player saves are unchanged.
        self.assertIn('TestInvocationId = Guid.NewGuid().ToString("N")', store)
        self.assertIn('"rabron-playmode-tests", TestInvocationId,', store)
        self.assertIn("Application.temporaryCachePath", store)
        self.assertIn("Application.persistentDataPath, FileName", store)
        self.assertIn('string.Equals(arg, "-runTests"', store)
        self.assertIn("Path.Combine(Application.persistentDataPath, FileName)", store)
        self.assertIn('Path.GetFullPath(PrototypeSaveStore.SavePath)', playmode)
        self.assertIn('Guid.TryParseExact(invocationDirectory, "N"', playmode)
        self.assertIn('"Batch save path must stay stable within one run"', playmode)
        self.assertIn('"Batch Unity tests must never use normal player progress"', playmode)
        self.assertIn("Application.temporaryCachePath", playmode)
        self.assertIn("per-invocation", guide.lower())

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
