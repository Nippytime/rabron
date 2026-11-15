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

    def test_demo_laundering_percentage_is_exact_and_overflow_safe(self):
        balance = read("PrototypeBalance.cs")
        smoke = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("if (amount <= 0)", balance)
        self.assertIn(
            "CleanPayoutPercent < 0 || CleanPayoutPercent > 100", balance
        )
        self.assertIn("long whole = amount / 100;", balance)
        self.assertIn("long remainder = amount % 100;", balance)
        self.assertIn("checked(whole * CleanPayoutPercent +", balance)
        self.assertIn("remainder * CleanPayoutPercent / 100", balance)
        self.assertNotIn("amount * CleanPayoutPercent / 100", balance)
        self.assertIn("ValidateDemoEconomy();", smoke)
        self.assertIn("ScriptableObject.CreateInstance<PrototypeBalance>()", smoke)
        self.assertIn("CleanPayoutFor(long.MaxValue)", smoke)
        self.assertIn("7378697629483820645L", smoke)
        self.assertIn("new[] { -1, 101 }", smoke)
        self.assertIn("UnityEngine.Object.DestroyImmediate(economy)", smoke)
        self.assertIn("overflow-safe", guide.lower())
        self.assertIn("not yet", guide.lower())

    def test_laundering_jobs_cannot_overflow_clean_cash_on_completion(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8"
        )
        tests = (ROOT / "game/Tests/Program.cs").read_text(
            encoding="utf-8"
        )
        smoke = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        guide = (ROOT / "game/README.md").read_text(encoding="utf-8")

        starting = core.split("public void StartLaundering(", 1)[1].split(
            "public void CompleteLaundering(", 1
        )[0]
        restoring = core.split(
            "public static HeistSession FromSnapshot(", 1
        )[1].split("private static void Require(", 1)[0]
        self.assertIn(
            "Require(cleanPayout <= long.MaxValue - CleanCash,", starting
        )
        self.assertLess(
            starting.index("cleanPayout <= long.MaxValue - CleanCash"),
            starting.index("DirtyCash -= dirtyAmount;"),
        )
        self.assertIn(
            "snapshot.LaunderingPayout > long.MaxValue - snapshot.CleanCash",
            restoring,
        )
        self.assertIn("Save contains an unpayable laundering job.", restoring)
        self.assertIn("LaunderingRejectsUnpayableCleanWalletCredits,", tests)
        self.assertIn("game.StartLaundering(20, 9, 100, 2)", tests)
        self.assertIn("game.StartLaundering(8, 8, 100, 2)", tests)
        self.assertIn("forged.CleanCash = long.MaxValue;", tests)
        self.assertIn("ValidateLaunderingCapacity();", smoke)
        self.assertIn("JsonUtility.FromJson<HeistSessionSnapshot>", smoke)
        self.assertIn("Unpayable laundering must not debit dirty cash", smoke)
        self.assertIn("unpayable", guide.lower())

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

    def test_guard_uses_crouch_capsule_and_solid_low_cover(self):
        guard = read("GuardSensor.cs")
        motor = read("ThirdPersonMotor.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        occlusion = read("WorldOcclusion.cs")
        self.assertIn("WorldOcclusion.UpperBodyPoint(player)", guard)
        self.assertIn("actor.GetComponent<CharacterController>()", occlusion)
        self.assertIn("actor.TransformPoint(body.center +", occlusion)
        self.assertIn("body.height * 0.5f - body.radius * 0.5f", occlusion)
        self.assertIn("delta.sqrMagnitude > DemoSightRange * DemoSightRange", guard)
        self.assertNotIn(
            "horizontal.sqrMagnitude > DemoSightRange * DemoSightRange", guard
        )
        self.assertIn("Vector3.ProjectOnPlane(delta, Vector3.up)", guard)
        self.assertIn("WorldOcclusion.HasClearLine(", guard)
        self.assertIn("QueryTriggerInteraction.Ignore", read("WorldOcclusion.cs"))
        self.assertIn('private void UpdateCrouch(bool held)', motor)
        self.assertIn("_character.height = height;", motor)
        self.assertIn("ValidateCrouchedGuardCover(root.transform, player, guard);",
                      editor)
        world = read("PrototypeWorld.cs")
        self.assertIn('"Warehouse stealth cover"', world)
        self.assertIn('new Vector3(0f, 0.75f, 30f)', world)
        self.assertIn('new Vector3(2.8f, 1.5f, 0.6f)', world)
        self.assertIn('root.Find("Warehouse stealth cover")', editor)
        self.assertIn('cover.GetComponent<BoxCollider>().enabled', editor)
        self.assertIn('!cover.GetComponent<BoxCollider>().isTrigger', editor)
        self.assertNotIn('"Temporary guard cover regression"', editor)
        self.assertIn('crouch.Invoke(player, new object[] { true });', editor)
        self.assertIn('crouch.Invoke(player, new object[] { false });', editor)
        self.assertIn("Standing player must be visible over low solid cover", editor)
        self.assertIn("Crouched player must be hidden behind low solid cover", editor)
        self.assertIn("Standing back up must restore guard visibility", editor)
        self.assertIn("far above 3D sight range", editor)
        self.assertIn("Standing beside real warehouse cover must remain visible", editor)
        self.assertNotIn("UnityEngine.Object.DestroyImmediate(cover)", editor)
        self.assertIn("crouch behind low cover", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_crouched_station_interactions_respect_live_capsule_and_cover(self):
        occlusion = read("WorldOcclusion.cs")
        guard = read("GuardSensor.cs")
        director = read("PrototypeDirector.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("public static Vector3 UpperBodyPoint(Transform actor)", occlusion)
        self.assertIn("actor.GetComponent<CharacterController>()", occlusion)
        self.assertIn("body.center +", occlusion)
        self.assertIn("body.height * 0.5f - body.radius * 0.5f", occlusion)
        self.assertIn("actor.position + Vector3.up * 1.5f", occlusion)
        self.assertIn("WorldOcclusion.UpperBodyPoint(player)", guard)
        self.assertIn("WorldOcclusion.UpperBodyPoint(_player.transform)", director)
        self.assertNotIn(
            "_player.transform.position + Vector3.up * 1.5f", director
        )

        # This authored Editor regression targets actual generated cover and
        # the live station geometry rather than a separate temporary barrier.
        self.assertIn('root.Find("Warehouse stealth cover")', editor)
        self.assertIn('marker => marker.Action == StationAction.ControlStaff', editor)
        self.assertIn("WorldOcclusion.UpperBodyPoint(player.transform)", editor)
        self.assertIn("WorldOcclusion.HasClearLine(", editor)
        self.assertIn("Standing sightline should clear real cover", editor)
        self.assertIn("Crouched station interaction cannot pass through", editor)
        self.assertIn("Standing back up must restore the station sightline", editor)
        self.assertIn("Flanking physical cover must restore station sightline", editor)
        self.assertIn("station interactions", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_real_guard_control_station_is_reachable_across_cover(self):
        world = read("PrototypeWorld.cs")
        director = read("PrototypeDirector.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn('new Vector3(-1.3f, 0f, 31.9f)', world)
        self.assertNotIn('new Vector3(3f, 0f, 34f)', world)
        self.assertIn("private const float InteractionRadius = 3.8f;", director)
        self.assertIn('"InteractionRadius", BindingFlags.Static', editor)
        self.assertIn("radiusField.GetRawConstantValue()", editor)
        self.assertIn('"Guard control must be inside the actual interaction radius"', editor)
        self.assertIn('"Guard control must be the nearest station at test position"', editor)
        self.assertIn("CheckControlInReach();", editor)
        self.assertIn('new Vector3(-0.7f, 0.12f, 29.2f)', editor)
        self.assertIn('new Vector3(-1.95f, 0.12f, 30.5f)', editor)

        # A real Play Mode director uses its own station availability,
        # distance and collision checks. Ray-only Editor checks are not enough.
        self.assertIn('"FindNearbyStation", PrivateInstance', playmode)
        self.assertIn("coverSession.StartHeist();", playmode)
        self.assertIn('new Vector3(-0.7f, 0.12f, 29.2f)', playmode)
        self.assertIn('"Control marker must win nearest-station selection"', playmode)
        self.assertIn('updateCrouch.Invoke(motor, new object[] { true });', playmode)
        self.assertIn('"Crouched player cannot select guard control through cover"', playmode)
        self.assertIn('"Standing again must restore nearby guard-control focus"', playmode)
        self.assertIn('"Walking around live cover must restore nearby station focus"', playmode)
        self.assertIn("motor.WarpTo(originalPosition);", playmode)
        self.assertIn("guard-control marker", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_quiet_guard_control_flank_uses_live_cone_and_dispatch(self):
        world = read("PrototypeWorld.cs")
        guard = read("GuardSensor.cs")
        director = read("PrototypeDirector.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn('new Vector3(-1.3f, 0f, 31.9f)', world)
        self.assertIn("private const float DemoHalfSightAngle = 55f;", guard)
        self.assertIn("Vector3.Angle(transform.forward, horizontal)", guard)
        self.assertIn("private const float InteractionRadius = 3.8f;", director)
        self.assertIn('new Vector3(-3.6f, 0.12f, 31f)', editor)
        self.assertIn("CheckControlInReach();", editor)
        self.assertIn('"Quiet left flank must reach the real guard-control station"', editor)
        self.assertIn('"Quiet flank guard ray must be unobstructed', editor)
        self.assertIn('"Quiet flank must be outside the real guard vision cone"', editor)
        self.assertIn('new Vector3(-3.6f, 0.12f, 31f)', playmode)
        self.assertIn("liveGuard.CanSee(motor.transform)", playmode)
        self.assertIn('"Quiet flank must select guard control', playmode)
        self.assertIn("perform.Invoke(director, new object[] { quietFocus, now })", playmode)
        self.assertIn("coverSession.StaffControlled, Is.True", playmode)
        self.assertIn("coverSession.AlarmRaised, Is.False", playmode)
        self.assertIn("update.Invoke(director, null)", playmode)
        self.assertIn("motor.WarpTo(originalPosition);", playmode)
        self.assertIn("wider left flank", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_alarm_is_single_shot_and_requires_uncontrolled_staff(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8"
        )
        tests = (ROOT / "game/Tests/Program.cs").read_text(
            encoding="utf-8"
        )
        director = read("PrototypeDirector.cs")
        guide = (ROOT / "game/README.md").read_text(encoding="utf-8")

        alarm = core.split("public void RaiseAlarm()", 1)[1].split(
            "public void ControlStaff()", 1
        )[0]
        self.assertIn("Phase == HeistPhase.Robbing", alarm)
        self.assertIn("!AlarmRaised && !StaffControlled", alarm)
        self.assertIn("AlarmRaised = true;", alarm)
        self.assertIn(
            "!_session.StaffControlled && !_session.AlarmRaised &&",
            director,
        )
        self.assertIn("GuardAlarmIsSingleShotAndRequiresActiveStaff,", tests)
        self.assertIn(
            "Throws<InvalidOperationException>(() => controlled.RaiseAlarm())",
            tests,
        )
        self.assertIn(
            "Throws<InvalidOperationException>(() => alerted.RaiseAlarm())",
            tests,
        )
        self.assertIn(
            "Throws<InvalidOperationException>(() => restored.RaiseAlarm())",
            tests,
        )
        self.assertIn(
            "game.RaiseAlarm();\n        game.ControlStaff();", tests,
        )
        self.assertIn("single-shot", guide.lower())
        self.assertIn("controlled staff", guide.lower())

    def test_guard_overlap_cannot_bypass_visibility_and_arrest(self):
        sensor = read("GuardSensor.cs")
        director = read("PrototypeDirector.cs")
        editor = (UNITY / "Assets/Editor/PrototypeSmokeTest.cs").read_text(
            encoding="utf-8"
        )
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # Full 3D range remains enforced even for elevated targets;
        # facing is undefined at exact overlap, so only ordinary nonzero
        # horizontal directions are subject to the cone.
        self.assertIn("delta.sqrMagnitude > DemoSightRange * DemoSightRange", sensor)
        self.assertIn("Vector3.ProjectOnPlane(delta, Vector3.up)", sensor)
        self.assertIn("horizontal.sqrMagnitude >= 0.001f &&", sensor)
        self.assertIn("Vector3.Angle(transform.forward, horizontal)", sensor)
        self.assertNotIn("horizontal.sqrMagnitude < 0.001f)", sensor)
        self.assertIn("WorldOcclusion.HasClearLine(origin, target, transform", sensor)
        self.assertIn("player.transform.position = guard.transform.position;", editor)
        self.assertIn("Overlapping the guard must not grant invisibility", editor)
        self.assertIn("Guard should not see a player directly behind him", editor)
        self.assertIn("motor.WarpTo(activeGuard.transform.position);", playmode)
        self.assertIn("activeGuard.CanSee(motor.transform), Is.True", playmode)
        self.assertIn("Guard must detect a player at its exact position", playmode)
        self.assertIn("Overlapping guard must cause confiscation after alarm", playmode)
        self.assertIn("_session.ArrestAfterAlarm();", director)
        self.assertIn("overlap", guide.lower())

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

    def test_hold_crouch_has_real_capsule_and_safe_standing_clearance(self):
        motor = read("ThirdPersonMotor.cs")
        hud = read("PrototypeHud.cs")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")

        self.assertIn('new InputAction("Crouch", InputActionType.Button)', motor)
        self.assertIn('_crouch.AddBinding("<Keyboard>/leftCtrl")', motor)
        self.assertIn('_crouch.AddBinding("<Gamepad>/rightStickPress")', motor)
        self.assertIn('_sprint.AddBinding("<Gamepad>/leftStickPress")', motor)
        for action in ("Enable", "Disable", "Dispose"):
            self.assertIn(f"_crouch?.{action}();", motor)
        self.assertIn("UpdateCrouch(_crouch.IsPressed());", motor)
        self.assertIn("float speed = _isCrouched ? DemoCrouchSpeed :", motor)
        self.assertIn("public bool IsCrouched => _isCrouched;", motor)
        self.assertIn("private void UpdateCrouch(bool held)", motor)
        self.assertIn("if (!held && !CanStand())", motor)
        self.assertIn("_character.height = height;", motor)
        self.assertIn("_character.center = _standingCenter -", motor)
        self.assertIn("_character.stepOffset = _standingStepOffset;", motor)
        self.assertIn("_bodyVisual.localScale = visualScale;", motor)
        self.assertIn("private bool CanStand()", motor)
        self.assertIn("Physics.OverlapCapsuleNonAlloc(", motor)
        self.assertIn("QueryTriggerInteraction.Ignore", motor)
        self.assertIn("if (count == _standHits.Length)", motor)
        self.assertIn("hit.transform.IsChildOf(transform)", motor)
        self.assertIn("Vector3 crouchedHead = transform.TransformPoint(", motor)
        self.assertIn("Vector3 standingHead = transform.TransformPoint(", motor)
        self.assertIn("_isCrouched ? 1.08f : 1.6f", motor)
        self.assertIn("Ctrl / R-stick click: crouch", hud)
        self.assertIn("Hold crouch (on foot)", guide)
        self.assertIn("low ceiling leaves the player", guide)
        self.assertIn('GetField("_crouch", PrivateInstance)', playmode)
        self.assertIn("Crouching must not lift or sink the player's feet", playmode)
        self.assertIn("Overhead solid geometry must prevent standing", playmode)
        self.assertIn("Blocked stand must not resize the capsule", playmode)
        self.assertIn("Clear overhead volume must permit standing", playmode)

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
        self.assertIn('director.transform.Find("Warehouse stealth cover")', probe)
        self.assertIn("cover.GetComponent<BoxCollider>()", probe)
        self.assertIn("coverCollider != null && coverCollider.enabled", probe)
        self.assertIn("!coverCollider.isTrigger", probe)
        self.assertIn("RABRON_WINDOWS_PLAYER_SMOKE_PASS", probe)
        self.assertIn("Application.Quit(saved ? 0 : 1)", probe)

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

    def test_windows_player_smoke_requires_isolated_persistence_roundtrip(self):
        smoke = read("PrototypePlayerSmoke.cs")
        store = read("PrototypeSaveStore.cs")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # The built-player probe is opt-in, and a bad world must not write.
        self.assertIn("private static bool VerifyIsolatedCheckpoint(out string error)", smoke)
        self.assertIn("bool saved = booted && VerifyIsolatedCheckpoint(out saveError);",
                      smoke)
        self.assertIn("Application.Quit(saved ? 0 : 1)", smoke)
        self.assertIn("FindFirstObjectByType<Camera>()", smoke)
        self.assertIn("FindFirstObjectByType<GuardSensor>()", smoke)
        self.assertIn("FindFirstObjectByType<PrototypeVehicle>()", smoke)
        for presenter in ("CashPilePresenter", "CourierParcelPresenter"):
            self.assertIn(f"FindObjectsByType<{presenter}>(", smoke)
        self.assertIn("FindObjectsInactive.Include, FindObjectsSortMode.None", smoke)
        self.assertIn("cash.Length == 1 && parcels.Length == 1", smoke)
        self.assertIn("vehicle.GetComponent<CharacterController>() != null", smoke)

        # Explicit path verification must happen before touching any file:
        # disallow ordinary Application.persistentDataPath and shared root.
        path_guard = smoke.index('string isolatedRoot = Path.GetFullPath(')
        first_save = smoke.index("PrototypeSaveStore.TrySave(initial, out error)")
        self.assertLess(path_guard, first_save)
        self.assertIn('Application.temporaryCachePath, "rabron-player-smoke"', smoke)
        self.assertIn("Path.GetDirectoryName(invocation), isolatedRoot", smoke)
        self.assertIn("Refusing to write outside a unique player-smoke", smoke)
        self.assertNotIn("Application.persistentDataPath", smoke)
        self.assertIn('"rabron-player-smoke", PlayerSmokeInvocationId', store)

        # First write, reload, second replace and restored previous backup
        # all exercise the real Unity SaveStore/JsonUtility implementation.
        self.assertEqual(smoke.count("PrototypeSaveStore.TrySave("), 2)
        self.assertEqual(smoke.count("PrototypeSaveStore.Load(out _)"), 2)
        self.assertIn("initial.PickUpCourierParcel();", smoke)
        self.assertIn("pending.DeliverCourierParcel(25);", smoke)
        self.assertIn("pending.DepositCleanCash(10);", smoke)
        self.assertIn('File.ReadAllText(path + ".bak")', smoke)
        self.assertIn("HeistSession.FromSnapshot(", smoke)
        self.assertIn("final.CleanCash != 15 || final.BankBalance != 10", smoke)
        self.assertIn("backup.CleanCash != 0 || backup.BankBalance != 0", smoke)
        self.assertIn("Directory.Delete(invocation, recursive: true)", smoke)
        self.assertIn("Could not clean isolated smoke files:", smoke)
        self.assertIn("RABRON_WINDOWS_PLAYER_SMOKE_FAILED:", smoke)
        self.assertIn("never writes or removes normal demo checkpoints", guide)
        self.assertIn("real isolated checkpoint", guide)

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

    def test_real_unity_acceptance_requires_binary_version_attestation(self):
        runner = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
            encoding="utf-8"
        )
        verifier = (UNITY / "Tools/Assert-UnityEditorVersion.ps1").read_text(
            encoding="utf-8"
        )
        fixture = (UNITY / "Tools/Test-AcceptanceGate.ps1").read_text(
            encoding="utf-8"
        )
        workflow = (ROOT.parent / ".github/workflows/reconstruction-tests.yml").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("'6000.3.18f1'", verifier)
        self.assertIn("m_EditorVersion:", verifier)
        self.assertIn("ProjectVersionPath", verifier)
        self.assertIn("& $EditorPath -version", verifier)
        self.assertIn("$LASTEXITCODE", verifier)
        self.assertIn("$versions.Count -ne 1", verifier)
        self.assertIn("$versions[0].Value -cne $required", verifier)
        self.assertIn("Write-Output $required", verifier)
        self.assertIn("actual_editor_version = $actualEditorVersion", runner)
        self.assertIn("'Assert-UnityEditorVersion.ps1'", runner)
        self.assertLess(
            runner.index("'Assert-UnityEditorVersion.ps1'"),
            runner.index("'Verify-Unity.ps1') -EditorPath $EditorPath"),
        )
        self.assertIn("Assert-UnityEditorVersion.ps1", workflow)
        self.assertIn("Test-AcceptanceGate.ps1", workflow)
        self.assertIn("'fake-unity.cmd'", fixture)
        self.assertIn("'fake-unity.sh'", fixture)
        self.assertIn("PASS accepted: exact Unity Editor", fixture)
        for scenario in ("wrong installed version", "ambiguous version output",
                         "nonzero native version probe", "missing version token"):
            self.assertIn(scenario, fixture)
        self.assertIn("actual unity editor version", guide.lower())
        self.assertIn("not a real unity", guide.lower())

    def test_unity_acceptance_rejects_git_head_drift_between_gates(self):
        gate = (UNITY / "Tools/Assert-UnitySourceTree.ps1").read_text(
            encoding="utf-8"
        )
        runner = (UNITY / "Tools/Verify-Acceptance.ps1").read_text(
            encoding="utf-8"
        )
        fixture = (UNITY / "Tools/Test-AcceptanceGate.ps1").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("[string]$ExpectedRevision", gate)
        self.assertIn("git -C $RepoRoot rev-parse --verify HEAD", gate)
        self.assertIn("$actualRevision -cne $ExpectedRevision", gate)
        self.assertIn("Git HEAD changed during Unity acceptance", gate)
        self.assertIn("Expected Unity acceptance Git revision must be", gate)
        self.assertEqual(runner.count("-ExpectedRevision $revision"), 3)
        self.assertIn("git_revision = $revision", runner)
        self.assertIn("$expectedHead = (& git -C $repoRoot rev-parse --verify HEAD)",
                      fixture)
        self.assertIn("-ExpectedRevision $expectedHead", fixture)
        self.assertIn("-ExpectedRevision ('0' * 40)", fixture)
        self.assertIn("Mismatched Git HEAD did not fail provenance", fixture)
        self.assertIn("PASS rejected: changed Unity acceptance Git HEAD", fixture)
        self.assertIn("git head", guide.lower())
        self.assertIn("not a real unity", guide.lower())

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
        self.assertIn("reconstruction/unity-prototype reconstruction/game/Core", gate)
        self.assertIn("reconstruction/unity-prototype/Assets/", gate)
        self.assertIn("Scenes/Prototype.unity", gate)
        self.assertIn("StartsWith($assetsPrefix", gate)
        self.assertIn("EndsWith('.meta'", gate)
        self.assertIn("Untracked Unity acceptance inputs are not covered by Git HEAD", gate)
        for path in ("Packages/", "ProjectSettings/", "Tools/", "game/Core/"):
            self.assertIn(path, fixture)
        self.assertIn("$unexpectedInputs", fixture)
        self.assertIn("foreach ($bad in $unexpectedInputs)", fixture)
        self.assertIn("@($meta) + $unexpectedInputs", fixture)
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
        self.assertIn('"Overlapping guard must cause confiscation after alarm"', playmode)
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
        self.assertIn("_preserveUnreadableSaves = File.Exists(primary) ||", store)
        self.assertIn("File.Exists(backup) || File.Exists(temporary);", store)
        self.assertIn("if (_preserveUnreadableSaves)", store)
        self.assertIn("Autosave disabled to preserve unreadable checkpoints.", store)
        self.assertIn("copy or move the existing save and backup files", store)
        self.assertIn('primary + ".corrupt-" + Guid.NewGuid().ToString("N")', store)
        self.assertIn("File.Move(primary, damaged);", store)
        self.assertIn("File.Copy(backup, primary, overwrite: false)", store)
        self.assertNotIn("File.Copy(backup, primary, overwrite: true)", store)
        self.assertLess(
            store.index("File.Move(primary, damaged);"),
            store.index("File.Copy(backup, primary, overwrite: false)"),
        )
        self.assertIn('File.Replace(temporary, target, target + ".bak")', store)
        self.assertIn("public void UnreadableCheckpointsMustSurviveLaterAutosaves()", playmode)
        self.assertIn('"-runTests"', playmode)
        self.assertIn("File.ReadAllBytes(primary), Is.EqualTo(brokenPrimary)", playmode)
        self.assertIn("File.ReadAllBytes(backup), Is.EqualTo(brokenBackup)", playmode)
        self.assertIn('Path.GetFileName(primary) + ".corrupt-*"', playmode)
        self.assertIn("Is.EqualTo(brokenPrimary)", playmode)
        self.assertIn("File.ReadAllBytes(retainedDamagedPrimary)", playmode)
        self.assertIn("File.ReadAllText(primary), Is.EqualTo(File.ReadAllText(backup))", playmode)
        self.assertIn("File.Delete(retainedDamagedPrimary)", playmode)
        self.assertIn('"Auto-save must fail closed on corruption"', playmode)
        self.assertIn("PrototypeSaveStore.Load(out _);", playmode)
        self.assertIn("move the save", guide.lower())
        self.assertIn("quarantine", guide.lower())
        self.assertIn("autosave", guide.lower())

    def test_interrupted_first_save_stage_recovers_without_overwriting_data(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        load = store.split("public static HeistSession Load(", 1)[1].split(
            "public static bool TrySave(", 1
        )[0]
        self.assertIn('string temporary = primary + ".tmp";', load)
        self.assertIn("!File.Exists(primary) && !File.Exists(backup)", load)
        self.assertIn("TryRead(temporary, out session)", load)
        self.assertIn("File.Move(temporary, primary);", load)
        self.assertNotIn("File.Copy(temporary, primary, overwrite: true)", load)
        self.assertLess(
            load.index("!File.Exists(primary) && !File.Exists(backup)"),
            load.index("File.Move(temporary, primary);"),
        )
        self.assertIn("_preserveUnreadableSaves = true;", load)
        self.assertIn("copy the .tmp file to safety and restart", load)
        self.assertIn("File.Exists(backup) || File.Exists(temporary)", load)
        self.assertIn("Preserve the .tmp checkpoint too.", load)
        self.assertIn("File.WriteAllText(temporary,", playmode)
        self.assertIn("resumed.CarryingCourierParcel, Is.True", playmode)
        self.assertIn("File.ReadAllBytes(primary), Is.EqualTo(stagedBytes)", playmode)
        self.assertIn("File.Exists(temporary), Is.False", playmode)
        self.assertIn("File.ReadAllBytes(temporary), Is.EqualTo(badStage)", playmode)
        self.assertIn("File.WriteAllBytes(temporary, stagedBytes)", playmode)
        self.assertIn("File.ReadAllBytes(backup), Is.EqualTo(brokenBackup)", playmode)
        self.assertIn("File.Delete(temporary);", playmode)
        self.assertIn("staged", guide.lower())
        self.assertIn("autosave", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_existing_primary_autosave_never_erases_previous_staged_progress(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        saving = store.split("public static bool TrySave(", 1)[1].split(
            "private static bool TryRead(", 1
        )[0]
        self.assertIn("if (File.Exists(temporary))", saving)
        self.assertIn('temporary + ".staged-" + Guid.NewGuid().ToString("N")', saving)
        self.assertIn("File.Move(temporary, preserved);", saving)
        self.assertLess(
            saving.index("File.Move(temporary, preserved);"),
            saving.index("File.WriteAllText(temporary, json);"),
        )
        self.assertIn("LastWriteFailed = true;", saving)
        self.assertIn("File.Replace(temporary, target, target + \".bak\")", saving)
        self.assertIn("uncommittedBytes = File.ReadAllBytes(temporary)", playmode)
        self.assertIn('Path.GetFileName(temporary) + ".staged-*"', playmode)
        self.assertIn("File.ReadAllBytes(retainedStagedCheckpoint)", playmode)
        self.assertIn("Is.EqualTo(uncommittedBytes)", playmode)
        self.assertIn("File.Delete(retainedStagedCheckpoint)", playmode)
        self.assertIn("Loading must prefer the committed checkpoint", playmode)
        self.assertIn("uncommitted", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_unreadable_backup_survives_valid_primary_rotation(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        saving = store.split("public static bool TrySave(", 1)[1].split(
            "private static bool TryRead(", 1
        )[0]
        self.assertIn('string backup = target + ".bak";', saving)
        self.assertIn("File.Exists(target) && File.Exists(backup)", saving)
        self.assertIn("!TryRead(backup, out _)", saving)
        self.assertIn('backup + ".corrupt-" + Guid.NewGuid().ToString("N")', saving)
        self.assertIn("File.Move(backup, damaged);", saving)
        self.assertLess(
            saving.index("File.Move(backup, damaged);"),
            saving.index("File.WriteAllText(temporary, json);"),
        )
        self.assertIn('File.Replace(temporary, target, target + ".bak")', saving)
        self.assertIn("LastWriteFailed = true;", saving)
        self.assertIn("committedBeforeRotation = File.ReadAllBytes(primary)", playmode)
        self.assertIn("unreadableBackup = File.ReadAllBytes(backup)", playmode)
        self.assertIn('Path.GetFileName(backup) + ".corrupt-*"', playmode)
        self.assertIn("File.ReadAllBytes(retainedDamagedBackup)", playmode)
        self.assertIn("Is.EqualTo(unreadableBackup)", playmode)
        self.assertIn("Is.EqualTo(committedBeforeRotation)", playmode)
        self.assertIn("File.Delete(retainedDamagedBackup)", playmode)
        self.assertIn("previously valid primary checkpoint", playmode)
        self.assertIn("unreadable backup", guide.lower())
        self.assertIn("not executed", guide.lower())

    def test_live_primary_corruption_cannot_rotate_over_valid_backup(self):
        store = read("PrototypeSaveStore.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8"
        )
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        saving = store.split("public static bool TrySave(", 1)[1].split(
            "private static bool TryRead(", 1
        )[0]
        guard = "File.Exists(target) && !TryRead(target, out _)"
        self.assertIn(guard, saving)
        self.assertLess(saving.index(guard), saving.index("if (File.Exists(temporary))"))
        self.assertLess(saving.index(guard), saving.index("File.Replace(temporary, target"))
        self.assertIn("_preserveUnreadableSaves = true;", saving)
        self.assertIn("throw new InvalidDataException(", saving)
        self.assertIn("LastWriteFailed = true;", saving)
        self.assertIn("liveBrokenPrimary = File.ReadAllBytes(primary)", playmode)
        self.assertIn("lastGoodBackup = File.ReadAllBytes(backup)", playmode)
        self.assertIn("Is.EqualTo(liveBrokenPrimary)", playmode)
        self.assertIn("Is.EqualTo(lastGoodBackup)", playmode)
        self.assertIn("PrototypeSaveStore.SavingDisabled, Is.True", playmode)
        self.assertIn("retainedLiveDamagedPrimary", playmode)
        self.assertIn("File.Delete(retainedLiveDamagedPrimary)", playmode)
        self.assertIn("restoredAfterLiveDamage", playmode)
        self.assertIn("after a successful load", guide.lower())
        self.assertIn("not executed", guide.lower())

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

    def test_guard_alarm_and_custody_do_not_mask_checkpoint_failure(self):
        director = read("PrototypeDirector.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        # All three automatic outcome notices (laundering, alarm, custody)
        # must precede their own SaveProgress call, not overwrite the error.
        for message in (
            'Notice("Laundering complete. Leave the city',
            'Notice("ALARM RAISED! The guard spotted you.',
            'Notice("ARRESTED. Carried loot and dirty cash confiscated.',
        ):
            pos = director.index(message)
            after = director[pos : pos + 190]
            self.assertIn("SaveProgress();", after)
            self.assertLess(after.index("Notice("), after.index("SaveProgress();"))
        self.assertIn('Notice("Progress could not be saved: " + error)', director)

        # Real Unity Play Mode source forces a blocked atomic write, triggers
        # both physical guard outcomes and inspects the actual director notice.
        self.assertIn("Directory.CreateDirectory(temporary);", playmode)
        self.assertIn("update.Invoke(director, null);", playmode)
        self.assertIn("alarmed.AlarmRaised, Is.True", playmode)
        self.assertIn("alarmed.Phase, Is.EqualTo(HeistPhase.Arrested)", playmode)
        self.assertIn(
            "Alarm notice must not overwrite failed checkpoint details", playmode
        )
        self.assertIn(
            "Custody notice must not overwrite failed checkpoint details", playmode
        )
        self.assertIn("sessionField.SetValue(director, normalSession);", playmode)
        self.assertIn("motor.WarpTo(normalPosition);", playmode)
        self.assertIn("Failed alarm/custody saves must preserve", playmode)
        self.assertIn("alarm", guide.lower())
        self.assertIn("save", guide.lower())

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

    def test_custody_release_cannot_consume_the_pre_arrest_interaction_press(self):
        director = read("PrototypeDirector.cs")
        motor = read("ThirdPersonMotor.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")

        self.assertIn("bool arrestedThisFrame = false;", director)
        self.assertIn("_session.ArrestAfterAlarm();\n                arrestedThisFrame = true;", director)
        self.assertIn(
            "if (CanConsumeInteraction(_player.InteractPressed, arrestedThisFrame))",
            director,
        )
        self.assertIn(
            "private static bool CanConsumeInteraction(bool pressed, bool arrestedThisFrame)",
            director,
        )
        self.assertIn("=> pressed && !arrestedThisFrame;", director)
        self.assertLess(
            director.index("arrestedThisFrame = true;"),
            director.index("if (CanConsumeInteraction(_player.InteractPressed"),
        )
        self.assertIn("public bool InteractPressed =>", motor)
        self.assertIn("CanConsumeInteraction", playmode)
        self.assertIn("Arrest frame must not reuse an earlier press", playmode)
        self.assertIn("A fresh later-frame press must allow release from custody", playmode)
        self.assertIn("Guard capture must remain active until a new release interaction",
                      playmode)
        self.assertIn("Interact(StationAction.ReleaseCustody);", playmode)
        self.assertIn("new press", guide.lower())

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

    def test_next_heist_requires_civilian_city_return_in_core_and_unity(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(encoding="utf-8")
        tests = (ROOT / "game/Tests/Program.cs").read_text(encoding="utf-8")
        director = read("PrototypeDirector.cs")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        core_guide = (ROOT / "game/README.md").read_text(encoding="utf-8")

        reset = core.split("public void BeginAnotherHeist()", 1)[1].split(
            "public HeistSessionSnapshot ExportSnapshot()", 1
        )[0]
        self.assertIn("CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian", reset)
        self.assertIn("Phase == HeistPhase.Laundered", reset)
        self.assertIn("CounterCash == 0", reset)
        self.assertIn("_laundering == null && _loot.Count == 0", reset)
        self.assertIn("StationAction.Reset => city && civilian &&", director)
        self.assertIn("_session.Phase == HeistPhase.Laundered,", director)
        self.assertIn("CompletedHeistRequiresCivilianCityReturnBeforeReset", tests)
        self.assertIn("Throws<InvalidOperationException>(() => game.BeginAnotherHeist())",
                      tests)
        self.assertIn("game.LeaveCity();", tests)
        self.assertIn("game.EnterCity();", tests)
        self.assertIn("90L, game.CleanCash", tests)
        self.assertIn("10L, game.BankBalance", tests)
        self.assertIn("civilian", guide.lower())
        self.assertIn("city", core_guide.lower())

    def test_mask_requires_unfinished_idle_or_scouted_cycle(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(
            encoding="utf-8"
        )
        tests = (ROOT / "game/Tests/Program.cs").read_text(
            encoding="utf-8"
        )
        director = read("PrototypeDirector.cs")
        guide = (ROOT / "game/README.md").read_text(encoding="utf-8")

        masking = core.split("public void PutOnMask()", 1)[1].split(
            "public void StartHeist()", 1
        )[0]
        self.assertIn("CurrentZone == Zone.City", masking)
        self.assertIn("CurrentRole == PlayerRole.Civilian", masking)
        self.assertIn("!CarryingCourierParcel", masking)
        self.assertIn(
            "(Phase == HeistPhase.Idle || Phase == HeistPhase.Scouted)", masking
        )
        self.assertIn("StationAction.Mask => city && civilian &&", director)
        self.assertIn(
            "(_session.Phase == HeistPhase.Idle ||", director
        )
        self.assertIn("MaskRequiresFreshIdleOrScoutedCycle,", tests)
        self.assertIn(
            "Throws<InvalidOperationException>(() => game.PutOnMask())", tests
        )
        self.assertIn("resumed.PutOnMask()", tests)
        self.assertIn("game.BeginAnotherHeist();", tests)
        self.assertIn("scoutFirst.PutOnMask();", tests)
        self.assertIn("cannot mask", guide.lower())

    def test_desert_return_objective_and_next_heist_marker_are_city_gated(self):
        director = read("PrototypeDirector.cs")
        playmode = (UNITY / "Assets/Tests/PlayMode/PlayModeFlowTests.cs").read_text(
            encoding="utf-8")
        guide = (UNITY / "README.md").read_text(encoding="utf-8")
        core = (ROOT / "game/Core/HeistSession.cs").read_text(encoding="utf-8")

        self.assertIn("StationAction.Reset => city && civilian &&", director)
        self.assertIn("StationAction.EnterCity => !city,", director)
        self.assertIn("StationAction.OpenBank => city && civilian", director)
        self.assertIn("CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian", core)
        self.assertIn("if (_session.CurrentZone == Zone.Desert)", director)
        self.assertIn(
            'return "OUTSIDE CITY: use the purple RETURN TO CITY marker nearby',
            director,
        )
        self.assertLess(
            director.index("if (_session.CurrentZone == Zone.Desert)"),
            director.index("return _session.Phase switch"),
        )
        self.assertIn("Desert must never expose a next-heist marker", playmode)
        self.assertIn("Return marker must remain available in the desert", playmode)
        self.assertIn("City-only banking must not appear available", playmode)
        self.assertIn("Desert objective must guide players", playmode)
        self.assertIn("Civilian city return must reenable", playmode)
        self.assertIn("RETURN TO CITY", guide)
        self.assertIn("desert", guide.lower())

    def test_forged_desert_criminal_role_is_rejected_by_core_and_save_restore(self):
        core = (ROOT / "game/Core/HeistSession.cs").read_text(encoding="utf-8")
        tests = (ROOT / "game/Tests/Program.cs").read_text(encoding="utf-8")
        save = read("PrototypeSaveStore.cs")
        guide = (ROOT / "game/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "initialZone == Zone.Desert && initialRole == PlayerRole.Criminal",
            core,
        )
        self.assertIn("A criminal cannot start outside the city.", core)
        self.assertIn(
            "snapshot.Zone == Zone.Desert && snapshot.Role == PlayerRole.Criminal",
            core,
        )
        self.assertIn("Save contains an unreachable desert criminal role.", core)
        self.assertIn("CurrentRole = PlayerRole.Civilian;", core)
        self.assertIn("RejectsUnreachableDesertCriminalRoles,", tests)
        self.assertIn(
            "new HeistSession(Zone.Desert, PlayerRole.Criminal)", tests
        )
        self.assertIn("forged.Role = PlayerRole.Criminal;", tests)
        self.assertIn("Throws<ArgumentException>(() => HeistSession.FromSnapshot(forged))",
                      tests)
        self.assertIn("new HeistSession(Zone.Desert, PlayerRole.Police)", tests)
        self.assertIn("HeistSession.FromSnapshot(checkpoint)", save)
        self.assertIn("criminal", guide.lower())
        self.assertIn("desert", guide.lower())

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
        self.assertIn("Physics.CapsuleCastNonAlloc(", car)
        self.assertIn("travel.normalized, _pathHits", car)
        self.assertIn("travel.magnitude, ~0, QueryTriggerInteraction.Ignore", car)
        self.assertIn("if (swept == _pathHits.Length)", car)
        self.assertIn("!hit.transform.IsChildOf(transform)", car)

        # These assertions are authored real-Unity Play Mode test source;
        # hosted Python cannot claim collider execution or Windows acceptance.
        self.assertIn("Synthetic ankle-height exit obstruction", playmode)
        self.assertIn("Full character capsule must reject ankle-height exit blockers",
                      playmode)
        self.assertIn("motor.IsDriving && car.Occupied, Is.True", playmode)
        self.assertIn("Stationary car must allow a collision-clear exit", playmode)
        self.assertIn("ankle-height", guide)
        self.assertIn("Solid walls between the car and clear exit points must block egress",
                      playmode)
        self.assertIn("Rejected swept exit must preserve vehicle occupancy", playmode)
        self.assertIn("One blocked door must fall back to the unblocked side", playmode)
        self.assertIn("swept capsule", guide)

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
