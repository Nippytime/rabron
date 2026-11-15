using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Rabron.Reconstruction;
using UnityEditor;
using UnityEngine;

namespace Rabron.Prototype.Editor
{
    /// <summary>
    /// Runs inside a real Unity 6000 Editor, not a mocked .NET environment.
    /// CLI: -executeMethod Rabron.Prototype.Editor.PrototypeSmokeTest.ValidateProject
    /// </summary>
    public static class PrototypeSmokeTest
    {
        private const string PassToken = "RABRON_UNITY_EDITOR_SMOKE_PASS";
        private const string BuildToken = "RABRON_UNITY_WINDOWS_BUILD_PASS";

        [MenuItem("Tools/Rabron/Verify Unity Prototype")]
        public static void ValidateProject()
        {
#if !ENABLE_INPUT_SYSTEM
            throw new InvalidOperationException(
                "Unity Input System backend is disabled. Enable 'Input System Package (New)' " +
                "under Project Settings > Player > Active Input Handling and restart Unity.");
#else
            PrototypeSceneInstaller.EnsureScene();

            var root = new GameObject("Temporary prototype verification");
            try
            {
                var stations = PrototypeWorld.Create(root.transform, out var player,
                                                    out var cashPile, out var guard);
                var kinds = new HashSet<StationAction>();
                foreach (var station in stations)
                {
                    Check(station != null && station.gameObject.activeSelf,
                          "A gameplay station was not instantiated");
                    Check(station.GetComponent<Collider>().isTrigger,
                          "A gameplay station obstructs player movement");
                    Check(kinds.Add(station.Action),
                          "Duplicate gameplay action " + station.Action);
                }

                var expected = (StationAction[])Enum.GetValues(typeof(StationAction));
                Check(stations.Count == expected.Length,
                      "Missing interaction markers: " + stations.Count);
                foreach (var action in expected)
                    Check(kinds.Contains(action), "Missing station " + action);

                Check(player != null, "No CharacterController motor created");
                var capsule = player.GetComponent<CharacterController>();
                Check(capsule != null && capsule.stepOffset >= 0.5f,
                      "Fencing platform is not reachable by walking");
                Check(root.transform.Find("Ground") != null,
                      "No collidable ground was created");

                // The independently authored car has a real movement
                // collider, and its enter pillar must travel with it.
                var car = root.GetComponentInChildren<PrototypeVehicle>(true);
                Check(car != null && car.GetComponent<CharacterController>() != null,
                      "No collider-backed prototype vehicle was created");
                Check(!car.Occupied, "Practice car must start unoccupied");
                bool carMarkerFollows = false;
                foreach (var station in stations)
                {
                    if (station.Action == StationAction.VehicleEnter)
                        carMarkerFollows = station.transform.IsChildOf(car.transform);
                }
                Check(carMarkerFollows, "Car entrance marker must follow the vehicle");

                // Source-side step verification in the actual Unity Editor.
                // This does not simulate pressing a jump key or prove traversal.
                var flags = BindingFlags.Static | BindingFlags.NonPublic;
                MethodInfo integrate = typeof(ThirdPersonMotor).GetMethod(
                    "IntegrateVertical", flags);
                MethodInfo ceiling = typeof(ThirdPersonMotor).GetMethod(
                    "ResolveCeiling", flags);
                Check(integrate != null && ceiling != null,
                      "Missing grounded jump/ceiling movement integration");
                float launch = (float)integrate.Invoke(null,
                    new object[] { 0f, true, true, 0f });
                float air = (float)integrate.Invoke(null,
                    new object[] { 0f, false, true, 0.1f });
                float groundedNoJump = (float)integrate.Invoke(null,
                    new object[] { launch, true, false, 0f });
                Check(groundedNoJump < 0f,
                      "Grounded motor cannot retain upward velocity without a jump");
                Check(launch > 0f && air < 0f,
                      "Jump must require ground and never permit double jump");
                Check((float)ceiling.Invoke(null,
                    new object[] { launch, CollisionFlags.Above }) == 0f,
                      "Jump must stop rising when colliding with a ceiling");

                // The heist wall must block both interaction and camera.
                // Probe the actual generated colliders, not a mock scene.
                Physics.SyncTransforms();
                Check(guard != null && guard.transform.parent == root.transform,
                      "Warehouse security guard did not spawn");

                // Source-backed FOV geometry, with invented demo distance/angles.
                player.transform.position = new Vector3(0f, 0f, 28f);
                Physics.SyncTransforms();
                Check(guard.CanSee(player.transform),
                      "Guard should see a player directly ahead inside the warehouse");
                player.transform.position = new Vector3(0f, 0f, 36f);
                Physics.SyncTransforms();
                Check(!guard.CanSee(player.transform),
                      "Guard should not see a player directly behind him");
                // A coincident position previously failed the forward-cone
                // check because the direction vector has zero length.
                player.transform.position = guard.transform.position;
                Physics.SyncTransforms();
                Check(guard.CanSee(player.transform),
                      "Overlapping the guard must not grant invisibility");
                player.transform.position = new Vector3(0f, 0.12f, -15f);
                Physics.SyncTransforms();

                var hits = new RaycastHit[24];
                Vector3 artwork = default;
                foreach (var station in stations)
                {
                    if (station.Action == StationAction.Artwork)
                        artwork = station.transform.position;
                }

                Check(!WorldOcclusion.HasClearLine(
                          new Vector3(-3f, 1.5f, 13f), artwork, player.transform, hits),
                      "Warehouse wall must block interactions from the street");
                Check(WorldOcclusion.HasClearLine(
                          new Vector3(-3f, 1.5f, 23f), artwork, player.transform, hits),
                      "Artwork must be interactable from inside the warehouse");

                Vector3 cashPickup = default;
                foreach (var station in stations)
                {
                    if (station.Action == StationAction.CollectCash)
                        cashPickup = station.transform.position;
                }

                Check(!WorldOcclusion.HasClearLine(
                          new Vector3(-19f, 1.5f, -2f), cashPickup,
                          player.transform, hits),
                      "Cash counter must block collection from its front");
                Check(WorldOcclusion.HasClearLine(
                          new Vector3(-19f, 1.5f, 3f), cashPickup,
                          player.transform, hits),
                      "Cash must be reachable from behind the counter");

                Vector3 pivot = new Vector3(-3f, 1.6f, 13f);
                Vector3 wallSide = new Vector3(-3f, 1.6f, 20f);
                Vector3 clamped = WorldOcclusion.ClampCamera(
                    pivot, wallSide, player.transform, hits);
                Check(clamped.z < 16.5f && clamped.z >= pivot.z,
                      "Follow camera must remain on the near side of warehouse wall");

                // Exercise the actual presenter, not a mocked visibility flag.
                Check(cashPile != null && !cashPile.IsVisible,
                      "Counter cash must start hidden");
                Check(cashPile.transform.childCount == 4,
                      "Expected four procedural cash bundles on the counter");
                foreach (Transform bundle in cashPile.transform)
                    Check(!bundle.GetComponent<Collider>().enabled,
                          "Decorative cash must not obstruct walking");
                cashPile.SetAmount(200); // Explicit test fixture, not a source payout.
                Check(cashPile.IsVisible,
                      "Uncollected cash must be physically visible after fencing");
                cashPile.SetAmount(0);
                Check(!cashPile.IsVisible,
                      "Collected cash must disappear from the fence");

                // Parcel is strictly a visual child of the player; it cannot
                // obstruct courier pickup, walls or other world interactions.
                var parcel = player.GetComponentInChildren<CourierParcelPresenter>(true);
                Check(parcel != null && !parcel.GetComponent<Collider>().enabled,
                      "Courier cargo visual must exist without an active collider");
                Check(!parcel.IsVisible, "Uncollected courier cargo must start hidden");
                parcel.SetCarrying(true);
                Check(parcel.IsVisible, "Courier cargo must be visible after pickup");
                parcel.SetCarrying(false);
                Check(!parcel.IsVisible, "Returned courier cargo must disappear");

                ValidateHeistCore();
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }

            Debug.Log(PassToken + ": procedural scene, stations, colliders, and heist core verified");
#endif
        }

