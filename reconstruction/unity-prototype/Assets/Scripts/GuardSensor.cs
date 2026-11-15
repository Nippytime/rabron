using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Original stationary guard prototype. Sight range and angle are demo
    /// tuning, not recovered ROB RUN alert or NPC behavior.
    /// </summary>
    public sealed class GuardSensor : MonoBehaviour
    {
        private const float DemoSightRange = 8f;
        private const float DemoHalfSightAngle = 55f;
        private readonly RaycastHit[] _hits = new RaycastHit[24];

        public bool CanSee(Transform player)
        {
            Vector3 origin = transform.position + Vector3.up * 1.5f;
            // The same live capsule-derived point is used for physical
            // interactions, so crouching never grants contradictory sight.
            Vector3 target = WorldOcclusion.UpperBodyPoint(player);
            Vector3 delta = target - origin;
            Vector3 horizontal = Vector3.ProjectOnPlane(delta, Vector3.up);

            // A high airborne target is not visible from unlimited altitude.
            if (delta.sqrMagnitude > DemoSightRange * DemoSightRange)
                return false;

            // An overlap has no meaningful facing angle. The placeholder
            // guard's mesh is a trigger, so standing inside it must not grant
            // invisibility or bypass arrest. Keep the normal cone at range.
            if (horizontal.sqrMagnitude >= 0.001f &&
                Vector3.Angle(transform.forward, horizontal) > DemoHalfSightAngle)
                return false;

            return WorldOcclusion.HasClearLine(origin, target, transform, _hits, player);
        }
    }
}
