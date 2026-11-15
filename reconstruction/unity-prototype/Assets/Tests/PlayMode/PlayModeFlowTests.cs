using System;
using System.Collections;
using System.IO;
using System.Reflection;
using NUnit.Framework;
using Rabron.Reconstruction;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.TestTools;
using UnityEngine.UIElements;

namespace Rabron.Prototype.Tests
{
    /// <summary>
    /// Must execute in a real Unity Play Mode process, NOT by Python/.NET CI.
    /// Does not emulate keyboard input or verify a packaged Windows player.
    /// </summary>
    [Category("RabronPlayMode")]
    public sealed class PlayModeFlowTests
    {
        private const BindingFlags PrivateInstance =
            BindingFlags.Instance | BindingFlags.NonPublic;

        // The physical money starts inactive when the counter holds zero.
        // Unity's active-only FindFirstObjectByType would miss it and fail
        // the entire heist acceptance suite before payout is exercised.
        private static CashPilePresenter FindCashPresenter()
        {
            var presenters = UnityEngine.Object.FindObjectsByType<CashPilePresenter>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            Assert.That(presenters.Length, Is.EqualTo(1),
                        "Expected one physical cash presenter, even when hidden");
            return presenters[0];
        }

        [Test]
        public void UnreadableCheckpointsMustSurviveLaterAutosaves()
        {
            // Never manipulate a developer's normal persistent demo save.
            // The Windows runner uses -runTests and a unique temp directory.
            if (!Array.Exists(Environment.GetCommandLineArgs(),
                arg => string.Equals(arg, "-runTests",
                                     StringComparison.OrdinalIgnoreCase)))
                Assert.Ignore("File corruption test runs only in isolated -runTests mode.");

            string primary = PrototypeSaveStore.SavePath;
            string backup = primary + ".bak";
            string temporary = primary + ".tmp";
            byte[] originalPrimary = File.Exists(primary) ? File.ReadAllBytes(primary) : null;
            byte[] originalBackup = File.Exists(backup) ? File.ReadAllBytes(backup) : null;
            byte[] originalTemporary = File.Exists(temporary) ? File.ReadAllBytes(temporary) : null;

            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(primary));
                File.WriteAllText(primary, "{broken primary checkpoint");
                File.WriteAllText(backup, "{broken backup checkpoint");
                byte[] brokenPrimary = File.ReadAllBytes(primary);
                byte[] brokenBackup = File.ReadAllBytes(backup);