        /// <summary>
        /// Use -buildTarget StandaloneWindows64 on the Unity CLI.
        /// Does NOT assert that the built executable has been interactively played.
        /// </summary>
        public static void ValidateAndBuildWindows()
        {
            ValidateProject();
            PrototypeSceneInstaller.BuildWindows();

            string outputDirectory = Path.GetFullPath(
                Path.Combine(Application.dataPath, "..", "Builds"));
            string executable = Path.Combine(outputDirectory, "RabronPrototype.exe");
            Check(File.Exists(executable), "Build succeeded but executable is missing: " + executable);
            Check(Directory.Exists(Path.Combine(outputDirectory, "RabronPrototype_Data")),
                  "Windows build data folder is missing");
            Debug.Log(BuildToken + ": " + executable);
        }

        private static void ValidateHeistCore()
        {
            // Numbers here are deliberately fixture data, not original rates.
            // Exercise the alternate lawful path through Unity's own JSON
            // serializer, including an in-progress parcel on restart.
            var courier = new HeistSession();
            courier.PickUpCourierParcel();
            courier = HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                JsonUtility.ToJson(courier.ExportSnapshot())));
            Check(courier.CarryingCourierParcel,
                  "Unity JSON lost the unfinished legal delivery parcel");
            courier.CancelCourierParcel();
            Check(!courier.CarryingCourierParcel && courier.CleanCash == 0,
                  "Courier return must clear the parcel without creating currency");
            courier.PickUpCourierParcel();
            courier.DeliverCourierParcel(12); // Deliberate independent demo fixture.
            Check(!courier.CarryingCourierParcel && courier.CleanCash == 12 &&
                  courier.DirtyCash == 0 && courier.CounterCash == 0,
                  "Lawful delivery must pay clean cash exactly once");
            courier.OpenBankAccount();
            courier.DepositCleanCash(12);
            Check(courier.BankBalance == 12,
                  "Lawful courier earnings were not depositable at the bank");

