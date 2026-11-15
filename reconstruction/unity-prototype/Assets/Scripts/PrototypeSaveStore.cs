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
        // Set after an I/O failure; cleared only by a confirmed write or a new Load.
        public static bool LastWriteFailed { get; private set; }
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
            LastWriteFailed = false;
            string primary = SavePath;
            string backup = primary + ".bak";
            string temporary = primary + ".tmp";
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
                    // A damaged primary may still contain recoverable progress.
                    // Move it aside instead of erasing it with the older backup.
                    // Same-directory rename is non-destructive, and each
                    // quarantine path is unique to avoid replacing prior data.
                    if (File.Exists(primary))
                    {
                        string damaged = primary + ".corrupt-" + Guid.NewGuid().ToString("N");
                        File.Move(primary, damaged);
                        Debug.LogWarning("Preserved damaged primary checkpoint at " + damaged);
                    }
                    // Copy only into a vacant path: races must never overwrite
                    // the primary or the sole validated backup.
                    File.Copy(backup, primary, overwrite: false);
                }
                catch (Exception exception)
                {
                    // Any failed move/repair leaves the validated backup
                    // untouched. Pausing saves prevents an unsafe rotation.
                    _preserveUnreadableSaves = true;
                    message = "Backup restored in memory, but repairing the primary failed. " +
                              "Saves are paused; copy the save files to safety and restart.";
                    Debug.LogWarning("Could not repair primary save: " + exception.Message);
                }
                return session;
            }

            // A crash during the very first write may leave ONLY a complete
            // staged .tmp checkpoint. Recover it without overwriting any
            // committed save or backup; existing damaged files stay protected.
            if (!File.Exists(primary) && !File.Exists(backup) &&
                TryRead(temporary, out session))
            {
                message = "Recovered interrupted first save from temporary checkpoint.";
                try
                {
                    File.Move(temporary, primary);
                }
                catch (Exception exception)
                {
                    // Keep the staged original intact and prevent the next
                    // auto-save from replacing the only recoverable copy.
                    _preserveUnreadableSaves = true;
                    message = "Temporary checkpoint recovered in memory, but repair failed. " +
                              "Saves are paused; copy the .tmp file to safety and restart.";
                    Debug.LogWarning("Could not promote temporary save: " + exception.Message);
                }
                return session;
            }

            // A truncated .tmp is still potential recovery evidence. A valid
            // staged file alongside unreadable primary/backup must NOT bypass
            // their protection or be silently overwritten on the next save.
            _preserveUnreadableSaves = File.Exists(primary) ||
                                       File.Exists(backup) || File.Exists(temporary);
            message = _preserveUnreadableSaves
                ? "Saved progress is unreadable. Starting fresh without saving; " +
                  "copy or move the existing save and backup files, then restart." +
                  (File.Exists(temporary) ? " Preserve the .tmp checkpoint too." : "")
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
                LastWriteFailed = false;
                return true;
            }
            catch (Exception exception)
            {
                LastWriteFailed = true;
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
