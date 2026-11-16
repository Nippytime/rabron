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
            PrototypeUrpSetup.VerifyConfigured();

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
                ValidateCrouchedGuardCover(root.transform, player, guard);
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
                ValidateDemoEconomy();
                ValidateLaunderingCapacity();
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

        private static void ValidateDemoEconomy()
        {
            // Exercise the live ScriptableObject formula in a real Unity
            // Editor invocation. CI's Python audit cannot execute this code.
            var economy = ScriptableObject.CreateInstance<PrototypeBalance>();
            try
            {
                economy.CleanPayoutPercent = 80;
                Check(economy.CleanPayoutFor(101) == 80,
                      "Demo percentage must round down to whole cash units");
                Check(economy.CleanPayoutFor(long.MaxValue) == 7378697629483820645L,
                      "Large clean payout must not overflow a valid 80% offer");

                economy.CleanPayoutPercent = 100;
                Check(economy.CleanPayoutFor(long.MaxValue) == long.MaxValue,
                      "100% payout must conserve an entire maximum-size balance");
                economy.CleanPayoutPercent = 0;
                Check(economy.CleanPayoutFor(long.MaxValue) == 0,
                      "Zero-percent offer must not mint currency");
                economy.CleanPayoutPercent = 1;
                Check(economy.CleanPayoutFor(99) == 0 &&
                      economy.CleanPayoutFor(101) == 1,
                      "Low-rate payout must truncate exact integer fractions");

                foreach (int invalid in new[] { -1, 101 })
                {
                    economy.CleanPayoutPercent = invalid;
                    bool rejected = false;
                    try { economy.CleanPayoutFor(10); }
                    catch (ArgumentOutOfRangeException) { rejected = true; }
                    Check(rejected, "Invalid demo percentage must fail closed: " + invalid);
                }

                economy.CleanPayoutPercent = 80;
                bool zeroRejected = false;
                try { economy.CleanPayoutFor(0); }
                catch (ArgumentOutOfRangeException) { zeroRejected = true; }
                Check(zeroRejected, "No payout is computed for zero dirty cash");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(economy);
            }
        }

        private static void ValidateLaunderingCapacity()
        {
            // This runs in the actual Unity Editor using JsonUtility; the
            // hosted Python/.NET jobs do not execute Editor code.
            var nearLimit = new HeistSession();
            nearLimit.PickUpCourierParcel();
            nearLimit.DeliverCourierParcel(long.MaxValue - 1);
            nearLimit.Scout();
            nearLimit.PutOnMask();
            nearLimit.StartHeist();
            nearLimit.TakeLoot("editor-capacity-loot");
            nearLimit.Escape();
            nearLimit.SellLoot(new Dictionary<string, long>
            {
                ["editor-capacity-loot"] = 10
            });
            nearLimit.CollectCounterCash();
            bool refused = false;
            try { nearLimit.StartLaundering(10, 2, 100, 2); }
            catch (InvalidOperationException) { refused = true; }
            Check(refused && nearLimit.Phase == HeistPhase.DirtyCashCollected &&
                  nearLimit.DirtyCash == 10 && nearLimit.CleanCash == long.MaxValue - 1,
                  "Unpayable laundering must not debit dirty cash or strand the phase");

            nearLimit.StartLaundering(1, 1, 100, 2);
            var invalid = nearLimit.ExportSnapshot();
            invalid.CleanCash = long.MaxValue;
            bool rejected = false;
            try
            {
                HeistSession.FromSnapshot(JsonUtility.FromJson<HeistSessionSnapshot>(
                    JsonUtility.ToJson(invalid)));
            }
            catch (ArgumentException) { rejected = true; }
            Check(rejected, "Unity JSON accepted an unpayable laundering checkpoint");

            var restored = HeistSession.FromSnapshot(
                JsonUtility.FromJson<HeistSessionSnapshot>(
                    JsonUtility.ToJson(nearLimit.ExportSnapshot())));
            restored.CompleteLaundering(102);
            Check(restored.CleanCash == long.MaxValue &&
                  restored.DirtyCash == 9 && restored.Phase == HeistPhase.Laundered,
                  "Maximum-size payable laundering job failed to complete after Unity JSON");
        }

        private static void ValidateCrouchedGuardCover(
            Transform root, ThirdPersonMotor player, GuardSensor guard)
        {
            // Probe the cover players actually encounter, not a temporary
            // test-only cube that can pass while the shipped world has none.
            Transform cover = root.Find("Warehouse stealth cover");
            Check(cover != null && cover.GetComponent<BoxCollider>() != null &&
                  cover.GetComponent<BoxCollider>().enabled &&
                  !cover.GetComponent<BoxCollider>().isTrigger,
                  "The generated warehouse must have solid player stealth cover");
            Check(cover.position.z > 28f && cover.position.z < guard.transform.position.z &&
                  cover.localScale.y >= 1.4f && cover.localScale.y <= 1.6f,
                  "Warehouse cover must be waist high and between player and guard");
            MethodInfo crouch = typeof(ThirdPersonMotor).GetMethod(
                "UpdateCrouch", BindingFlags.Instance | BindingFlags.NonPublic);
            Check(crouch != null, "Cannot exercise the live crouch capsule");

            // Use the real guard-control station across the real barrier.
            // Crouch must block BOTH guard sight and the player's station ray.
            InteractionMarker control = Array.Find(
                root.GetComponentsInChildren<InteractionMarker>(true),
                marker => marker.Action == StationAction.ControlStaff);
            Check(control != null, "Generated guard-control station is missing");
            // Read the production radius, not a synthetic test-only budget.
            FieldInfo radiusField = typeof(PrototypeDirector).GetField(
                "InteractionRadius", BindingFlags.Static | BindingFlags.NonPublic);
            Check(radiusField != null, "Director interaction radius is missing");
            float reach = (float)radiusField.GetRawConstantValue();
            Check(reach > 0f, "Director interaction radius must be positive");
            var interactionHits = new RaycastHit[24];
            bool CanReachControl() => WorldOcclusion.HasClearLine(
                WorldOcclusion.UpperBodyPoint(player.transform),
                control.transform.position, player.transform, interactionHits);
            // Use a reachable, collider-clear point directly in front of
            // the shipped cover. A sightline test alone is not an action test.
            void CheckControlInReach()
            {
                float distanceSq = (control.transform.position -
                                    player.transform.position).sqrMagnitude;
                Check(distanceSq < reach * reach,
                      "Guard control must be inside the actual interaction radius");
                foreach (InteractionMarker marker in
                         root.GetComponentsInChildren<InteractionMarker>(true))
                {
                    if (marker != control)
                        Check((marker.transform.position - player.transform.position)
                                  .sqrMagnitude > distanceSq,
                              "Guard control must be the nearest station at test position");
                }
            }
            try
            {
                player.transform.position = new Vector3(-0.7f, 0.12f, 29.2f);
                Physics.SyncTransforms();
                CheckControlInReach();
                Check(guard.CanSee(player.transform),
                      "Standing player must be visible over low solid cover");
                Check(CanReachControl(),
                      "Standing sightline should clear real cover toward guard control");

                crouch.Invoke(player, new object[] { true });
                Physics.SyncTransforms();
                Check(player.IsCrouched && !guard.CanSee(player.transform),
                      "Crouched player must be hidden behind low solid cover");
                Check(!CanReachControl(),
                      "Crouched station interaction cannot pass through low solid cover");

                crouch.Invoke(player, new object[] { false });
                Physics.SyncTransforms();
                Check(!player.IsCrouched && guard.CanSee(player.transform),
                      "Standing back up must restore guard visibility over cover");
                Check(CanReachControl(),
                      "Standing back up must restore the station sightline");

                // Stealth is due to the physical barrier, not an invisible
                // gameplay flag: walking around it restores detection.
                player.transform.position = new Vector3(-1.95f, 0.12f, 30.5f);
                Physics.SyncTransforms();
                CheckControlInReach();
                Check(guard.CanSee(player.transform),
                      "Standing beside real warehouse cover must remain visible");
                Check(CanReachControl(),
                      "Flanking physical cover must restore station sightline");

                // The near-side flank above is intentionally exposed. This
                // wider route must be genuinely quiet, not just covered:
                // clear geometry to guard and station, but outside live FOV.
                player.transform.position = new Vector3(-3.6f, 0.12f, 31f);
                Physics.SyncTransforms();
                CheckControlInReach();
                Check(CanReachControl(),
                      "Quiet left flank must reach the real guard-control station");
                Check(WorldOcclusion.HasClearLine(
                          guard.transform.position + Vector3.up * 1.5f,
                          WorldOcclusion.UpperBodyPoint(player.transform),
                          guard.transform, interactionHits, player.transform),
                      "Quiet flank guard ray must be unobstructed, not hidden by cover");
                Check(!guard.CanSee(player.transform),
                      "Quiet flank must be outside the real guard vision cone");

                player.transform.position = new Vector3(0f, 20f, 28f);
                Physics.SyncTransforms();
                Check(!guard.CanSee(player.transform),
                      "Guard cannot detect a player far above 3D sight range");
            }
            finally
            {
                if (player.IsCrouched)
                    crouch.Invoke(player, new object[] { false });
                Physics.SyncTransforms();
            }
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
