using System;
using System.Collections;
using System.Reflection;
using NUnit.Framework;
using Rabron.Reconstruction;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UIElements;

namespace Rabron.Prototype.Tests
{
    /// <summary>
    /// Must execute in a real Unity Play Mode process, NOT by Python/.NET CI.
    /// Does not emulate keyboard input or verify a packaged Windows player.
    /// </summary>
    public sealed class PlayModeFlowTests
    {
        private const BindingFlags PrivateInstance =
            BindingFlags.Instance | BindingFlags.NonPublic;

        [UnityTest]
        public IEnumerator SceneBootCreatesRuntimePlayerCameraHudAndStations()
        {
            yield return null; // Let Unity run scene-load bootstrap + Awake/Start.

            var director = UnityEngine.Object.FindFirstObjectByType<PrototypeDirector>();
            Assert.That(director, Is.Not.Null,
                        "PrototypeBoot did not instantiate the runtime director");

            var motor = UnityEngine.Object.FindFirstObjectByType<ThirdPersonMotor>();
            var camera = UnityEngine.Object.FindFirstObjectByType<Camera>();
            var hud = UnityEngine.Object.FindFirstObjectByType<PrototypeHud>();
            var cash = UnityEngine.Object.FindFirstObjectByType<CashPilePresenter>();
            var guard = UnityEngine.Object.FindFirstObjectByType<GuardSensor>();
            var stations = UnityEngine.Object.FindObjectsByType<InteractionMarker>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);

            Assert.That(motor, Is.Not.Null, "No player controller");
            Assert.That(motor.GetComponent<CharacterController>(), Is.Not.Null);
            Assert.That(camera, Is.Not.Null, "No runtime follow camera");
            Assert.That(camera.isActiveAndEnabled, Is.True);
            Assert.That(hud, Is.Not.Null, "No runtime HUD");
            Assert.That(hud.GetComponent<UIDocument>().rootVisualElement.childCount,
                        Is.GreaterThan(0), "HUD labels were not attached");
            Assert.That(guard, Is.Not.Null, "No guard sensor in runtime scene");
            Assert.That(cash, Is.Not.Null, "No collectible physical counter money");
            Assert.That(stations.Length, Is.EqualTo(15));
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
            var simulated = new HeistSession();
            var cash = UnityEngine.Object.FindFirstObjectByType<CashPilePresenter>();
            Assert.That(cash, Is.Not.Null);
            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();

            // Direct dispatcher calls deliberately avoid modifying existing
            // save files or injecting synthetic keyboard events. Manual input,
            // collision-driven reachability and packaged EXE still need testing.
            try
            {
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
                cash.SetAmount(original.CounterCash);
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
