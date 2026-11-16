using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Rabron.Prototype
{
    /// <summary>Auto-initialize the procedural prototype when pressing Play.</summary>
    public static class PrototypeBoot
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Spawn()
        {
            if (!(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset))
                throw new InvalidOperationException(
                    "Rabron requires the configured Universal Render Pipeline, including in Windows Player.");
            var director = UnityEngine.Object.FindFirstObjectByType<PrototypeDirector>();
            if (director == null)
            {
                var root = new GameObject("Rabron Procedural Prototype");
                director = root.AddComponent<PrototypeDirector>();
            }

            // Only the explicit standalone headless acceptance invocation
            // self-terminates. Regular Editor and player sessions never do.
            if (!Application.isEditor && Application.isBatchMode &&
                Array.Exists(Environment.GetCommandLineArgs(),
                    arg => string.Equals(arg, "-rabronPlayerSmoke",
                                         StringComparison.OrdinalIgnoreCase)))
                director.gameObject.AddComponent<PrototypePlayerSmoke>();

            Application.targetFrameRate = 60;
        }
    }
}
