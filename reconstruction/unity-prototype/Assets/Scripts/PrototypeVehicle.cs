using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Independently authored small driving blockout, not extracted vehicle
    /// handling. A CharacterController prevents driving through static walls.
    /// This is not a wheel/suspension or networked vehicle simulation.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public sealed class PrototypeVehicle : MonoBehaviour
    {
        private const float ForwardSpeed = 10f;
        private const float ReverseSpeed = 4f;
        private const float Acceleration = 8f;
        private const float BrakeDeceleration = 18f;
        private const float SteeringDegrees = 66f;
        private readonly Collider[] _exitHits = new Collider[32];
        private CharacterController _body = null!;
        private float _speed;

        public bool Occupied { get; private set; }
        public float Speed => _speed;

        private void Awake()
        {
            _body = GetComponent<CharacterController>();
        }

        public bool BeginDriving()
        {
            if (Occupied)
                return false;
            _speed = 0f;
            Occupied = true;
            return true;
        }

        public void EndDriving()
        {
            Occupied = false;
            _speed = 0f;
        }

        public void Drive(Vector2 steeringAndThrottle, bool braking, float deltaSeconds)
        {
            if (!Occupied || deltaSeconds <= 0f)
                return;

            float throttle = Mathf.Clamp(steeringAndThrottle.y, -1f, 1f);
            float target = braking ? 0f
                : throttle * (throttle < 0f ? ReverseSpeed : ForwardSpeed);
            _speed = Mathf.MoveTowards(_speed, target,
                (braking ? BrakeDeceleration : Acceleration) * deltaSeconds);

            // Turn in the direction of motion, including reversing. No
            // zero-speed pivot or instant lateral teleport through obstacles.
            if (Mathf.Abs(_speed) > 0.1f)
            {
                float turn = Mathf.Clamp(steeringAndThrottle.x, -1f, 1f)
                    * Mathf.Sign(_speed) * SteeringDegrees * deltaSeconds
                    * Mathf.Clamp01(Mathf.Abs(_speed) / 3f);
                transform.Rotate(0f, turn, 0f);
            }

            CollisionFlags collision = _body.Move(
                (transform.forward * _speed + Vector3.down * 2f) * deltaSeconds);
            if ((collision & CollisionFlags.Sides) != 0)
                _speed = 0f;
        }

        public bool TryFindExit(Transform passenger, out Vector3 destination)
        {
            destination = default;
            if (!Occupied || Mathf.Abs(_speed) > 0.5f)
                return false;

            // Use the passenger's actual full capsule, not a guessed probe
            // that misses ankle-height obstructions when walking is restored.
            // The motor disables its CharacterController while seated, but
            // its dimensions remain available for an accurate clearance test.
            CharacterController passengerBody = passenger.GetComponent<CharacterController>();
            if (passengerBody == null)
                return false;
            Vector3 scale = passenger.lossyScale;
            float radius = passengerBody.radius *
                Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z));
            float height = Mathf.Max(passengerBody.height * Mathf.Abs(scale.y),
                                     radius * 2f);
            float halfAxis = height * 0.5f - radius;
            float clearanceRadius = radius + passengerBody.skinWidth *
                Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z));
            Vector3 centerOffset = passenger.rotation *
                Vector3.Scale(passengerBody.center, scale);

            // Check both sides rather than ejecting a player through a wall.
            // Root/vehicle collider and the passenger are deliberately ignored.
            for (int side = 1; side >= -1; side -= 2)
            {
                Vector3 candidate = transform.position + transform.right * (side * 2.3f);
                candidate.y = transform.position.y + 0.1f;
                Vector3 center = candidate + centerOffset;
                int count = Physics.OverlapCapsuleNonAlloc(
                    center - Vector3.up * halfAxis,
                    center + Vector3.up * halfAxis,
                    clearanceRadius, _exitHits, ~0, QueryTriggerInteraction.Ignore);
                if (count == _exitHits.Length)
                    continue; // Cannot prove clearance on overflow.

                bool blocked = false;
                for (int i = 0; i < count; i++)
                {
                    Collider hit = _exitHits[i];
                    if (hit != null && !hit.transform.IsChildOf(transform) &&
                        !hit.transform.IsChildOf(passenger))
                    {
                        blocked = true;
                        break;
                    }
                }
                if (blocked)
                    continue;

                destination = candidate;
                return true;
            }
            return false;
        }
    }
}