            // A quiet/loud empty-handed robbery must have a recovery
            // path without fencing, minting or persisting an Escaped dead end.
            var retreat = new HeistSession();
            retreat.Scout();
            retreat.PutOnMask();
            retreat.StartHeist();
            retreat.RaiseAlarm();
            retreat = HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                JsonUtility.ToJson(retreat.ExportSnapshot())));
            Check(retreat.Phase == HeistPhase.Robbing && retreat.Loot.Count == 0,
                  "Unity JSON lost the empty in-progress robbery");
            retreat.WithdrawEmptyHanded();
            Check(retreat.Phase == HeistPhase.Idle &&
                  retreat.CurrentRole == PlayerRole.Civilian && !retreat.AlarmRaised &&
                  retreat.CounterCash == 0 && retreat.DirtyCash == 0,
                  "Empty-handed withdrawal must restore civilian play without paying");

            // The core cannot exit with an unfinished heist even if a
            // caller bypasses the UI's already-guarded ExitCity station.
            var interrupted = new HeistSession();
            interrupted.Scout();
            interrupted.PutOnMask();
            interrupted.StartHeist();
            interrupted.TakeLoot("smoke-city-only-loot");
            bool blockedExit = false;
            try { interrupted.LeaveCity(); }
            catch (InvalidOperationException) { blockedExit = true; }
            Check(blockedExit && interrupted.CurrentZone == Zone.City &&
                  interrupted.CurrentRole == PlayerRole.Criminal &&
                  interrupted.Loot.Count == 1,
                  "Active robbery must not escape city through core API");
            var impossibleDesert = interrupted.ExportSnapshot();
            impossibleDesert.Zone = Zone.Desert;
            bool rejectedDesert = false;
            try
            {
                HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                    JsonUtility.ToJson(impossibleDesert)));
            }
            catch (ArgumentException) { rejectedDesert = true; }
            Check(rejectedDesert, "Unity JSON accepted unreachable desert robbery");

            // Exercise the custody state through Unity's actual JSON
            // serializer. An alarm alone is not the same as arrest.
            var custody = new HeistSession();
            custody.Scout();
            custody.PutOnMask();
            custody.StartHeist();
            custody.TakeLoot("smoke-arrest-loot");
            custody.RaiseAlarm();
            custody.ArrestAfterAlarm();
            custody = HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                JsonUtility.ToJson(custody.ExportSnapshot())));
            Check(custody.Phase == HeistPhase.Arrested &&
                  custody.CurrentRole == PlayerRole.Criminal &&
                  custody.Loot.Count == 0 && custody.AlarmRaised,
                  "Unity JSON lost the alarm/custody confiscation checkpoint");
            custody.ReleaseFromCustody();
            Check(custody.CurrentRole == PlayerRole.Civilian &&
                  custody.Phase == HeistPhase.Idle && !custody.AlarmRaised,
                  "Custody release must unlock lawful civilian gameplay");

            var session = new HeistSession();
            session.Scout();
            session.PutOnMask();
            session.StartHeist();
            session.ControlStaff();
            Check(session.StaffControlled && !session.AlarmRaised,
                  "Controlling staff should not itself raise an alarm");
            session.TakeLoot("smoke-loot-01");
            session.Escape();
            session.SellLoot(new Dictionary<string, long>
            {
                ["smoke-loot-01"] = 20
            });
            Check(session.CounterCash == 20 && session.DirtyCash == 0,
                  "Fencing skipped collectible counter cash");

            // Exercise Unity's actual JSON serializer, not merely the
            // portable snapshot transfer object tested by .NET Actions.
            session = HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                JsonUtility.ToJson(session.ExportSnapshot())));
            Check(session.CounterCash == 20 && session.DirtyCash == 0,
                  "JSON roundtrip incorrectly collected money from the fence");

            session.CollectCounterCash();
            session.StartLaundering(20, 15, 100, 5);
            session = HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                JsonUtility.ToJson(session.ExportSnapshot())));
            Check(session.LaunderingReadyAt == 105,
                  "Laundering deadline was not preserved by Unity JSON");
            session.CompleteLaundering(105);
            session.LeaveCity();
            session.EnterCity();
            session.OpenBankAccount();
            session.DepositCleanCash(15);
            Check(session.BankBalance == 15 && session.CleanCash == 0,
                  "Clean cash was not deposited");
        }

        private static void Check(bool condition, string reason)
        {
            if (!condition)
                throw new InvalidOperationException(reason);
        }
    }
}
