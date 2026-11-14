using System;

namespace Rabron.Reconstruction
{
    /// <summary>
    /// Versioned data-only checkpoint for the local Unity prototype.
    /// This is NOT the original game's save protocol or an authoritative server.
    /// Public fields deliberately support Unity JsonUtility without coupling
    /// the gameplay core to UnityEngine or a JSON library.
    /// </summary>
    [Serializable]
    public sealed class HeistSessionSnapshot
    {
        public const int CurrentVersion = 1;

        public int Version;
        public Zone Zone;
        public PlayerRole Role;
        public HeistPhase Phase;
        public bool AlarmRaised;
        public bool StaffControlled;
        public bool BankAccountOpened;
        public long CounterCash;
        public long DirtyCash;
        public long CleanCash;
        public long BankBalance;
        public string[] LootIds = Array.Empty<string>();
        public long LaunderingInput;
        public long LaunderingPayout;
        public long LaunderingReadyAt;
    }
}
