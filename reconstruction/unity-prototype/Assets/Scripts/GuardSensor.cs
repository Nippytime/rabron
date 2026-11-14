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
            Vector3 target = player.position + Vector3.up * 1.5f;
            Vector3 delta = target - origin;
            Vector3 horizontal = Vector3.ProjectOnPlane(delta, Vector3.up);

            if (horizontal.sqrMagnitude > DemoSightRange * DemoSightRange ||
                horizontal.sqrMagnitude < 0.001f)
                return false;

            if (Vector3.Angle(transform.forward, horizontal) > DemoHalfSightAngle)
                return false;

            return WorldOcclusion.HasClearLine(origin, target, transform, _hits, player);
        }
    }
}
