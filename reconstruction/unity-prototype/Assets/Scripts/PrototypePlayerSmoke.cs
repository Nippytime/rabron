using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Rabron.Reconstruction;
using UnityEngine;
using UnityEngine.UIElements;

namespace Rabron.Prototype
{
    /// <summary>
    /// Opt-in standalone Windows startup and isolated save round-trip probe.
    /// Runs only with -batchmode -rabronPlayerSmoke, never in normal play.
    /// This is not visual, controller or gameplay acceptance.
    /// </summary>
    public sealed class PrototypePlayerSmoke : MonoBehaviour
    {
        private IEnumerator Start()
        {
            // The runtime boot creates its procedural world in Awake.
            yield return null;

            var director = FindFirstObjectByType<PrototypeDirector>();
            var motor = FindFirstObjectByType<ThirdPersonMotor>();
            var camera = FindFirstObjectByType<Camera>();
            var hud = FindFirstObjectByType<PrototypeHud>();
            var audio = FindFirstObjectByType<PrototypeAudioFeedback>();
            var guard = FindFirstObjectByType<GuardSensor>();
            var vehicle = FindFirstObjectByType<PrototypeVehicle>();
            var cash = FindObjectsByType<CashPilePresenter>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            var parcels = FindObjectsByType<CourierParcelPresenter>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            var markers = FindObjectsByType<InteractionMarker>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            var actions = new HashSet<StationAction>();
            foreach (var marker in markers)
                if (marker != null)
                    actions.Add(marker.Action);

            bool booted = director != null && motor != null &&
                motor.GetComponent<CharacterController>() != null &&
                camera != null && hud != null &&
                hud.GetComponent<UIDocument>() != null &&
                audio != null && audio.CuesReady &&
                guard != null && vehicle != null &&
                vehicle.GetComponent<CharacterController>() != null &&
                !vehicle.Occupied &&
                cash.Length == 1 && parcels.Length == 1 &&
                markers.Length == 21 && actions.Count == 21;

            // Do not touch the filesystem at all unless the expected world
            // exists. The checkpoint probe itself enforces a unique temp path.
            bool saved = booted && VerifyIsolatedCheckpoint(out string saveError);
            if (saved)
                Debug.Log("RABRON_WINDOWS_PLAYER_SMOKE_PASS");
            else
                Debug.LogError("RABRON_WINDOWS_PLAYER_SMOKE_FAILED: " +
                    (booted ? saveError :
                    "Missing runtime camera, motor, HUD, audio, guard, vehicle, " +
                    "cash, parcel or 21 unique stations."));

            // Only the automated smoke invocation exits the application.
            Application.Quit(saved ? 0 : 1);
        }

        private static bool VerifyIsolatedCheckpoint(out string error)
        {
            error = "";
            string path = Path.GetFullPath(PrototypeSaveStore.SavePath);
            string invocation = Path.GetDirectoryName(path);
            string isolatedRoot = Path.GetFullPath(Path.Combine(
                Application.temporaryCachePath, "rabron-player-smoke"));

            // A path in persistentDataPath, an unrelated temp directory or
            // the shared smoke root must never be used for this write probe.
            if (string.IsNullOrEmpty(invocation) ||
                !string.Equals(Path.GetDirectoryName(invocation), isolatedRoot,
                               StringComparison.OrdinalIgnoreCase))
            {
                error = "Refusing to write outside a unique player-smoke temp directory.";
                return false;
            }

            try
            {
                var initial = new HeistSession();
                initial.OpenBankAccount();
                initial.PickUpCourierParcel();
                if (!PrototypeSaveStore.TrySave(initial, out error))
                    return false;

                var pending = PrototypeSaveStore.Load(out _);
                if (!pending.BankAccountOpened || !pending.CarryingCourierParcel ||
                    pending.BankBalance != 0 || pending.CleanCash != 0)
                {
                    error = "First isolated checkpoint did not restore courier cargo.";
                    return false;
                }

                pending.DeliverCourierParcel(25);
                pending.DepositCleanCash(10);
                if (!PrototypeSaveStore.TrySave(pending, out error))
                    return false;

                var final = PrototypeSaveStore.Load(out _);
                var backup = HeistSession.FromSnapshot(
                    JsonUtility.FromJson<HeistSessionSnapshot>(
                        File.ReadAllText(path + ".bak")));
                if (!final.BankAccountOpened || final.CarryingCourierParcel ||
                    final.CleanCash != 15 || final.BankBalance != 10 ||
                    !backup.BankAccountOpened || !backup.CarryingCourierParcel ||
                    backup.CleanCash != 0 || backup.BankBalance != 0)
                {
                    error = "Atomic replacement or backup round-trip did not preserve balances.";
                    return false;
                }
                return true;
            }
            catch (Exception exception)
            {
                error = "Isolated checkpoint smoke failed: " + exception.Message;
                return false;
            }
            finally
            {
                // This exact invocation directory was verified as a child
                // of the smoke-specific cache root before the first write.
                try
                {
                    if (Directory.Exists(invocation))
                        Directory.Delete(invocation, recursive: true);
                }
                catch (Exception exception)
                {
                    Debug.LogWarning("Could not clean isolated smoke files: " +
                                     exception.Message);
                }
            }
        }
    }
}
