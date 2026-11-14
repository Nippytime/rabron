using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>Auto-initialize the procedural prototype when pressing Play.</summary>
    public static class PrototypeBoot
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Spawn()
        {
            if (Object.FindFirstObjectByType<PrototypeDirector>() != null)
                return;
            var root = new GameObject("Rabron Procedural Prototype");
            root.AddComponent<PrototypeDirector>();
            Application.targetFrameRate = 60;
        }
    }
}
