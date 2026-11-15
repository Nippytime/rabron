using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Rabron.Prototype
{
    /// <summary>
    /// One-frame, opt-in standalone Windows startup evidence. Attached only
    /// when -batchmode and -rabronPlayerSmoke are both supplied to the Player.
    /// No synthetic interaction and no gameplay/graphics acceptance claim.
    /// </summary>
    public sealed class PrototypePlayerSmoke : MonoBehaviour
    {
        private IEnumerator Start()
        {
            // The runtime boot creates its procedural world in Awake.
            yield return null;

            var director = FindFirstObjectByType<PrototypeDirector>();
            var motor = FindFirstObjectByType<ThirdPersonMotor>();
            var hud = FindFirstObjectByType<PrototypeHud>();
            var markers = FindObjectsByType<InteractionMarker>(
                FindObjectsInactive.Include, FindObjectsSortMode.None);
            var actions = new HashSet<StationAction>();
            foreach (var marker in markers)
                if (marker != null)
                    actions.Add(marker.Action);

            bool booted = director != null && motor != null &&
                motor.GetComponent<CharacterController>() != null &&
                hud != null && hud.GetComponent<UIDocument>() != null &&
                markers.Length == 21 && actions.Count == 21;

            if (booted)
                Debug.Log("RABRON_WINDOWS_PLAYER_SMOKE_PASS");
            else
                Debug.LogError("RABRON_WINDOWS_PLAYER_SMOKE_FAILED: " +
                    "missing runtime director, motor, HUD or unique stations.");

            // Only the automated smoke invocation exits the application.
            // This probe is never added to a normal interactive player.
            Application.Quit(booted ? 0 : 1);
        }
    }
}
