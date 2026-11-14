using System;
using System.Collections.Generic;

namespace Rabron.Reconstruction
{
    // This is independently authored core logic, NOT extracted IL2CPP code.
    // Economy prices, production time and exchange rates must be supplied by
    // verified data or a future authoritative server.
    public enum Zone { City, Desert }
    public enum PlayerRole { Civilian, Criminal, Police }
    public enum HeistPhase
    {
        Idle, Scouted, Robbing, Escaped, CashOnCounter,
        DirtyCashCollected, Laundering, Laundered
    }

    public sealed class HeistSession
    {
        private readonly List<string> _loot = new List<string>();
        private LaunderingJob? _laundering;

        public Zone CurrentZone { get; private set; }
        public PlayerRole CurrentRole { get; private set; }
        public HeistPhase Phase { get; private set; }
        public bool AlarmRaised { get; private set; }
        public bool BankAccountOpened { get; private set; }

        public long DirtyCash { get; private set; }
        public long CounterCash { get; private set; }
        public long CleanCash { get; private set; }
        public long BankBalance { get; private set; }
        public IReadOnlyList<string> Loot => _loot.AsReadOnly();
        public long? LaunderingReadyAt => _laundering?.FinishSeconds;

        public HeistSession(Zone initialZone = Zone.City, PlayerRole initialRole = PlayerRole.Civilian)
        {
            CurrentZone = initialZone;
            CurrentRole = initialRole;
            Phase = HeistPhase.Idle;
        }

        public void Scout()
        {
            Require(CurrentZone == Zone.City && Phase == HeistPhase.Idle,
                    "Scouting is only available in the city before a heist.");
            Phase = HeistPhase.Scouted;
        }

        public void PutOnMask()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian,
                    "Only a civilian in the city may enter criminal mode.");
            CurrentRole = PlayerRole.Criminal;
        }

        public void StartHeist()
        {
            Require(Phase == HeistPhase.Scouted && CurrentRole == PlayerRole.Criminal &&
                    CurrentZone == Zone.City, "Scout and enter criminal mode first.");
            Phase = HeistPhase.Robbing;
        }

        public void RaiseAlarm()
        {
            Require(Phase == HeistPhase.Robbing, "Alarm requires an active robbery.");
            AlarmRaised = true;
        }

        public void TakeLoot(string itemId)
        {
            Require(Phase == HeistPhase.Robbing, "Loot is only taken during a robbery.");
            if (string.IsNullOrWhiteSpace(itemId))
                throw new ArgumentException("Loot ID cannot be blank.", nameof(itemId));
            Require(!_loot.Contains(itemId), "Duplicate loot ID.");
            _loot.Add(itemId);
        }

        public void Escape()
        {
            Require(Phase == HeistPhase.Robbing, "No active robbery to escape.");
            Phase = HeistPhase.Escaped;
        }

        public void SellLoot(IReadOnlyDictionary<string, long> verifiedQuotes)
        {
            Require(Phase == HeistPhase.Escaped && _loot.Count > 0,
                    "Escape with loot before selling.");
            if (verifiedQuotes == null)
                throw new ArgumentNullException(nameof(verifiedQuotes));

            // Validate the complete sale before changing the inventory.
            long total = 0;
            checked
            {
                foreach (string item in _loot)
                {
                    if (!verifiedQuotes.TryGetValue(item, out long price) || price <= 0)
                        throw new ArgumentException("Each looted item needs a positive quote.");
                    total += price;
                }
            }

            // The official game places the sale cash on a physical counter.
            // It must be collected explicitly; it is not yet player currency.
            CounterCash = checked(CounterCash + total);
            _loot.Clear();
            Phase = HeistPhase.CashOnCounter;
        }

        public void CollectCounterCash()
        {
            Require(Phase == HeistPhase.CashOnCounter && CounterCash > 0,
                    "No cash is waiting on the counter.");
            DirtyCash = checked(DirtyCash + CounterCash);
            CounterCash = 0;
            Phase = HeistPhase.DirtyCashCollected;
        }

        public void StartLaundering(long dirtyAmount, long cleanPayout,
                                    long nowSeconds, long durationSeconds)
        {
            Require(Phase == HeistPhase.DirtyCashCollected,
                    "Collect dirty cash before laundering.");
            Require(dirtyAmount > 0 && dirtyAmount <= DirtyCash,
                    "Cannot launder more than available dirty cash.");
            Require(cleanPayout >= 0 && cleanPayout <= dirtyAmount,
                    "Conversion quote must be non-negative and cannot mint value.");
            Require(durationSeconds > 0,
                    "A positive laundering duration must be supplied.");
            long finish = checked(nowSeconds + durationSeconds);
            _laundering = new LaunderingJob(dirtyAmount, cleanPayout, finish);
            DirtyCash -= dirtyAmount;
            Phase = HeistPhase.Laundering;
        }

        public void CompleteLaundering(long nowSeconds)
        {
            Require(Phase == HeistPhase.Laundering && _laundering != null,
                    "No laundering job is active.");
            LaunderingJob job = _laundering!;
            Require(nowSeconds >= job.FinishSeconds, "Laundering time has not elapsed.");
            CleanCash = checked(CleanCash + job.CleanPayout);
            _laundering = null;
            Phase = HeistPhase.Laundered;
        }

        public void LeaveCity()
        {
            Require(CurrentZone == Zone.City, "Already outside the city.");
            CurrentZone = Zone.Desert;
            if (CurrentRole == PlayerRole.Criminal)
                CurrentRole = PlayerRole.Civilian; // Official status reset occurs on city exit.
        }

        public void EnterCity()
        {
            Require(CurrentZone == Zone.Desert, "Already inside the city.");
            CurrentZone = Zone.City;
        }

        public void OpenBankAccount()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian,
                    "A civilian must open the account inside the city.");
            BankAccountOpened = true;
        }

        public void DepositCleanCash(long amount)
        {
            Require(BankAccountOpened && CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian,
                    "Bank deposits require a civilian account holder in the city.");
            Require(amount > 0 && amount <= CleanCash,
                    "Cannot deposit more clean cash than owned.");
            BankBalance = checked(BankBalance + amount);
            CleanCash -= amount;
        }

        public void BeginAnotherHeist()
        {
            Require(Phase == HeistPhase.Laundered && CounterCash == 0 &&
                    _laundering == null && _loot.Count == 0,
                    "Finish the current heist and laundering first.");
            Phase = HeistPhase.Idle;
            AlarmRaised = false;
        }

        private static void Require(bool condition, string reason)
        {
            if (!condition)
                throw new InvalidOperationException(reason);
        }

        private sealed class LaunderingJob
        {
            public long DirtyInput { get; }
            public long CleanPayout { get; }
            public long FinishSeconds { get; }

            public LaunderingJob(long dirtyInput, long cleanPayout, long finishSeconds)
            {
                DirtyInput = dirtyInput;
                CleanPayout = cleanPayout;
                FinishSeconds = finishSeconds;
            }
        }
    }
}
