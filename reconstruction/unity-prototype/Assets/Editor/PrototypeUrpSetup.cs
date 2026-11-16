using System;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Rabron.Prototype.Editor
{
    /// <summary>Unity CLI: -executeMethod Rabron.Prototype.Editor.PrototypeUrpSetup.Configure</summary>
    public static class PrototypeUrpSetup
    {
        private const string Folder = "Assets/Settings";
        private const string RendererPath = Folder + "/RabronRenderer.asset";
        private const string PipelinePath = Folder + "/RabronURP.asset";
        private const string PassToken = "RABRON_URP_CONFIGURED_PASS";

        [MenuItem("Tools/Rabron/Configure URP 17.5")]
        public static void Configure()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
                throw new InvalidOperationException("Unity must be idle to configure URP.");

            EnsureConfigured();
            VerifyConfigured();
            Debug.Log(PassToken + ": URP Lit/Universal Renderer configured for Graphics and all quality levels");
        }

        internal static void EnsureConfigured()
        {
            if (!AssetDatabase.IsValidFolder(Folder))
                AssetDatabase.CreateFolder("Assets", "Settings");

            var rendererObject = AssetDatabase.LoadMainAssetAtPath(RendererPath);
            if (rendererObject != null && !(rendererObject is UniversalRendererData))
                throw new InvalidOperationException("Expected a URP Universal Renderer at " + RendererPath);
            var renderer = rendererObject as UniversalRendererData;
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                renderer.name = "Rabron Universal Renderer";
                AssetDatabase.CreateAsset(renderer, RendererPath);
            }

            var pipelineObject = AssetDatabase.LoadMainAssetAtPath(PipelinePath);
            if (pipelineObject != null && !(pipelineObject is UniversalRenderPipelineAsset))
                throw new InvalidOperationException("Expected a URP pipeline at " + PipelinePath);
            var pipeline = pipelineObject as UniversalRenderPipelineAsset;
            if (pipeline == null)
            {
                pipeline = UniversalRenderPipelineAsset.Create(renderer);
                pipeline.name = "Rabron URP";
                AssetDatabase.CreateAsset(pipeline, PipelinePath);
            }

            // Never replace an asset's renderer silently. A manually edited
            // or corrupted pipeline must be fixed explicitly.
            var rendererList = new SerializedObject(pipeline).FindProperty("m_RendererDataList");
            if (rendererList == null || rendererList.arraySize == 0 ||
                rendererList.GetArrayElementAtIndex(0).objectReferenceValue != renderer)
                throw new InvalidOperationException("URP pipeline is not linked to the expected Universal Renderer.");

            if (GraphicsSettings.defaultRenderPipeline != pipeline)
                GraphicsSettings.defaultRenderPipeline = pipeline;

            // Quality overrides take precedence over GraphicsSettings. Set
            // every level to the same asset so none can fall back to Built-In.
            int originalLevel = QualitySettings.GetQualityLevel();
            try
            {
                for (int i = 0; i < QualitySettings.names.Length; i++)
                {
                    QualitySettings.SetQualityLevel(i, false);
                    if (QualitySettings.renderPipeline != pipeline)
                        QualitySettings.renderPipeline = pipeline;
                }
            }
            finally
            {
                QualitySettings.SetQualityLevel(originalLevel, false);
            }

            AssetDatabase.SaveAssets();
            VerifyConfigured();
        }

        internal static void VerifyConfigured()
        {
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
            var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
            if (pipeline == null || renderer == null)
                throw new InvalidOperationException("URP pipeline and Universal Renderer assets are missing.");
            var rendererList = new SerializedObject(pipeline).FindProperty("m_RendererDataList");
            if (rendererList == null || rendererList.arraySize == 0 ||
                rendererList.GetArrayElementAtIndex(0).objectReferenceValue != renderer)
                throw new InvalidOperationException("URP renderer reference is missing.");

            if (GraphicsSettings.defaultRenderPipeline != pipeline ||
                GraphicsSettings.currentRenderPipeline != pipeline)
                throw new InvalidOperationException("The active Graphics render pipeline is not Rabron URP.");

            for (int i = 0; i < QualitySettings.names.Length; i++)
                if (QualitySettings.GetRenderPipelineAssetAt(i) != pipeline)
                    throw new InvalidOperationException("Quality level " + i + " is not using Rabron URP.");

            if (Shader.Find("Universal Render Pipeline/Lit") == null)
                throw new InvalidOperationException("The URP Lit shader could not be resolved.");
        }
    }
}
