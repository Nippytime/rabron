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
        self.assertEqual(len(enum_cases), 21)

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

    def test_original_audio_cues_are_bounded_and_runtime_only(self):
        audio = read("PrototypeAudioFeedback.cs")
        director = read("PrototypeDirector.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        player_smoke = read("PrototypePlayerSmoke.cs")

        self.assertIn("public bool CuesReady", audio)
        self.assertIn("audio != null && audio.CuesReady", player_smoke)
        self.assertIn("[RequireComponent(typeof(AudioSource))]", audio)
        self.assertIn("private const int SampleRate = 24000;", audio)
        self.assertIn("AudioClip.Create(name, count, 1, SampleRate, false)", audio)
        self.assertIn("clip.SetData(samples, 0);", audio)
        self.assertIn("float envelope = Mathf.Sin(Mathf.PI * t);", audio)
        self.assertIn("_output.playOnAwake = false;", audio)
        self.assertIn("_output.loop = false;", audio)
        self.assertIn("_output.spatialBlend = 0f;", audio)
        self.assertIn("!Application.isBatchMode", audio)
        for cue in ("_success", "_rejected", "_alarm"):
            self.assertIn(f"private AudioClip {cue}", audio)
            self.assertIn(f"Destroy({cue});", audio)
        self.assertNotIn("Update()", audio)
        self.assertNotIn("Resources.Load", audio)
        self.assertNotIn("HeistSession", audio)

        self.assertIn("gameObject.AddComponent<PrototypeAudioFeedback>();", director)
        self.assertIn("_audio.PlaySuccess();", director)
        self.assertIn("_audio.PlayRejected();", director)
        self.assertIn("_audio.PlayAlarm();", director)
        self.assertIn("director.GetComponent<PrototypeAudioFeedback>()", playmode)
        self.assertIn('"No original action audio presenter"', playmode)
        self.assertIn("clip.GetData(samples, clip.samples / 2 - 256)", playmode)
        self.assertIn("Generated cue must contain non-silent PCM samples", playmode)
        self.assertIn("original", guide.lower())
        self.assertIn("sound", guide.lower())

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
        acceptance = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
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
        self.assertEqual(tests.count("[Test]"), 1)
        self.assertIn("public void UnreadableCheckpointsMustSurviveLaterAutosaves()", tests)
        self.assertIn("SceneBootCreatesRuntimePlayerCameraHudAndStations", tests)
        self.assertIn("HeistMarkersDriveFullLoopAndPhysicalCounterMoney", tests)
        self.assertIn("FindFirstObjectByType<PrototypeDirector>()", tests)
        self.assertIn("Perform", tests)
        self.assertIn("StationAction.CollectCash", tests)
        self.assertIn("StationAction.Deposit", tests)
        self.assertIn("Is.EqualTo(HeistPhase.Idle)", tests)
        self.assertIn("field.SetValue(director, original)", tests)
        self.assertIn("Is.EqualTo(21)", tests)

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
        self.assertIn(
            "Rabron.Prototype.Tests.PlayModeFlowTests.UnreadableCheckpointsMustSurviveLaterAutosaves",
            validator
        )
        self.assertIn("$total -lt $expected.Count", validator)
        self.assertIn("$testCount -lt 3", acceptance)
        self.assertIn("all three named tests passed", validator_tests)
        self.assertIn(
            "green two-case report missing mandatory save-recovery test",
            validator_tests
        )
        self.assertIn("unrelated third test cannot replace save recovery", validator_tests)
        self.assertIn("failed save-recovery case hidden by green summary", validator_tests)
        self.assertIn("skipped save-recovery case hidden by green summary", validator_tests)
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
        self.assertIn("new List<InteractionMarker>(21)", world)
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

    def test_real_windows_player_boot_is_a_required_isolated_gate(self):
        boot = read("PrototypeBoot.cs")
        probe = read("PrototypePlayerSmoke.cs")
        store = read("PrototypeSaveStore.cs")
        player = (UNITY / "Tools/Verify-WindowsPlayer.ps1").read_text(
            encoding="utf-8")
        acceptance = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
            encoding="utf-8")
        fixture = (UNITY / "Tools/Test-AcceptanceGate.ps1").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn('"-rabronPlayerSmoke"', boot)
        self.assertIn("Application.isBatchMode", boot)
        self.assertIn("director.gameObject.AddComponent<PrototypePlayerSmoke>()", boot)
        self.assertIn("yield return null;", probe)
        self.assertIn("FindFirstObjectByType<PrototypeDirector>()", probe)
        self.assertIn("FindFirstObjectByType<ThirdPersonMotor>()", probe)
        self.assertIn("FindFirstObjectByType<PrototypeHud>()", probe)
        self.assertIn("markers.Length == 21 && actions.Count == 21", probe)
        self.assertIn("RABRON_WINDOWS_PLAYER_SMOKE_PASS", probe)
        self.assertIn("Application.Quit(booted ? 0 : 1)", probe)

        self.assertIn('"rabron-player-smoke", PlayerSmokeInvocationId', store)
        self.assertIn("Application.temporaryCachePath", store)
        self.assertIn("Guid.NewGuid().ToString(\"N\")", store)
        self.assertIn('"-rabronPlayerSmoke"', store)

        self.assertIn("Remove-Item -LiteralPath $LogPath -Force", player)
        self.assertIn("[PlatformID]::Win32NT", player)
        self.assertIn("Test-Path -LiteralPath $ExePath -PathType Leaf", player)
        self.assertIn("'-batchmode', '-nographics', '-rabronPlayerSmoke'", player)
        self.assertIn("Start-Process -FilePath $ExePath", player)
        self.assertIn("$process.WaitForExit($TimeoutSeconds * 1000)", player)
        self.assertIn("$process.Kill()", player)
        self.assertIn("$exitCode -ne 0", player)
        self.assertIn("RABRON_WINDOWS_PLAYER_SMOKE_PASS", player)

        build = acceptance.index("'Verify-Unity.ps1') -EditorPath $EditorPath -BuildWindows")
        player_gate = acceptance.index("'Verify-WindowsPlayer.ps1')")
        manifest = acceptance.index("Move-Item -LiteralPath $temp -Destination $EvidencePath")
        self.assertLess(build, player_gate)
        self.assertLess(player_gate, manifest)
        self.assertIn("windows_player_smoke_passed = $true", acceptance)
        self.assertIn("windows_player_smoke_log = File-Summary $playerLog", acceptance)
        self.assertIn("Assert-NonemptyFile $playerLog", acceptance)
        self.assertIn("Stale green Windows Player log survived", fixture)
        self.assertIn("missing-player.exe", fixture)
        self.assertIn("headless", guide.lower())
        self.assertIn("not a manual", guide.lower())

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

    def test_untracked_unity_assets_rejected_and_scene_fingerprinted(self):
        gate = (UNITY / "Tools/Assert-UnitySourceTree.ps1").read_text(
            encoding="utf-8")
        runner = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
            encoding="utf-8")
        fixture = (UNITY / "Tools/Test-AcceptanceGate.ps1").read_text(
            encoding="utf-8")
        workflow = (ROOT.parent / ".github/workflows/reconstruction-tests.yml").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("ls-files --others --exclude-standard", gate)
        self.assertIn("reconstruction/unity-prototype/Assets", gate)
        self.assertIn("Scenes/Prototype.unity", gate)
        self.assertIn("EndsWith('.meta'", gate)
        self.assertIn("Untracked authored Unity assets are not covered by Git HEAD", gate)
        self.assertIn("Assert-UnitySourceTree.ps1", workflow)
        self.assertEqual(runner.count("'Assert-UnitySourceTree.ps1'"), 3)
        self.assertIn("$sceneAtSmoke = File-Summary $scene", runner)
        self.assertEqual(
            runner.count("(File-Summary $scene).sha256 -ne $sceneAtSmoke.sha256"), 2
        )
        self.assertIn("generated_scene = $sceneAtSmoke", runner)
        self.assertIn("Assert-NonemptyFile $smoke", runner)
        self.assertIn("Move-Item -LiteralPath $temp -Destination $EvidencePath", runner)
        self.assertIn("Untracked authored Unity file was incorrectly accepted", fixture)
        self.assertIn("synthetic Unity import metadata", fixture)
        self.assertIn("synthetic bootstrap scene", fixture)
        self.assertIn("generated scene", guide.lower())
        self.assertIn("untracked", guide.lower())
        self.assertIn("not a real unity", guide.lower())

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
        self.assertIn("Phase == HeistPhase.Idle || Phase == HeistPhase.Scouted", core)
        self.assertIn("ReleaseCustody", marker)
        self.assertIn("StationAction.ReleaseCustody", world)
        self.assertIn('new List<InteractionMarker>(21)', world)
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

    def test_unreadable_primary_and_backup_are_not_overwritten(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("private static bool _preserveUnreadableSaves;", store)
        self.assertIn("_preserveUnreadableSaves = false;", store)
        self.assertIn("_preserveUnreadableSaves = File.Exists(primary) || File.Exists(backup);", store)
        self.assertIn("if (_preserveUnreadableSaves)", store)
        self.assertIn("Autosave disabled to preserve unreadable checkpoints.", store)
        self.assertIn("copy or move the existing save and backup files", store)
        self.assertIn('File.Copy(backup, primary, overwrite: true)', store)
        self.assertIn('File.Replace(temporary, target, target + ".bak")', store)
        self.assertIn("public void UnreadableCheckpointsMustSurviveLaterAutosaves()", playmode)
        self.assertIn('"-runTests"', playmode)
        self.assertIn("File.ReadAllBytes(primary), Is.EqualTo(brokenPrimary)", playmode)
        self.assertIn("File.ReadAllBytes(backup), Is.EqualTo(brokenBackup)", playmode)
        self.assertIn('"Auto-save must fail closed on corruption"', playmode)
        self.assertIn("PrototypeSaveStore.Load(out _);", playmode)
        self.assertIn("move the save", guide.lower())
        self.assertIn("autosave", guide.lower())

    def test_unsaved_checkpoint_warning_remains_visible_in_live_hud(self):
        store = read("PrototypeSaveStore.cs")
        director = read("PrototypeDirector.cs")
        hud = read("PrototypeHud.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("public static bool SavingDisabled => _preserveUnreadableSaves", store)
        self.assertIn("PrototypeSaveStore.SavingDisabled,", director)
        self.assertIn("PrototypeSaveStore.LastWriteFailed);", director)
        self.assertIn("bool savingDisabled, bool lastWriteFailed)", hud)
        self.assertIn("public bool SaveWarningVisible { get; private set; }", hud)
        self.assertIn("_saveWarning.style.display = SaveWarningVisible", hud)
        self.assertIn("SAVING DISABLED — THIS SESSION WILL NOT BE SAVED", hud)
        self.assertIn("Copy or move damaged save and .bak files", hud)
        self.assertIn("SaveWarningVisible = savingDisabled || lastWriteFailed;", hud)
        self.assertIn("Temporary notices must not clear the unsaved-session warning", playmode)
        self.assertIn("Blocked autosave must have a persistent HUD warning", playmode)
        self.assertIn("Valid backup recovery must clear the persistent warning", playmode)
        self.assertIn("PrototypeSaveStore.SavingDisabled, Is.True", playmode)
        self.assertIn("PrototypeSaveStore.SavingDisabled, Is.False", playmode)
        self.assertIn("persistent", guide.lower())
        self.assertIn("saving disabled", guide.lower())

    def test_failed_disk_writes_keep_a_distinct_visible_warning_until_retry(self):
        store = read("PrototypeSaveStore.cs")
        director = read("PrototypeDirector.cs")
        hud = read("PrototypeHud.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("public static bool LastWriteFailed { get; private set; }", store)
        self.assertIn("LastWriteFailed = true;", store)
        self.assertEqual(store.count("LastWriteFailed = false;"), 2)
        self.assertIn("error = exception.Message;", store)
        self.assertIn("SaveWarningVisible = savingDisabled || lastWriteFailed;", hud)
        self.assertIn("LAST SAVE FAILED — RECENT PROGRESS IS NOT SAVED", hud)
        self.assertIn("Check free space and folder permissions", hud)
        self.assertIn("PrototypeSaveStore.LastWriteFailed);", director)
        self.assertLess(
            director.index('Notice("Laundering complete. Leave the city'),
            director.index("SaveProgress();"),
            "Laundering success notice must not overwrite a save failure",
        )

        # These are authored Play Mode assertions: a .tmp directory forces a
        # failed actual filesystem write in the isolated -runTests directory.
        self.assertIn("Directory.CreateDirectory(temporary);", playmode)
        self.assertIn("Directory.Delete(temporary);", playmode)
        self.assertIn("PrototypeSaveStore.LastWriteFailed, Is.True", playmode)
        self.assertIn("PrototypeSaveStore.LastWriteFailed, Is.False", playmode)
        self.assertIn("LAST SAVE FAILED", playmode)
        self.assertIn("A confirmed checkpoint should clear", playmode)
        self.assertIn("failed disk writes", guide.lower())

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

    def test_empty_heist_withdrawal_has_no_cash_faucet_or_stuck_escape(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8")
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        marker = read("InteractionMarker.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("public void WithdrawEmptyHanded()", core)
        self.assertIn("Phase == HeistPhase.Robbing && _loot.Count == 0", core)
        self.assertIn("Phase == HeistPhase.Robbing && _loot.Count > 0", core)
        self.assertIn("snapshot.Phase != HeistPhase.Escaped || loot.Length > 0", core)
        self.assertIn("StationAction.WithdrawEmptyHanded", director)
        self.assertIn("_session.WithdrawEmptyHanded();", director)
        self.assertIn("_session.Loot.Count == 0", director)
        self.assertIn("WithdrawEmptyHanded", marker)
        self.assertIn("new List<InteractionMarker>(21)", world)
        self.assertIn('StationAction.WithdrawEmptyHanded,', world)
        self.assertIn("WITHDRAW", director)
        self.assertIn("retreat.WithdrawEmptyHanded();", editor)
        self.assertIn("Interact(StationAction.WithdrawEmptyHanded)", playmode)
        self.assertIn("StationAction.Escape }), Is.False", playmode)
        self.assertIn("no reward", guide.lower())
        self.assertNotIn("DirtyCash =", director)
        self.assertNotIn("CounterCash =", director)

    def test_city_travel_rejects_active_heist_and_unreachable_desert_saves(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        director = read("PrototypeDirector.cs")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # The portable state machine must not bypass the Unity-only
        # ExitCity availability gate or import an interrupted desert heist.
        self.assertIn("Phase == HeistPhase.Idle || Phase == HeistPhase.Scouted ||", core)
        self.assertIn("Phase == HeistPhase.Laundered)", core)
        self.assertIn("snapshot.Zone == Zone.Desert", core)
        self.assertIn("snapshot.Phase != HeistPhase.Laundered)", core)
        self.assertIn("unreachable desert heist phase", core)
        self.assertIn("Finish the current heist before leaving the city.", core)
        self.assertIn("Active robbery must not escape city through core API", editor)
        self.assertIn("Unity JSON accepted unreachable desert robbery", editor)
        self.assertIn('"An active robbery must not expose desert exit"', playmode)
        self.assertIn('"A completed heist must allow lawful city departure"', playmode)
        self.assertIn("StationAction.ExitCity => city && _session.Phase == HeistPhase.Laundered", director)
        self.assertIn("in-progress", guide.lower())
        self.assertIn("desert", guide.lower())

    def test_original_driving_car_enter_throttle_brake_and_safe_exit(self):
        car = read("PrototypeVehicle.cs")
        motor = read("ThirdPersonMotor.cs")
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        marker = read("InteractionMarker.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("WithdrawEmptyHanded, VehicleEnter", marker)
        self.assertIn("new List<InteractionMarker>(21)", world)
        self.assertIn("car.AddComponent<PrototypeVehicle>()", world)
        self.assertIn("Station(car.transform, stations, StationAction.VehicleEnter", world)
        self.assertIn("carBody = car.AddComponent<CharacterController>()", world)
        self.assertIn("public bool BeginDriving()", car)
        self.assertIn("public void Drive(Vector2 steeringAndThrottle", car)
        self.assertIn("CharacterController", car)
        self.assertIn("_body.Move(", car)
        self.assertIn("CollisionFlags.Sides", car)
        self.assertIn("Physics.OverlapCapsuleNonAlloc(", car)
        self.assertIn("QueryTriggerInteraction.Ignore", car)
        self.assertIn("Mathf.Abs(_speed) > 0.5f", car)
        self.assertIn("public bool TryFindExit(", car)
        self.assertNotIn("HeistSession", car)
        self.assertIn("public void BoardVehicle(PrototypeVehicle vehicle)", motor)
        self.assertIn("public bool TryExitVehicle()", motor)
        self.assertIn("public bool IsDriving => _vehicle != null", motor)
        self.assertIn("_character.enabled = false;", motor)
        self.assertIn("_character.enabled = true;", motor)
        self.assertIn("_exitInteractFrame != Time.frameCount", motor)
        self.assertIn("Transform focus = _vehicle != null", motor)
        self.assertIn("StationAction.VehicleEnter => city && civilian", director)
        self.assertIn("_player.BoardVehicle(_vehicle);", director)
        self.assertIn("_player.IsDriving", director)
        self.assertIn("No collider-backed prototype vehicle was created", editor)
        self.assertIn("Interact(StationAction.VehicleEnter)", playmode)
        self.assertIn('"Moving car must prevent an unsafe exit"', playmode)
        self.assertIn('"Brake must stop the car"', playmode)
        self.assertIn('"Stationary car must allow a collision-clear exit"', playmode)
        self.assertIn("drive", guide.lower())
        self.assertIn("vehicle position", guide.lower())

    def test_car_exit_checks_full_actual_passenger_capsule(self):
        car = read("PrototypeVehicle.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # The old hardcoded +0.55m/+1.55m capsule missed ankle-height
        # obstacles before the full-height on-foot collider was reenabled.
        self.assertNotIn("candidate + Vector3.up * 0.55f", car)
        self.assertNotIn("candidate + Vector3.up * 1.55f", car)
        self.assertIn("passenger.GetComponent<CharacterController>()", car)
        self.assertIn("passengerBody.radius", car)
        self.assertIn("passengerBody.height", car)
        self.assertIn("passengerBody.center", car)
        self.assertIn("passengerBody.skinWidth", car)
        self.assertIn("passenger.lossyScale", car)
        self.assertIn("center - Vector3.up * halfAxis", car)
        self.assertIn("center + Vector3.up * halfAxis", car)
        self.assertIn("clearanceRadius, _exitHits", car)
        self.assertIn("if (count == _exitHits.Length)", car)
        self.assertIn("!hit.transform.IsChildOf(passenger)", car)

        # These assertions are authored real-Unity Play Mode test source;
        # hosted Python cannot claim collider execution or Windows acceptance.
        self.assertIn("Synthetic ankle-height exit obstruction", playmode)
        self.assertIn("Full character capsule must reject ankle-height exit blockers",
                      playmode)
        self.assertIn("motor.IsDriving && car.Occupied, Is.True", playmode)
        self.assertIn("Stationary car must allow a collision-clear exit", playmode)
        self.assertIn("ankle-height", guide)

    def test_driving_camera_look_stays_independent_of_vehicle_steering(self):
        motor = read("ThirdPersonMotor.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # Driver look must be applied before the vehicle branch returns,
        # with an orbit offset rather than moving the steering transform.
        self.assertIn("private void ApplyLookDelta(Vector2 look)", motor)
        self.assertLess(
            motor.index("ApplyLookDelta(look);"),
            motor.index("if (ExitPressAfterBoard(_boardedVehicleFrame, Time.frameCount,"),
        )
        self.assertIn("if (_vehicle == null)\n                transform.Rotate", motor)
        self.assertIn(
            "_drivingLookYaw = Mathf.Repeat(_drivingLookYaw + look.x + 180f, 360f) - 180f;",
            motor,
        )
        self.assertIn(
            "focus.eulerAngles.y + (_vehicle != null ? _drivingLookYaw : 0f)",
            motor,
        )
        self.assertIn("_pitch = Mathf.Clamp(_pitch - look.y, -45f, 70f);", motor)
        self.assertIn(
            "transform.rotation = Quaternion.Euler(0f, parkedCar.transform.eulerAngles.y, 0f);",
            motor,
        )
        self.assertIn("private float _drivingLookYaw;", motor)

        # These are test sources, not evidence that Unity ran.
        self.assertIn('GetMethod(\n                    "ApplyLookDelta"', playmode)
        self.assertIn('"Driver look accumulation must wrap without drifting"', playmode)
        self.assertIn('"Camera orbit must not steer the car"', playmode)
        self.assertIn('"Vehicle orbit must reset after a safe exit"', playmode)
        self.assertIn('"On-foot camera heading should match the parked car"', playmode)
        self.assertIn("mouse and right stick", guide.lower())

    def test_gamepad_right_stick_works_with_unlocked_mouse_cursor(self):
        motor = read("ThirdPersonMotor.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        hud = read("PrototypeHud.cs")

        self.assertIn("private static Vector2 ComposeLook(", motor)
        self.assertIn("Vector2 mouseLook = cursorLocked ? mouseDelta * 0.12f", motor)
        self.assertIn("Vector2 stickLook = Vector2.ClampMagnitude(gamepadStick, 1f)", motor)
        self.assertIn("120f * Mathf.Max(0f, deltaSeconds)", motor)
        self.assertIn("return mouseLook + stickLook;", motor)
        self.assertIn("Vector2 look = ComposeLook(_mouse.ReadValue<Vector2>(),", motor)
        self.assertIn("_stick.ReadValue<Vector2>()", motor)
        self.assertIn("Cursor.lockState == CursorLockMode.Locked, Time.deltaTime", motor)
        self.assertIn("if (look.sqrMagnitude > 0f)\n                ApplyLookDelta(look);", motor)
        self.assertNotIn(
            "if (Cursor.lockState == CursorLockMode.Locked)\n            {\n"
            "                Vector2 look", motor
        )
        self.assertLess(
            motor.index("Vector2 look = ComposeLook("),
            motor.index("if (_vehicle != null)\n            {\n"
                        "                if (ExitPressAfterBoard"),
        )
        self.assertIn('GetMethod("ComposeLook", flags)', playmode)
        self.assertIn("Right stick must still rotate the camera with released cursor",
                      playmode)
        self.assertIn("Unlocked mouse motion must not steer the camera", playmode)
        self.assertIn("Locked cursor must retain both mouse and gamepad look",
                      playmode)
        self.assertIn("Gamepad look must not require a connected mouse", playmode)
        self.assertIn("right stick", guide.lower())
        self.assertIn("cursor", guide.lower())
        self.assertIn("right stick", hud.lower())

    def test_car_board_press_cannot_same_frame_exit(self):
        motor = read("ThirdPersonMotor.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("private int _boardedVehicleFrame = -1;", motor)
        self.assertIn("_boardedVehicleFrame = Time.frameCount;", motor)
        self.assertIn("ExitPressAfterBoard(_boardedVehicleFrame, Time.frameCount,", motor)
        self.assertIn("private static bool ExitPressAfterBoard", motor)
        self.assertIn("=> pressed && boardFrame != frame;", motor)
        self.assertIn("_exitInteractFrame != Time.frameCount", motor)
        self.assertIn("TryExitVehicle();", motor)
        self.assertIn('"Boarding press must never immediately exit the car"', playmode)
        self.assertIn('"A later frame without a fresh press must not exit"', playmode)
        self.assertIn('"A fresh later-frame press must allow a stopped-car exit"', playmode)
        self.assertIn("boardFrame, Is.EqualTo(Time.frameCount)", playmode)
        self.assertIn("release and press", guide.lower())
        self.assertIn("same-frame", guide.lower())

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