                var fresh = PrototypeSaveStore.Load(out string message);
                Assert.That(message, Does.Contain("without saving"));
                Assert.That(fresh.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(PrototypeSaveStore.SavingDisabled, Is.True);
                var hud = UnityEngine.Object.FindFirstObjectByType<PrototypeHud>();
                Assert.That(hud, Is.Not.Null, "Actual runtime HUD must exist");
                hud.Render(fresh, "Recover progress", "", message,
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.True,
                            "Blocked autosave must have a persistent HUD warning");
                hud.Render(fresh, "Different activity", "", "",
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.True,
                            "Temporary notices must not clear the unsaved-session warning");
                Assert.That(PrototypeSaveStore.TrySave(fresh, out string error),
                            Is.False, "Auto-save must fail closed on corruption");
                Assert.That(error, Does.Contain("Autosave disabled"));
                Assert.That(File.ReadAllBytes(primary), Is.EqualTo(brokenPrimary),
                            "Unreadable primary must survive auto-save unchanged");
                Assert.That(File.ReadAllBytes(backup), Is.EqualTo(brokenBackup),
                            "Unreadable backup must survive auto-save unchanged");

                // Prove a genuinely valid fallback remains usable, and a
                // new Load clears the session-only write block.
                var knownGood = new HeistSession();
                File.WriteAllText(backup, JsonUtility.ToJson(knownGood.ExportSnapshot()));
                var recovered = PrototypeSaveStore.Load(out string recoveredMessage);
                Assert.That(recoveredMessage, Does.Contain("recovered"));
                Assert.That(recovered.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(PrototypeSaveStore.SavingDisabled, Is.False);
                hud.Render(recovered, "Delivery available", "", "",
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.False,
                            "Valid backup recovery must clear the persistent warning");
                Assert.That(PrototypeSaveStore.TrySave(recovered, out string saveError),
                            Is.True, saveError);

                // Reproduce a normal file write failure without touching an
                // actual player's save or relying on machine permissions:
                // an existing directory at the atomic .tmp path refuses
                // File.WriteAllText on Windows and Linux alike.
                byte[] previousCheckpoint = File.ReadAllBytes(primary);
                Assert.That(File.Exists(temporary) || Directory.Exists(temporary),
                            Is.False, "The isolated .tmp fixture must start clear");
                Directory.CreateDirectory(temporary);
                var pending = new HeistSession();
                pending.PickUpCourierParcel();
                Assert.That(PrototypeSaveStore.TrySave(pending, out string writeError),
                            Is.False, "Directory occupying .tmp must reject disk writes");
                Assert.That(writeError, Is.Not.Empty);
                Assert.That(PrototypeSaveStore.SavingDisabled, Is.False,
                            "Transient write errors must not trigger corruption lockout");
                Assert.That(PrototypeSaveStore.LastWriteFailed, Is.True);
                Assert.That(File.ReadAllBytes(primary), Is.EqualTo(previousCheckpoint),
                            "A failed write must preserve the prior valid checkpoint");

                hud.Render(pending, "Delivery started", "", "Save failed",
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.True,
                            "A failed disk write must retain a persistent warning");
                var warning = (Label)typeof(PrototypeHud)
                    .GetField("_saveWarning", PrivateInstance).GetValue(hud);
                Assert.That(warning.text, Does.Contain("LAST SAVE FAILED"));
                hud.Render(pending, "Delivery in progress", "", "Other notice",
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.True,
                            "A different notice must not hide unsaved progress");

                // Reuse this real rejected disk write in both production
                // guard outcomes. Earlier code overwrote the SaveProgress
                // error by issuing ALARM/ARRESTED notices afterward.
                var director = UnityEngine.Object.FindFirstObjectByType<PrototypeDirector>();
                var motor = UnityEngine.Object.FindFirstObjectByType<ThirdPersonMotor>();
                Assert.That(director, Is.Not.Null);
                Assert.That(motor, Is.Not.Null);
                var sessionField = typeof(PrototypeDirector).GetField("_session", PrivateInstance);
                var noticeField = typeof(PrototypeDirector).GetField("_notice", PrivateInstance);
                var untilField = typeof(PrototypeDirector).GetField("_noticeUntil", PrivateInstance);
                var update = typeof(PrototypeDirector).GetMethod("Update", PrivateInstance);
                Assert.That(sessionField, Is.Not.Null);
                Assert.That(noticeField, Is.Not.Null);
                Assert.That(untilField, Is.Not.Null);
                Assert.That(update, Is.Not.Null);
                var normalSession = (HeistSession)sessionField.GetValue(director);
                var normalPosition = motor.transform.position;
                var normalRotation = motor.transform.rotation;
                string normalNotice = (string)noticeField.GetValue(director);
                float normalNoticeUntil = (float)untilField.GetValue(director);
                try
                {
                    var alarmed = new HeistSession();
                    alarmed.Scout();
                    alarmed.PutOnMask();
                    alarmed.StartHeist();
                    sessionField.SetValue(director, alarmed);

                    // Visible to the guard but too far away for custody.
                    motor.WarpTo(new Vector3(0f, 0.12f, 27f));
                    Physics.SyncTransforms();
                    update.Invoke(director, null);
                    Assert.That(alarmed.AlarmRaised, Is.True,
                                "The production guard must trigger an alarm");
                    Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Robbing));
                    Assert.That((string)noticeField.GetValue(director),
                                Does.StartWith("Progress could not be saved:"),
                                "Alarm notice must not overwrite failed checkpoint details");

                    // Move into real guard capture range on the next update.
                    motor.WarpTo(new Vector3(0f, 0.12f, 31.5f));
                    Physics.SyncTransforms();
                    update.Invoke(director, null);
                    Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Arrested),
                                "The production guard must apply the custody outcome");
                    Assert.That((string)noticeField.GetValue(director),
                                Does.StartWith("Progress could not be saved:"),
                                "Custody notice must not overwrite failed checkpoint details");
                    Assert.That(PrototypeSaveStore.LastWriteFailed, Is.True);
                    Assert.That(File.ReadAllBytes(primary), Is.EqualTo(previousCheckpoint),
                                "Failed alarm/custody saves must preserve the prior checkpoint");
                }
                finally
                {
                    sessionField.SetValue(director, normalSession);
                    motor.WarpTo(normalPosition);
                    motor.transform.rotation = normalRotation;
                    noticeField.SetValue(director, normalNotice);
                    untilField.SetValue(director, normalNoticeUntil);
                    Physics.SyncTransforms();
                }

                Directory.Delete(temporary);
                Assert.That(PrototypeSaveStore.TrySave(pending, out string retryError),
                            Is.True, retryError);
                Assert.That(PrototypeSaveStore.LastWriteFailed, Is.False,
                            "Only a successful write clears the transient warning");
                hud.Render(pending, "Delivery in progress", "", "",
                           PrototypeSaveStore.SavingDisabled,
                           PrototypeSaveStore.LastWriteFailed);
                Assert.That(hud.SaveWarningVisible, Is.False,
                            "A confirmed checkpoint should clear the write-error banner");
                Assert.That(PrototypeSaveStore.Load(out _).CarryingCourierParcel, Is.True,
                            "Successful retry must durably save the pending courier parcel");
            }
            finally
            {
                // .tmp can be a deliberately blocking directory in this test.
                if (Directory.Exists(temporary))
                    Directory.Delete(temporary, recursive: true);
                Restore(primary, originalPrimary);
                Restore(backup, originalBackup);
                Restore(temporary, originalTemporary);
                // Do not leave a global write block affecting other tests.
                PrototypeSaveStore.Load(out _);
            }

            void Restore(string path, byte[] bytes)
            {
                if (bytes == null)
                {
                    if (File.Exists(path))
                        File.Delete(path);
                }
                else
                    File.WriteAllBytes(path, bytes);
            }
        }

        [UnityTest]
        public IEnumerator SceneBootCreatesRuntimePlayerCameraHudAndStations()
        {
            yield return null; // Let Unity run scene-load bootstrap + Awake/Start.

            var director = UnityEngine.Object.FindFirstObjectByType<PrototypeDirector>();
            Assert.That(director, Is.Not.Null,
                        "PrototypeBoot did not instantiate the runtime director");

            // The -runTests process must not reuse a previous run's save or
            // ever read the developer's normal Editor/Windows demo checkpoint.
            // Ordinary GUI play mode remains on the existing persistent path.
            if (Array.Exists(Environment.GetCommandLineArgs(),
                arg => string.Equals(arg, "-runTests",
                                     StringComparison.OrdinalIgnoreCase)))
            {
                string testRoot = Path.GetFullPath(Path.Combine(
                    Application.temporaryCachePath, "rabron-playmode-tests"))
                    + Path.DirectorySeparatorChar;
                string savePath = Path.GetFullPath(PrototypeSaveStore.SavePath);
                Assert.That(savePath.StartsWith(testRoot,
                    StringComparison.OrdinalIgnoreCase), Is.True,
                    "Batch Unity tests must use the isolated temporary cache");
                string invocationDirectory = Path.GetFileName(
                    Path.GetDirectoryName(savePath));
                Assert.That(Guid.TryParseExact(invocationDirectory, "N", out _),
                            Is.True, "Batch save directory must be unique to the run");
                Assert.That(Path.GetFullPath(PrototypeSaveStore.SavePath),
                            Is.EqualTo(savePath),
                            "Batch save path must stay stable within one run");
                Assert.That(savePath, Is.Not.EqualTo(Path.GetFullPath(
                    Path.Combine(Application.persistentDataPath,
                                 "rabron-prototype-v1.json"))),
                    "Batch Unity tests must never use normal player progress");
            }

            var motor = UnityEngine.Object.FindFirstObjectByType<ThirdPersonMotor>();
            var camera = UnityEngine.Object.FindFirstObjectByType<Camera>();
            var hud = UnityEngine.Object.FindFirstObjectByType<PrototypeHud>();
            var cash = FindCashPresenter();
            var guard = UnityEngine.Object.FindFirstObjectByType<GuardSensor>();
            var car = UnityEngine.Object.FindFirstObjectByType<PrototypeVehicle>();
            var stations = UnityEngine.Object.FindObjectsByType<InteractionMarker>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);

            Assert.That(motor, Is.Not.Null, "No player controller");
            Assert.That(motor.GetComponent<CharacterController>(), Is.Not.Null);
            // Check the real Input System action, not a hard-coded key label.
            var jumpField = typeof(ThirdPersonMotor).GetField("_jump", PrivateInstance);
            Assert.That(jumpField, Is.Not.Null);
            var jump = (InputAction)jumpField.GetValue(motor);
            Assert.That(jump, Is.Not.Null);
            Assert.That(jump.enabled, Is.True);
            bool keyboardJump = false;
            bool gamepadJump = false;
            foreach (var binding in jump.bindings)
            {
                keyboardJump |= binding.effectivePath == "<Keyboard>/space";
                gamepadJump |= binding.effectivePath == "<Gamepad>/buttonNorth";
            }
            Assert.That(keyboardJump && gamepadJump, Is.True,
                        "Jump requires dedicated Space and north-face bindings");

            // Deterministic motor integration tests do not emulate real
            // keyboard input, physics collision timing or a packaged player.
            var flags = PrivateInstance | BindingFlags.Static;
            var integrate = typeof(ThirdPersonMotor).GetMethod("IntegrateVertical", flags);
            var ceiling = typeof(ThirdPersonMotor).GetMethod("ResolveCeiling", flags);
            Assert.That(integrate, Is.Not.Null);
            Assert.That(ceiling, Is.Not.Null);
            float launched = (float)integrate.Invoke(null,
                new object[] { 0f, true, true, 0f });
            Assert.That(launched, Is.GreaterThan(0f), "Grounded jump must launch upward");
            float noAutoJump = (float)integrate.Invoke(null,
                new object[] { launched, true, false, 0f });
            Assert.That(noAutoJump, Is.LessThan(0f),
                        "Ground contact without a new press must not relaunch");
            float airborne = (float)integrate.Invoke(null,
                new object[] { 0f, false, true, 0.1f });
            Assert.That(airborne, Is.LessThan(0f), "No airborne double-jump");
            Assert.That((float)ceiling.Invoke(null,
                new object[] { launched, CollisionFlags.Above }), Is.EqualTo(0f),
                "Ceiling collision must cancel ascent");
            Assert.That((float)ceiling.Invoke(null,
                new object[] { airborne, CollisionFlags.Above }), Is.EqualTo(airborne),
                "Ceiling contact must preserve falling speed");

            // Escape unlocks the desktop pointer but must not disable
            // controller camera look. Exercise production input composition
            // without requiring a synthetic physical gamepad in this test.
            var composeLook = typeof(ThirdPersonMotor).GetMethod("ComposeLook", flags);
            Assert.That(composeLook, Is.Not.Null, "Gamepad/mouse look composition missing");
            var mouseDelta = new Vector2(80f, -60f);
            var rightStick = new Vector2(0.5f, -0.25f);
            var unlockedStick = (Vector2)composeLook.Invoke(null,
                new object[] { mouseDelta, rightStick, false, 0.02f });
            Assert.That(Vector2.Distance(unlockedStick, new Vector2(1.2f, -0.6f)),
                        Is.LessThan(0.0001f),
                        "Right stick must still rotate the camera with released cursor");
            var unlockedMouseOnly = (Vector2)composeLook.Invoke(null,
                new object[] { mouseDelta, Vector2.zero, false, 0.02f });
            Assert.That(unlockedMouseOnly, Is.EqualTo(Vector2.zero),
                        "Unlocked mouse motion must not steer the camera");
            var lockedCombined = (Vector2)composeLook.Invoke(null,
                new object[] { mouseDelta, rightStick, true, 0.02f });
            Assert.That(Vector2.Distance(lockedCombined,
                                        new Vector2(10.8f, -7.8f)),
                        Is.LessThan(0.0001f),
                        "Locked cursor must retain both mouse and gamepad look");
            var unlockedWithoutMouse = (Vector2)composeLook.Invoke(null,
                new object[] { Vector2.zero, rightStick, false, 0.02f });
            Assert.That(unlockedWithoutMouse, Is.EqualTo(unlockedStick),
                        "Gamepad look must not require a connected mouse");

            // Verify the real hold-to-crouch action and actual capsule
            // geometry without injecting a synthetic gamepad or keypress.
            var crouchField = typeof(ThirdPersonMotor).GetField("_crouch", PrivateInstance);
            Assert.That(crouchField, Is.Not.Null);
            var crouchInput = (InputAction)crouchField.GetValue(motor);
            Assert.That(crouchInput, Is.Not.Null);
            Assert.That(crouchInput.enabled, Is.True);
            bool keyboardCrouch = false;
            bool gamepadCrouch = false;
            foreach (var binding in crouchInput.bindings)
            {
                keyboardCrouch |= binding.effectivePath == "<Keyboard>/leftCtrl";
                gamepadCrouch |= binding.effectivePath == "<Gamepad>/rightStickPress";
            }
            Assert.That(keyboardCrouch && gamepadCrouch, Is.True,
                        "Crouch must use dedicated Ctrl/right-stick-click bindings");

            var setCrouch = typeof(ThirdPersonMotor).GetMethod(
                "UpdateCrouch", PrivateInstance);
            var canStand = typeof(ThirdPersonMotor).GetMethod(
                "CanStand", PrivateInstance);
            Assert.That(setCrouch, Is.Not.Null);
            Assert.That(canStand, Is.Not.Null);
            var playerCapsule = motor.GetComponent<CharacterController>();
            var playerMesh = motor.transform.Find("Player mesh");
            Assert.That(playerMesh, Is.Not.Null);
            float fullHeight = playerCapsule.height;
            float fullStep = playerCapsule.stepOffset;
            float footY = playerCapsule.center.y - fullHeight * 0.5f;
            Vector3 meshScale = playerMesh.localScale;
            Vector3 meshPosition = playerMesh.localPosition;
            var ceilingObstacle = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                setCrouch.Invoke(motor, new object[] { true });
                Assert.That(motor.IsCrouched, Is.True);
                Assert.That(playerCapsule.height, Is.LessThan(fullHeight),
                            "Crouch must shrink the real physical capsule");
                Assert.That(playerCapsule.stepOffset, Is.LessThan(fullStep),
                            "Crouch must reduce step climbing");
                Assert.That(playerCapsule.center.y - playerCapsule.height * 0.5f,
                            Is.EqualTo(footY).Within(0.001f),
                            "Crouching must not lift or sink the player's feet");
                Assert.That(playerMesh.localScale.y, Is.LessThan(meshScale.y),
                            "Visual capsule must match the crouched collision height");

                ceilingObstacle.name = "Temporary crouch headroom test";
                ceilingObstacle.transform.position =
                    motor.transform.position + Vector3.up * 1.53f;
                ceilingObstacle.transform.localScale = new Vector3(1.8f, 0.3f, 1.8f);
                Physics.SyncTransforms();
                Assert.That((bool)canStand.Invoke(motor, null), Is.False,
                            "Overhead solid geometry must prevent standing");
                setCrouch.Invoke(motor, new object[] { false });
                Assert.That(motor.IsCrouched, Is.True,
                            "Releasing crouch under a ceiling must remain crouched");
                Assert.That(playerCapsule.height, Is.LessThan(fullHeight),
                            "Blocked stand must not resize the capsule through a ceiling");

                ceilingObstacle.transform.position += Vector3.right * 20f;
                Physics.SyncTransforms();
                Assert.That((bool)canStand.Invoke(motor, null), Is.True,
                            "Clear overhead volume must permit standing");
                setCrouch.Invoke(motor, new object[] { false });
                Assert.That(motor.IsCrouched, Is.False);
                Assert.That(playerCapsule.height, Is.EqualTo(fullHeight).Within(0.001f));
                Assert.That(playerCapsule.stepOffset, Is.EqualTo(fullStep).Within(0.001f));
                Assert.That(playerMesh.localScale, Is.EqualTo(meshScale));
                Assert.That(playerMesh.localPosition, Is.EqualTo(meshPosition));
            }
            finally
            {
                ceilingObstacle.transform.position += Vector3.right * 20f;
                Physics.SyncTransforms();
                setCrouch.Invoke(motor, new object[] { false });
                UnityEngine.Object.Destroy(ceilingObstacle);
            }

            Assert.That(camera, Is.Not.Null, "No runtime follow camera");
            Assert.That(camera.isActiveAndEnabled, Is.True);
            Assert.That(hud, Is.Not.Null, "No runtime HUD");
            Assert.That(hud.GetComponent<UIDocument>().rootVisualElement.childCount,
                        Is.GreaterThan(0), "HUD labels were not attached");

            // Original procedural feedback must be part of the runtime scene.
            // This checks sound data without claiming human audible playback.
            var feedback = director.GetComponent<PrototypeAudioFeedback>();
            Assert.That(feedback, Is.Not.Null, "No original action audio presenter");
            var output = feedback.GetComponent<AudioSource>();
            Assert.That(output, Is.Not.Null);
            Assert.That(output.playOnAwake || output.loop, Is.False,
                        "UI feedback must only play bounded one-shot cues");
            foreach (string name in new[] { "_success", "_rejected", "_alarm" })
            {
                var clipField = typeof(PrototypeAudioFeedback).GetField(name, PrivateInstance);
                Assert.That(clipField, Is.Not.Null);
                var clip = (AudioClip)clipField.GetValue(feedback);
                Assert.That(clip, Is.Not.Null, "Missing generated audio cue " + name);
                Assert.That(clip.samples, Is.GreaterThan(1024));
                Assert.That(clip.channels, Is.EqualTo(1));
                Assert.That(clip.frequency, Is.EqualTo(24000));
                var samples = new float[512];
                Assert.That(clip.GetData(samples, clip.samples / 2 - 256), Is.True);
                float energy = 0f;
                foreach (float sample in samples)
                    energy += Mathf.Abs(sample);
                Assert.That(energy, Is.GreaterThan(0.1f),
                            "Generated cue must contain non-silent PCM samples");
            }

            Assert.That(guard, Is.Not.Null, "No guard sensor in runtime scene");
            Assert.That(cash, Is.Not.Null, "No collectible physical counter money");
            Assert.That(stations.Length, Is.EqualTo(21));
            Assert.That(car, Is.Not.Null, "No original practice car");
            Assert.That(car.GetComponent<CharacterController>(), Is.Not.Null);
            Assert.That(car.Occupied, Is.False);
            var parcel = motor.GetComponentInChildren<CourierParcelPresenter>(true);
            Assert.That(parcel, Is.Not.Null, "No physical courier cargo visual");
            Assert.That(parcel.GetComponent<Collider>().enabled, Is.False,
                        "Courier visual must not obstruct movement or interactions");
            var saved = (HeistSession)typeof(PrototypeDirector)
                .GetField("_session", PrivateInstance).GetValue(director);
            Assert.That(cash.IsVisible, Is.EqualTo(saved.CounterCash > 0L),
                        "Physical counter cash visibility must match loaded checkpoint");
            Assert.That(parcel.IsVisible, Is.EqualTo(saved.CarryingCourierParcel));
            Assert.That(Application.isPlaying, Is.True);
        }

        [UnityTest]
        public IEnumerator HeistMarkersDriveFullLoopAndPhysicalCounterMoney()
        {
            yield return null;

            var director = UnityEngine.Object.FindFirstObjectByType<PrototypeDirector>();
            Assert.That(director, Is.Not.Null);

            FieldInfo field = typeof(PrototypeDirector).GetField("_session",
                PrivateInstance);
            MethodInfo perform = typeof(PrototypeDirector).GetMethod("Perform",
                PrivateInstance);
            MethodInfo update = typeof(PrototypeDirector).GetMethod("Update",
                PrivateInstance);
            Assert.That(field, Is.Not.Null, "Director state integration changed");
            Assert.That(perform, Is.Not.Null, "Director action dispatcher missing");
            Assert.That(update, Is.Not.Null, "Director frame integration missing");

            var original = (HeistSession)field.GetValue(director);
            var motor = UnityEngine.Object.FindFirstObjectByType<ThirdPersonMotor>();
            Assert.That(motor, Is.Not.Null);
            var originalPosition = motor.transform.position;
            var originalRotation = motor.transform.rotation;
            var car = UnityEngine.Object.FindFirstObjectByType<PrototypeVehicle>();
            Assert.That(car, Is.Not.Null);
            var carPosition = car.transform.position;
            var carRotation = car.transform.rotation;
            var exitBlockers = new GameObject[2];
            var simulated = new HeistSession();
            var cash = FindCashPresenter();
            Assert.That(cash, Is.Not.Null);
            var parcels = UnityEngine.Object.FindObjectsByType<CourierParcelPresenter>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            Assert.That(parcels.Length, Is.EqualTo(1));
            var parcel = parcels[0];
            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();

            // Direct dispatcher calls deliberately avoid modifying existing
            // save files or injecting synthetic keyboard events. Manual input,
            // collision-driven reachability and packaged EXE still need testing.
            try
            {
                // Exercise discovery while the actual cash actor is inactive.
                // Do not activate it to make the test pass.
                cash.SetAmount(0);
                Assert.That(cash.IsVisible, Is.False);
                Assert.That(FindCashPresenter(), Is.SameAs(cash),
                            "Hidden counter money must remain discoverable");

                // Board and leave the actual collider-backed car through
                // production station dispatch, without changing money or role.
                var driver = new HeistSession();
                field.SetValue(director, driver);
                MethodInfo availableVehicle = typeof(PrototypeDirector).GetMethod(
                    "Available", PrivateInstance);
                Assert.That(availableVehicle, Is.Not.Null);
                Assert.That((bool)availableVehicle.Invoke(director,
                    new object[] { StationAction.VehicleEnter }), Is.True);
                Interact(StationAction.VehicleEnter);
                Assert.That(motor.IsDriving && car.Occupied, Is.True);
                // Director and motor Update order is unspecified. The E/A
                // press that boarded this frame may not also exit this frame.
                var boardFrameField = typeof(ThirdPersonMotor).GetField(
                    "_boardedVehicleFrame", PrivateInstance);
                var exitPredicate = typeof(ThirdPersonMotor).GetMethod(
                    "ExitPressAfterBoard", BindingFlags.NonPublic | BindingFlags.Static);
                Assert.That(boardFrameField, Is.Not.Null);
                Assert.That(exitPredicate, Is.Not.Null);
                int boardFrame = (int)boardFrameField.GetValue(motor);
                Assert.That(boardFrame, Is.EqualTo(Time.frameCount));
                Assert.That((bool)exitPredicate.Invoke(null,
                    new object[] { boardFrame, boardFrame, true }), Is.False,
                    "Boarding press must never immediately exit the car");
                Assert.That((bool)exitPredicate.Invoke(null,
                    new object[] { boardFrame, boardFrame + 1, false }), Is.False,
                    "A later frame without a fresh press must not exit");
                Assert.That((bool)exitPredicate.Invoke(null,
                    new object[] { boardFrame, boardFrame + 1, true }), Is.True,
                    "A fresh later-frame press must allow a stopped-car exit");
                Assert.That(motor.IsDriving && car.Occupied, Is.True);
                var onFootVisual = motor.transform.Find("Player mesh").GetComponent<Renderer>();
                Assert.That(onFootVisual.enabled, Is.False,
                            "Seated on-foot mesh must not obstruct the car camera");
                Assert.That(motor.GetComponent<CharacterController>().enabled, Is.False);
                Assert.That((bool)availableVehicle.Invoke(director,
                    new object[] { StationAction.VehicleEnter }), Is.False);

                // Exercise the real motor's look routing without injecting
                // device input: orbiting a moving car cannot steer the car or
                // rotate the hidden walking avatar.
                var applyLook = typeof(ThirdPersonMotor).GetMethod(
                    "ApplyLookDelta", PrivateInstance);
                var drivingYaw = typeof(ThirdPersonMotor).GetField(
                    "_drivingLookYaw", PrivateInstance);
                var pitchField = typeof(ThirdPersonMotor).GetField(
                    "_pitch", PrivateInstance);
                Assert.That(applyLook, Is.Not.Null);
                Assert.That(drivingYaw, Is.Not.Null);
                Assert.That(pitchField, Is.Not.Null);
                float carHeading = car.transform.eulerAngles.y;
                float playerHeading = motor.transform.eulerAngles.y;
                float originalPitch = (float)pitchField.GetValue(motor);
                applyLook.Invoke(motor, new object[] { new Vector2(42f, 10f) });
                Assert.That((float)drivingYaw.GetValue(motor),
                            Is.EqualTo(42f).Within(0.001f),
                            "Driver right-stick/mouse look must orbit the camera");
                Assert.That((float)pitchField.GetValue(motor),
                            Is.EqualTo(Mathf.Clamp(originalPitch - 10f, -45f, 70f))
                              .Within(0.001f));
                applyLook.Invoke(motor, new object[] { new Vector2(360f, 0f) });
                Assert.That((float)drivingYaw.GetValue(motor),
                            Is.EqualTo(42f).Within(0.001f),
                            "Driver look accumulation must wrap without drifting");
                Assert.That(car.transform.eulerAngles.y,
                            Is.EqualTo(carHeading).Within(0.001f),
                            "Camera orbit must not steer the car");
                Assert.That(motor.transform.eulerAngles.y,
                            Is.EqualTo(playerHeading).Within(0.001f),
                            "Camera orbit must not rotate the seated avatar");

                car.Drive(new Vector2(0f, 1f), false, 0.1f);
                Assert.That(car.Speed, Is.GreaterThan(0f),
                            "Throttle must accelerate the vehicle");
                Assert.That(motor.TryExitVehicle(), Is.False,
                            "Moving car must prevent an unsafe exit");
                car.Drive(Vector2.zero, true, 0.3f);
                Assert.That(car.Speed, Is.EqualTo(0f).Within(0.001f),
                            "Brake must stop the car");

                // These short solid obstacles reach the avatar's feet but
                // end below the old +0.20m probe's first collision surface.
                // Two blocked sides must refuse exit without altering role,
                // carried money, vehicle occupancy or walking collision.
                for (int side = 0; side < exitBlockers.Length; side++)
                {
                    var obstacle = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    obstacle.name = "Synthetic ankle-height exit obstruction";
                    obstacle.transform.position = car.transform.position +
                        car.transform.right * (side == 0 ? 2.3f : -2.3f) +
                        Vector3.up * 0.19f;
                    obstacle.transform.localScale = new Vector3(0.7f, 0.18f, 0.7f);
                    exitBlockers[side] = obstacle;
                }
                Physics.SyncTransforms();
                Assert.That(motor.TryExitVehicle(), Is.False,
                    "Full character capsule must reject ankle-height exit blockers");
                Assert.That(motor.IsDriving && car.Occupied, Is.True);
                Assert.That(motor.GetComponent<CharacterController>().enabled, Is.False);
                Assert.That(driver.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(driver.CleanCash, Is.EqualTo(0L));
                foreach (var obstacle in exitBlockers)
                    obstacle.GetComponent<Collider>().enabled = false;
                Physics.SyncTransforms();

                // Reproduce an on-foot heading mismatch before the safe exit.
                // Returning to walking should inherit the car's heading,
                // rather than snapping to an unrelated pre-drive view.
                motor.transform.rotation = Quaternion.Euler(0f, 130f, 0f);
                Physics.SyncTransforms();
                Assert.That(motor.TryExitVehicle(), Is.True,
                            "Stationary car must allow a collision-clear exit");
                Assert.That(motor.IsDriving || car.Occupied, Is.False);
                Assert.That(motor.GetComponent<CharacterController>().enabled, Is.True);
                Assert.That(onFootVisual.enabled, Is.True,
                            "Leaving the car must restore the walking avatar");
                Assert.That((float)drivingYaw.GetValue(motor),
                            Is.EqualTo(0f).Within(0.001f),
                            "Vehicle orbit must reset after a safe exit");
                Assert.That(Quaternion.Angle(motor.transform.rotation,
                    Quaternion.Euler(0f, car.transform.eulerAngles.y, 0f)),
                    Is.LessThan(0.001f),
                    "On-foot camera heading should match the parked car");
                Assert.That(driver.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(driver.CurrentRole, Is.EqualTo(PlayerRole.Civilian));
                Assert.That(driver.CleanCash, Is.EqualTo(0L));
                Assert.That(driver.DirtyCash, Is.EqualTo(0L));
                Assert.That(driver.BankBalance, Is.EqualTo(0L));

                // The lawful civilian path must be actionable through the
                // production world marker dispatcher, without a robbery.
                var courier = new HeistSession();
                field.SetValue(director, courier);
                Interact(StationAction.CourierPickup);
                update.Invoke(director, null);
                Assert.That(courier.CarryingCourierParcel, Is.True);
                Assert.That(parcel.IsVisible, Is.True,
                            "Carried parcel should appear on the player");

                Interact(StationAction.CourierCancel);
                update.Invoke(director, null);
                Assert.That(courier.CarryingCourierParcel, Is.False);
                Assert.That(courier.CleanCash, Is.EqualTo(0L),
                            "Returning a parcel must never pay currency");
                Assert.That(parcel.IsVisible, Is.False,
                            "Returned parcel should disappear from player");

                Interact(StationAction.CourierPickup);
                courier = HeistSession.FromSnapshot(courier.ExportSnapshot());
                field.SetValue(director, courier);
                update.Invoke(director, null);
                Assert.That(parcel.IsVisible, Is.True,
                            "Parcel visibility must restore from saved cargo state");
                Interact(StationAction.CourierDropoff);
                update.Invoke(director, null);
                Assert.That(courier.CarryingCourierParcel, Is.False);
                Assert.That(parcel.IsVisible, Is.False);
                Assert.That(courier.CleanCash, Is.GreaterThan(0L));
                Assert.That(courier.DirtyCash, Is.EqualTo(0L));
                Interact(StationAction.OpenBank);
                Interact(StationAction.Deposit);
                Assert.That(courier.BankBalance, Is.GreaterThan(0L));

                // Recover an empty-handed robbery using the production
                // station dispatcher and its real availability predicate.
                var empty = new HeistSession();
                field.SetValue(director, empty);
                Interact(StationAction.Scout);
                Interact(StationAction.Mask);
                Interact(StationAction.BeginRobbery);
                MethodInfo available = typeof(PrototypeDirector).GetMethod(
                    "Available", PrivateInstance);
                Assert.That(available, Is.Not.Null);
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.WithdrawEmptyHanded }), Is.True);
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.Escape }), Is.False);
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.ExitCity }), Is.False,
                    "An active robbery must not expose desert exit");
                Interact(StationAction.WithdrawEmptyHanded);
                Assert.That(empty.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(empty.CurrentRole, Is.EqualTo(PlayerRole.Civilian));
                Assert.That(empty.CounterCash, Is.EqualTo(0L));
                Assert.That(empty.DirtyCash, Is.EqualTo(0L));
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.WithdrawEmptyHanded }), Is.False);
                Assert.That(HeistSession.FromSnapshot(empty.ExportSnapshot()).Phase,
                            Is.EqualTo(HeistPhase.Idle));

                // Test actual guard sight/proximity -> core confiscation,
                // then dispatch through the real custody release station.
                var alarmed = new HeistSession();
                alarmed.Scout();
                alarmed.PutOnMask();
                alarmed.StartHeist();
                alarmed.TakeLoot("arrest-test-loot");
                alarmed.RaiseAlarm();
                field.SetValue(director, alarmed);
                var activeGuard = UnityEngine.Object.FindFirstObjectByType<GuardSensor>();
                Assert.That(activeGuard, Is.Not.Null);
                // The procedural guard mesh has a trigger collider. A player
                // may physically overlap the guard; zero horizontal distance
                // must never be a blind spot that bypasses a raised alarm.
                motor.WarpTo(activeGuard.transform.position);
                Physics.SyncTransforms();
                Assert.That(activeGuard.CanSee(motor.transform), Is.True,
                            "Guard must detect a player at its exact position");
                update.Invoke(director, null);
                Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Arrested),
                            "Overlapping guard must cause confiscation after alarm");
                Assert.That(alarmed.Loot.Count, Is.EqualTo(0));
                Assert.That(alarmed.DirtyCash, Is.EqualTo(0L));
                Assert.That(alarmed.CurrentRole, Is.EqualTo(PlayerRole.Criminal));
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.ReleaseCustody }), Is.True,
                    "Custody release marker should be ready after an actual arrest");

                // The production update must ignore a pre-arrest E/A press
                // on the capture frame, even though the release pillar has
                // become available beside the teleported actor.
                var canConsume = typeof(PrototypeDirector).GetMethod(
                    "CanConsumeInteraction", BindingFlags.Static | BindingFlags.NonPublic);
                Assert.That(canConsume, Is.Not.Null);
                Assert.That((bool)canConsume.Invoke(null, new object[] { true, true }),
                            Is.False,
                            "Arrest frame must not reuse an earlier press to release custody");
                Assert.That((bool)canConsume.Invoke(null, new object[] { false, true }),
                            Is.False, "No button press must remain inert during capture");
                Assert.That((bool)canConsume.Invoke(null, new object[] { false, false }),
                            Is.False, "No press on later frames must remain inert");
                Assert.That((bool)canConsume.Invoke(null, new object[] { true, false }),
                            Is.True,
                            "A fresh later-frame press must allow release from custody");
                Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Arrested),
                            "Guard capture must remain active until a new release interaction");

                Interact(StationAction.ReleaseCustody);
                Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(alarmed.CurrentRole, Is.EqualTo(PlayerRole.Civilian));
                Assert.That(alarmed.AlarmRaised, Is.False);

                field.SetValue(director, simulated);
                Interact(StationAction.Scout);
                Interact(StationAction.Mask);
                Interact(StationAction.BeginRobbery);
                Interact(StationAction.ControlStaff);
                Interact(StationAction.Artwork);
                Interact(StationAction.Watch);
                Assert.That(simulated.Loot.Count, Is.EqualTo(2));

                Interact(StationAction.Escape);
                Interact(StationAction.Fence);
                Assert.That(simulated.CounterCash, Is.GreaterThan(0));
                Assert.That(simulated.DirtyCash, Is.EqualTo(0L));

                // Exercise the REAL director Update/HUD/cash presenter path.
                update.Invoke(director, null);
                Assert.That(cash.IsVisible, Is.True,
                            "Sold currency must be on the physical counter");

                Interact(StationAction.CollectCash);
                update.Invoke(director, null);
                Assert.That(simulated.CounterCash, Is.EqualTo(0L));
                Assert.That(simulated.DirtyCash, Is.GreaterThan(0L));
                Assert.That(cash.IsVisible, Is.False,
                            "Cash must disappear once explicitly collected");

                Interact(StationAction.Launder);
                Assert.That(simulated.Phase, Is.EqualTo(HeistPhase.Laundering));
                Assert.That(simulated.LaunderingReadyAt, Is.Not.Null);
                // The portable core validates exact deadlines separately.
                simulated.CompleteLaundering(
                    simulated.LaunderingReadyAt.GetValueOrDefault());
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.ExitCity }), Is.True,
                    "A completed heist must allow lawful city departure");
                Interact(StationAction.ExitCity);
                Assert.That(simulated.CurrentRole, Is.EqualTo(PlayerRole.Civilian));
                Assert.That(simulated.CurrentZone, Is.EqualTo(Zone.Desert));
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.EnterCity }), Is.True,
                    "Return marker must remain available in the desert");
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.Reset }), Is.False,
                    "Desert must never expose a next-heist marker");
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.OpenBank }), Is.False,
                    "City-only banking must not appear available in the desert");
                var objectiveMethod = typeof(PrototypeDirector).GetMethod(
                    "Objective", PrivateInstance);
                Assert.That(objectiveMethod, Is.Not.Null);
                Assert.That((string)objectiveMethod.Invoke(director,
                    new object[] { now }), Does.Contain("RETURN TO CITY"),
                    "Desert objective must guide players to the nearby return marker");

                Interact(StationAction.EnterCity);
                Assert.That(simulated.CurrentZone, Is.EqualTo(Zone.City));
                Assert.That((bool)available.Invoke(director,
                    new object[] { StationAction.Reset }), Is.True,
                    "Civilian city return must reenable the next-heist marker");
                Interact(StationAction.OpenBank);
                Interact(StationAction.Deposit);
                Assert.That(simulated.BankBalance, Is.GreaterThan(0L));

                long retainedBank = simulated.BankBalance;
                Interact(StationAction.Reset);
                Assert.That(simulated.Phase, Is.EqualTo(HeistPhase.Idle));
                Assert.That(simulated.BankBalance, Is.EqualTo(retainedBank));
            }
            finally
            {
                foreach (var obstacle in exitBlockers)
                {
                    if (obstacle == null)
                        continue;
                    obstacle.GetComponent<Collider>().enabled = false;
                    UnityEngine.Object.Destroy(obstacle);
                }
                Physics.SyncTransforms();
                field.SetValue(director, original);
                if (motor.IsDriving)
                    motor.TryExitVehicle();
                car.EndDriving();
                car.GetComponent<CharacterController>().enabled = false;
                car.transform.SetPositionAndRotation(carPosition, carRotation);
                car.GetComponent<CharacterController>().enabled = true;
                motor.WarpTo(originalPosition);
                motor.transform.rotation = originalRotation;
                cash.SetAmount(original.CounterCash);
                parcel.SetCarrying(original.CarryingCourierParcel);
            }

            void Interact(StationAction action)
            {
                var stations = UnityEngine.Object.FindObjectsByType<InteractionMarker>(
                    FindObjectsInactive.Include, FindObjectsSortMode.None);
                InteractionMarker target = null;
                foreach (var marker in stations)
                {
                    if (marker.Action == action)
                    {
                        target = marker;
                        break;
                    }
                }

                Assert.That(target, Is.Not.Null, "Missing world action: " + action);
                perform.Invoke(director, new object[] { target, now });
            }
        }
    }
}
