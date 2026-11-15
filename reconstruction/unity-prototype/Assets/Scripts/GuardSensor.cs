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
            // Crouching changes the real CharacterController capsule. Aim at
            // its upper body rather than an imaginary standing-height head:
            // low solid cover can now block a crouched player's sightline.
            CharacterController body = player.GetComponent<CharacterController>();
            Vector3 target = body == null
                ? player.position + Vector3.up * 1.5f
                : player.TransformPoint(body.center +
                    Vector3.up * (body.height * 0.5f - body.radius * 0.5f));
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
