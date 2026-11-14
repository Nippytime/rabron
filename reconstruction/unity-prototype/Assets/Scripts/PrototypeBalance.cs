using System;
using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>Provisional demo tuning, NOT the original ROB RUN economy.</summary>
    [CreateAssetMenu(fileName = "DemoEconomy", menuName = "Rabron/Prototype Economy")]
    public sealed class PrototypeBalance : ScriptableObject
    {
        [Min(1)] public int ArtworkQuote = 120;
        [Min(1)] public int WatchQuote = 80;
        [Range(0, 100)] public int CleanPayoutPercent = 80;
        [Min(1)] public int LaunderingSeconds = 8;

        public long QuoteFor(string lootId) => lootId switch
        {
            "artwork-001" => ArtworkQuote,
            "watch-001" => WatchQuote,
            _ => throw new ArgumentException("No demo quote for " + lootId, nameof(lootId)),
        };

        public long CleanPayoutFor(long amount)
        {
            if (amount <= 0)
                throw new ArgumentOutOfRangeException(nameof(amount));
            return checked(amount * CleanPayoutPercent / 100);
        }
    }
}
