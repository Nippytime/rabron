using System;
using System.IO;
using Rabron.Reconstruction;
using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Single-player demo checkpoint. File access is confined to this Unity
    /// adapter; the portable gameplay core only exposes validated snapshots.
    /// No cloud account, original game's protocol or speculative server logic.
    /// </summary>
    public static class PrototypeSaveStore
    {
        private const string FileName = "rabron-prototype-v1.json";
        // Once recovery fails, auto-save must not destroy the original
        // unreadable primary/backup that a player may still recover manually.
        // Reset only on a new Load after the player has moved those files.
        private static bool _preserveUnreadableSaves;
        // Headless standalone acceptance must not touch real player saves.
        private static readonly string PlayerSmokeInvocationId =
            Guid.NewGuid().ToString("N");
        // Read-only UI signal; never interpret an in-memory fallback as saved.
        public static bool SavingDisabled => _preserveUnreadableSaves;
#if UNITY_EDITOR
        // A fixed test-cache path lets a later -runTests process reload stale
        // arrests or courier jobs from an earlier NUnit execution. Generate one
        // path per loaded Editor domain; all reads/writes within it stay stable.
        // Normal gameplay never uses this identifier.
        private static readonly string TestInvocationId = Guid.NewGuid().ToString("N");
#endif

        public static string SavePath
        {
            get
            {
#if UNITY_EDITOR
                // Unity's batchmode Play Mode acceptance tests must never
                // read or overwrite the developer's normal demo progress.
                if (Array.Exists(Environment.GetCommandLineArgs(),
                    arg => string.Equals(arg, "-runTests",
                                         StringComparison.OrdinalIgnoreCase)))
                    return Path.Combine(Application.temporaryCachePath,
                                        "rabron-playmode-tests", TestInvocationId,
                                        FileName);
#endif
                if (!Application.isEditor &&
                    Array.Exists(Environment.GetCommandLineArgs(),
                        arg => string.Equals(arg, "-rabronPlayerSmoke",
                                             StringComparison.OrdinalIgnoreCase)))
                    return Path.Combine(Application.temporaryCachePath,
                                        "rabron-player-smoke", PlayerSmokeInvocationId,
                                        FileName);
                return Path.Combine(Application.persistentDataPath, FileName);
            }
        }

        public static HeistSession Load(out string message)
        {
            _preserveUnreadableSaves = false;
            string primary = SavePath;
            string backup = primary + ".bak";
            Debug.Log("Rabron demo save path: " + primary);

            if (TryRead(primary, out HeistSession session))
            {
                message = "Previous local demo progress restored.";
                return session;
            }
            if (TryRead(backup, out session))
            {
                message = "Primary save invalid; recovered previous local checkpoint.";
                Debug.LogWarning("Recovered Rabron prototype save from " + backup);
                try
                {
                    // Keep the recovered checkpoint safe before future writes.
                    File.Copy(backup, primary, overwrite: true);
                }
                catch (Exception exception)
                {
                    // Backup is the only proven good checkpoint; never let
                    // later File.Replace overwrite it with a corrupt primary.
                    _preserveUnreadableSaves = true;
                    message = "Backup restored in memory, but repairing the primary failed. " +
                              "Saves are paused; copy the save files to safety and restart.";
                    Debug.LogWarning("Could not repair primary save: " + exception.Message);
                }
                return session;
            }

            _preserveUnreadableSaves = File.Exists(primary) || File.Exists(backup);
            message = _preserveUnreadableSaves
                ? "Saved progress is unreadable. Starting fresh without saving; " +
                  "copy or move the existing save and backup files, then restart."
                : "New local demo session started.";
            if (_preserveUnreadableSaves)
                Debug.LogWarning(message + " Location: " + primary);
            return new HeistSession();
        }

        public static bool TrySave(HeistSession session, out string error)
        {
            if (session == null)
                throw new ArgumentNullException(nameof(session));

            if (_preserveUnreadableSaves)
            {
                error = "Autosave disabled to preserve unreadable checkpoints. " +
                        "Copy or move the save and .bak files, then restart.";
                return false;
            }

            string target = SavePath;
            string temporary = target + ".tmp";
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string json = JsonUtility.ToJson(session.ExportSnapshot());
                File.WriteAllText(temporary, json);

                if (File.Exists(target))
                    File.Replace(temporary, target, target + ".bak");
                else
                    File.Move(temporary, target);

                error = "";
                return true;
            }
            catch (Exception exception)
            {
                error = exception.Message;
                Debug.LogWarning("Local prototype save failed: " + exception);
                return false;
            }
        }

        private static bool TryRead(string path, out HeistSession session)
        {
            session = null;
            if (!File.Exists(path))
                return false;

            try
            {
                string json = File.ReadAllText(path);
                HeistSessionSnapshot checkpoint =
                    JsonUtility.FromJson<HeistSessionSnapshot>(json);
                session = HeistSession.FromSnapshot(checkpoint);
                return true;
            }
            catch (Exception exception)
            {
                // Never trust a partially written or older-version snapshot.
                Debug.LogWarning("Ignored invalid Rabron prototype save at " +
                                 path + ": " + exception.Message);
                return false;
            }
        }
    }
}
