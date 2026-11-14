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

        public static string SavePath =>
            Path.Combine(Application.persistentDataPath, FileName);

        public static HeistSession Load(out string message)
        {
            string primary = SavePath;
            string backup = primary + ".bak";

            if (TryRead(primary, out HeistSession session))
            {
                message = "Previous local demo progress restored.";
                return session;
            }
            if (TryRead(backup, out session))
            {
                message = "Primary save invalid; recovered previous local checkpoint.";
                Debug.LogWarning("Recovered Rabron prototype save from " + backup);
                return session;
            }

            message = File.Exists(primary) || File.Exists(backup)
                ? "Saved progress could not be read. Starting fresh; existing files were kept."
                : "New local demo session started.";
            if (File.Exists(primary) || File.Exists(backup))
                Debug.LogWarning(message + " Location: " + primary);
            return new HeistSession();
        }

        public static bool TrySave(HeistSession session, out string error)
        {
            if (session == null)
                throw new ArgumentNullException(nameof(session));

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
