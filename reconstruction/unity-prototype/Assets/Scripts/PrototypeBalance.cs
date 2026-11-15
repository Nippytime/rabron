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
        [Min(1)] public int CourierReward = 35; // Provisional legal-job faucet.

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
            if (CleanPayoutPercent < 0 || CleanPayoutPercent > 100)
                throw new ArgumentOutOfRangeException(nameof(CleanPayoutPercent));

            // Integer floor(amount * percent / 100) without multiplying
            // the full 64-bit balance first. Each term fits because the
            // validated percentage is between 0 and 100.
            long whole = amount / 100;
            long remainder = amount % 100;
            return checked(whole * CleanPayoutPercent +
                           remainder * CleanPayoutPercent / 100);
        }
    }
}
