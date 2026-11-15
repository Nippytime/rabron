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

            Assert.That(camera, Is.Not.Null, "No runtime follow camera");
            Assert.That(camera.isActiveAndEnabled, Is.True);
            Assert.That(hud, Is.Not.Null, "No runtime HUD");
            Assert.That(hud.GetComponent<UIDocument>().rootVisualElement.childCount,
                        Is.GreaterThan(0), "HUD labels were not attached");
            Assert.That(guard, Is.Not.Null, "No guard sensor in runtime scene");
            Assert.That(cash, Is.Not.Null, "No collectible physical counter money");
            Assert.That(stations.Length, Is.EqualTo(20));
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
                motor.WarpTo(new Vector3(0f, 0.12f, 31.5f));
                Physics.SyncTransforms();
                update.Invoke(director, null);
                Assert.That(alarmed.Phase, Is.EqualTo(HeistPhase.Arrested),
                            "Visible close guard must cause confiscation after alarm");
                Assert.That(alarmed.Loot.Count, Is.EqualTo(0));
                Assert.That(alarmed.DirtyCash, Is.EqualTo(0L));
                Assert.That(alarmed.CurrentRole, Is.EqualTo(PlayerRole.Criminal));
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
                Interact(StationAction.ExitCity);
                Assert.That(simulated.CurrentRole, Is.EqualTo(PlayerRole.Civilian));
                Interact(StationAction.EnterCity);
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
                field.SetValue(director, original);
                motor.WarpTo(originalPosition);
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
