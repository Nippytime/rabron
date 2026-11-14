using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Small geometry query helpers shared by the third-person camera and
    /// interaction picker. The caller owns a reusable hit buffer to avoid
    /// per-frame allocations; overflow is treated conservatively.
    /// </summary>
    public static class WorldOcclusion
    {
        public static bool HasClearLine(Vector3 from, Vector3 to,
                                        Transform ignore, RaycastHit[] hits,
                                        Transform alsoIgnore = null)
        {
            Vector3 offset = to - from;
            float length = offset.magnitude;
            if (length < 0.001f)
                return true;

            int count = Physics.RaycastNonAlloc(from, offset / length, hits,
                                               length, ~0,
                                               QueryTriggerInteraction.Ignore);
            if (count == hits.Length)
                return false;

            for (int i = 0; i < count; i++)
            {
                Collider collider = hits[i].collider;
                if (collider != null &&
                    !collider.transform.IsChildOf(ignore) &&
                    (alsoIgnore == null || !collider.transform.IsChildOf(alsoIgnore)))
                    return false;
            }
            return true;
        }

        public static Vector3 ClampCamera(Vector3 pivot, Vector3 desired,
                                          Transform ignore, RaycastHit[] hits,
                                          float radius = 0.22f)
        {
            Vector3 offset = desired - pivot;
            float distance = offset.magnitude;
            if (distance < 0.01f)
                return desired;

            Vector3 direction = offset / distance;
            int count = Physics.SphereCastNonAlloc(pivot, radius, direction,
                                                  hits, distance, ~0,
                                                  QueryTriggerInteraction.Ignore);
            // An overflow means the nearest obstacle may be missing.
            if (count == hits.Length)
                return pivot + direction * 0.1f;

            float clearance = distance;
            for (int i = 0; i < count; i++)
            {
                RaycastHit hit = hits[i];
                if (hit.collider == null || hit.collider.transform.IsChildOf(ignore))
                    continue;

                clearance = Mathf.Min(clearance,
                    Mathf.Max(0.1f, hit.distance - 0.12f));
            }

            return pivot + direction * clearance;
        }
    }
}
