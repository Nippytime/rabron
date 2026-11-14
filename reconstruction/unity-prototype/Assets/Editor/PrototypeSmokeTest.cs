using System;
using System.Collections.Generic;
using System.IO;
using Rabron.Reconstruction;
using UnityEditor;
using UnityEngine;

namespace Rabron.Prototype.Editor
{
    /// <summary>
    /// Runs inside a real Unity 6000 Editor, not a mocked .NET environment.
    /// CLI: -executeMethod Rabron.Prototype.Editor.PrototypeSmokeTest.ValidateProject
    /// </summary>
    public static class PrototypeSmokeTest
    {
        private const string PassToken = "RABRON_UNITY_EDITOR_SMOKE_PASS";
        private const string BuildToken = "RABRON_UNITY_WINDOWS_BUILD_PASS";

        [MenuItem("Tools/Rabron/Verify Unity Prototype")]
        public static void ValidateProject()
        {
            PrototypeSceneInstaller.EnsureScene();

            var root = new GameObject("Temporary prototype verification");
            try
            {
                var stations = PrototypeWorld.Create(root.transform, out var player);
                var kinds = new HashSet<StationAction>();
                foreach (var station in stations)
                {
                    Check(station != null && station.gameObject.activeSelf,
                          "A gameplay station was not instantiated");
                    Check(station.GetComponent<Collider>().isTrigger,
                          "A gameplay station obstructs player movement");
                    Check(kinds.Add(station.Action),
                          "Duplicate gameplay action " + station.Action);
                }

                var expected = (StationAction[])Enum.GetValues(typeof(StationAction));
                Check(stations.Count == expected.Length,
                      "Missing interaction markers: " + stations.Count);
                foreach (var action in expected)
                    Check(kinds.Contains(action), "Missing station " + action);

                Check(player != null, "No CharacterController motor created");
                var capsule = player.GetComponent<CharacterController>();
                Check(capsule != null && capsule.stepOffset >= 0.5f,
                      "Fencing platform is not reachable by walking");
                Check(root.transform.Find("Ground") != null,
                      "No collidable ground was created");

                ValidateHeistCore();
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }

            Debug.Log(PassToken + ": procedural scene, stations, colliders, and heist core verified");
        }

        /// <summary>
        /// Use -buildTarget StandaloneWindows64 on the Unity CLI.
        /// Does NOT assert that the built executable has been interactively played.
        /// </summary>
        public static void ValidateAndBuildWindows()
        {
            ValidateProject();
            PrototypeSceneInstaller.BuildWindows();

            string executable = Path.GetFullPath("Builds/RabronPrototype.exe");
            Check(File.Exists(executable), "Build succeeded but executable is missing: " + executable);
            Check(Directory.Exists(Path.GetFullPath("Builds/RabronPrototype_Data")),
                  "Windows build data folder is missing");
            Debug.Log(BuildToken + ": " + executable);
        }

        private static void ValidateHeistCore()
        {
            // Numbers here are deliberately fixture data, not original rates.
            var session = new HeistSession();
            session.Scout();
            session.PutOnMask();
            session.StartHeist();
            session.TakeLoot("smoke-loot-01");
            session.Escape();
            session.SellLoot(new Dictionary<string, long>
            {
                ["smoke-loot-01"] = 20
            });
            Check(session.CounterCash == 20 && session.DirtyCash == 0,
                  "Fencing skipped collectible counter cash");

            session.CollectCounterCash();
            session.StartLaundering(20, 15, 100, 5);
            Check(session.LaunderingReadyAt == 105,
                  "Laundering deadline is incorrect");
            session.CompleteLaundering(105);
            session.LeaveCity();
            session.EnterCity();
            session.OpenBankAccount();
            session.DepositCleanCash(15);
            Check(session.BankBalance == 15 && session.CleanCash == 0,
                  "Clean cash was not deposited");
        }

        private static void Check(bool condition, string reason)
        {
            if (!condition)
                throw new InvalidOperationException(reason);
        }
    }
}
