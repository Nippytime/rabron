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
        DirtyCashCollected, Laundering, Laundered, Arrested
    }

    public sealed class HeistSession
    {
        private readonly List<string> _loot = new List<string>();
        private LaunderingJob? _laundering;

        public Zone CurrentZone { get; private set; }
        public PlayerRole CurrentRole { get; private set; }
        public HeistPhase Phase { get; private set; }
        public bool AlarmRaised { get; private set; }
        public bool StaffControlled { get; private set; }
        public bool BankAccountOpened { get; private set; }
        public bool CarryingCourierParcel { get; private set; }

        public long DirtyCash { get; private set; }
        public long CounterCash { get; private set; }
        public long CleanCash { get; private set; }
        public long BankBalance { get; private set; }
        public IReadOnlyList<string> Loot => _loot.AsReadOnly();
        public long? LaunderingReadyAt => _laundering?.FinishSeconds;

        public HeistSession(Zone initialZone = Zone.City, PlayerRole initialRole = PlayerRole.Civilian)
        {
            if (!Enum.IsDefined(typeof(Zone), initialZone))
                throw new ArgumentOutOfRangeException(nameof(initialZone));
            if (!Enum.IsDefined(typeof(PlayerRole), initialRole))
                throw new ArgumentOutOfRangeException(nameof(initialRole));
            // No legal transition can put a masked criminal in the desert:
            // leaving the city always clears that role before zone travel.
            if (initialZone == Zone.Desert && initialRole == PlayerRole.Criminal)
                throw new ArgumentException(
                    "A criminal cannot start outside the city.", nameof(initialRole));

            CurrentZone = initialZone;
            CurrentRole = initialRole;
            Phase = HeistPhase.Idle;
        }

        public void Scout()
        {
            Require(CurrentZone == Zone.City && Phase == HeistPhase.Idle &&
                    !CarryingCourierParcel,
                    "Finish the courier delivery before scouting a heist.");
            Phase = HeistPhase.Scouted;
        }

        public void PutOnMask()
        {
            // Complete the previous heist's city-return/reset cycle before
            // masking again. Match the Unity MASK station's Idle/Scouted gate.
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian &&
                    !CarryingCourierParcel &&
                    (Phase == HeistPhase.Idle || Phase == HeistPhase.Scouted),
                    "Masking requires an idle or scouting civilian without courier cargo in the city.");
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

        public void ControlStaff()
        {
            Require(Phase == HeistPhase.Robbing, "Staff can only be controlled during a robbery.");
            Require(!StaffControlled, "Staff is already controlled.");
            // Taking control does not retroactively cancel an existing alarm.
            StaffControlled = true;
        }

        public void TakeLoot(string itemId)
        {
            Require(Phase == HeistPhase.Robbing, "Loot is only taken during a robbery.");
            if (string.IsNullOrWhiteSpace(itemId))
                throw new ArgumentException("Loot ID cannot be blank.", nameof(itemId));
            Require(!_loot.Contains(itemId), "Duplicate loot ID.");
            _loot.Add(itemId);
        }

        /// <summary>
        /// Invented single-player guard consequence, not original police AI.
        /// The confiscation changes no clean cash or already banked funds.
        /// </summary>
        public void ArrestAfterAlarm()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Criminal &&
                    Phase == HeistPhase.Robbing && AlarmRaised && !StaffControlled,
                    "Only an alarmed criminal with an active guard can be arrested.");
            _loot.Clear();
            DirtyCash = 0;
            Phase = HeistPhase.Arrested;
        }

        public void ReleaseFromCustody()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Criminal &&
                    Phase == HeistPhase.Arrested,
                    "Release requires a criminal custody checkpoint.");
            CurrentRole = PlayerRole.Civilian;
            Phase = HeistPhase.Idle;
            AlarmRaised = false;
            StaffControlled = false;
        }

        /// <summary>
        /// Abandon an unfinished robbery without loot or a payout. This does
        /// not affect legal earnings or dirty money from earlier heists.
        /// </summary>
        public void WithdrawEmptyHanded()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Criminal &&
                    Phase == HeistPhase.Robbing && _loot.Count == 0,
                    "Only an active empty-handed robbery can be abandoned.");
            CurrentRole = PlayerRole.Civilian;
            Phase = HeistPhase.Idle;
            AlarmRaised = false;
            StaffControlled = false;
        }

        public void Escape()
        {
            Require(Phase == HeistPhase.Robbing && _loot.Count > 0,
                    "Take at least one loot item before escaping.");
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
            // Checkpoints require a positive completion timestamp on reload.
            Require(nowSeconds >= 0,
                    "Laundering start time cannot be negative.");
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
            // Leaving during a robbery, fence pickup or laundering would
            // strand the session outside its valid city-only transition path.
            Require(CurrentZone == Zone.City && !CarryingCourierParcel &&
                    (Phase == HeistPhase.Idle || Phase == HeistPhase.Scouted ||
                     Phase == HeistPhase.Laundered),
                    "Finish the current heist before leaving the city.");
            CurrentZone = Zone.Desert;
            if (CurrentRole == PlayerRole.Criminal)
                CurrentRole = PlayerRole.Civilian; // Official status reset occurs on city exit.
        }

        public void EnterCity()
        {
            Require(CurrentZone == Zone.Desert, "Already inside the city.");
            CurrentZone = Zone.City;
        }

        /// <summary>
        /// Independent civilian demo job. The pickup is persisted so a delivery
        /// cannot pay twice without acquiring a new parcel first.
        /// </summary>
        public void PickUpCourierParcel()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian &&
                    Phase == HeistPhase.Idle && !CarryingCourierParcel,
                    "Courier pickup requires an idle civilian in the city.");
            CarryingCourierParcel = true;
        }

        /// <summary>
        /// Returning the physical parcel ends the job without creating money.
        /// The civilian can then enter another career immediately.
        /// </summary>
        public void CancelCourierParcel()
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian &&
                    Phase == HeistPhase.Idle && CarryingCourierParcel,
                    "Only the active civilian courier can return a parcel.");
            CarryingCourierParcel = false;
        }

        public void DeliverCourierParcel(long verifiedCleanPayout)
        {
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian &&
                    Phase == HeistPhase.Idle && CarryingCourierParcel,
                    "Pick up the courier parcel before completing the delivery.");
            Require(verifiedCleanPayout > 0, "Courier payout must be positive.");
            // One named, explicitly configured legal-job faucet; never a
            // transfer from dirty cash or a client-authoritative server rule.
            long next = checked(CleanCash + verifiedCleanPayout);
            CleanCash = next;
            CarryingCourierParcel = false;
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
            // A completed heist must still clear criminal status by leaving
            // the city and returning as a civilian before another cycle.
            // The Unity NEXT HEIST marker already enforces this same rule.
            Require(CurrentZone == Zone.City && CurrentRole == PlayerRole.Civilian &&
                    Phase == HeistPhase.Laundered && CounterCash == 0 &&
                    _laundering == null && _loot.Count == 0,
                    "Return to the city as a civilian after laundering before restarting.");
            Phase = HeistPhase.Idle;
            AlarmRaised = false;
            StaffControlled = false;
        }

        /// <summary>Copy all authoritative state into a data-only checkpoint.</summary>
        public HeistSessionSnapshot ExportSnapshot()
        {
            return new HeistSessionSnapshot
            {
                Version = HeistSessionSnapshot.CurrentVersion,
                Zone = CurrentZone,
                Role = CurrentRole,
                Phase = Phase,
                AlarmRaised = AlarmRaised,
                StaffControlled = StaffControlled,
                BankAccountOpened = BankAccountOpened,
                CarryingCourierParcel = CarryingCourierParcel,
                CounterCash = CounterCash,
                DirtyCash = DirtyCash,
                CleanCash = CleanCash,
                BankBalance = BankBalance,
                LootIds = _loot.ToArray(),
                LaunderingInput = _laundering?.DirtyInput ?? 0,
                LaunderingPayout = _laundering?.CleanPayout ?? 0,
                LaunderingReadyAt = _laundering?.FinishSeconds ?? 0,
            };
        }

        /// <summary>
        /// Restore a saved checkpoint only after validating all fields.
        /// Import never generates extra currency or silently repairs corruption.
        /// </summary>
        public static HeistSession FromSnapshot(HeistSessionSnapshot snapshot)
        {
            if (snapshot == null)
                throw new ArgumentNullException(nameof(snapshot));

            bool supported = snapshot.Version == HeistSessionSnapshot.CurrentVersion &&
                Enum.IsDefined(typeof(Zone), snapshot.Zone) &&
                Enum.IsDefined(typeof(PlayerRole), snapshot.Role) &&
                Enum.IsDefined(typeof(HeistPhase), snapshot.Phase);
            if (!supported)
                throw new ArgumentException("Unsupported or invalid session save.", nameof(snapshot));

            // Only idle/scouted/completed sessions can legitimately exit
            // the city. Reject former core-only desert checkpoints that could
            // process unsold loot or unfinished laundering outside the map.
            if (snapshot.Zone == Zone.Desert &&
                snapshot.Phase != HeistPhase.Idle &&
                snapshot.Phase != HeistPhase.Scouted &&
                snapshot.Phase != HeistPhase.Laundered)
                throw new ArgumentException("Save contains an unreachable desert heist phase.", nameof(snapshot));

            // City departure always clears criminal status; neither entering
            // the desert nor a checkpoint can preserve a masked criminal.
            if (snapshot.Zone == Zone.Desert && snapshot.Role == PlayerRole.Criminal)
                throw new ArgumentException(
                    "Save contains an unreachable desert criminal role.", nameof(snapshot));

            // Police may scout but cannot start a robbery in this state machine.
            // Reject unreachable later phases instead of loading a forged role.
            if (snapshot.Role == PlayerRole.Police &&
                snapshot.Phase != HeistPhase.Idle && snapshot.Phase != HeistPhase.Scouted)
                throw new ArgumentException("Police role cannot occupy a robbery state.", nameof(snapshot));

            // Only a masked criminal can reach these in-flight heist stages.
            // Civilian status is restored by a safe withdrawal, custody release,
            // or city exit after laundering, never during the active cycle.
            if (snapshot.Role == PlayerRole.Civilian &&
                (snapshot.Phase == HeistPhase.Robbing ||
                 snapshot.Phase == HeistPhase.Escaped ||
                 snapshot.Phase == HeistPhase.CashOnCounter ||
                 snapshot.Phase == HeistPhase.DirtyCashCollected ||
                 snapshot.Phase == HeistPhase.Laundering))
                throw new ArgumentException(
                    "Civilian role cannot occupy an active heist state.", nameof(snapshot));

            // No operation in this local state machine grants Police money or
            // a civilian bank account. They also cannot switch to civilian.
            if (snapshot.Role == PlayerRole.Police &&
                (snapshot.BankAccountOpened || snapshot.CounterCash != 0 ||
                 snapshot.DirtyCash != 0 || snapshot.CleanCash != 0 ||
                 snapshot.BankBalance != 0))
                throw new ArgumentException("Police role cannot own civilian funds or an account.", nameof(snapshot));

            if (snapshot.CounterCash < 0 || snapshot.DirtyCash < 0 ||
                snapshot.CleanCash < 0 || snapshot.BankBalance < 0 ||
                (snapshot.BankBalance > 0 && !snapshot.BankAccountOpened))
                throw new ArgumentException("Save contains invalid money balances.", nameof(snapshot));

            string[] loot = snapshot.LootIds ?? Array.Empty<string>();
            var unique = new HashSet<string>(StringComparer.Ordinal);
            foreach (string item in loot)
            {
                if (string.IsNullOrWhiteSpace(item) || !unique.Add(item))
                    throw new ArgumentException("Save contains invalid or duplicate loot.", nameof(snapshot));
            }

            // A courier parcel can only exist before any heist or scouting,
            // in the city with its original civilian carrier.
            if (snapshot.CarryingCourierParcel &&
                (snapshot.Zone != Zone.City || snapshot.Role != PlayerRole.Civilian ||
                 snapshot.Phase != HeistPhase.Idle))
                throw new ArgumentException("Courier save contains an unreachable cargo state.", nameof(snapshot));

            // Custody has exactly one reachable shape. Legacy v1 integer
            // phases retain their previous meanings (Arrested is appended).
            if (snapshot.Phase == HeistPhase.Arrested &&
                (snapshot.Zone != Zone.City ||
                 snapshot.Role != PlayerRole.Criminal ||
                 !snapshot.AlarmRaised || snapshot.StaffControlled ||
                 snapshot.CarryingCourierParcel || snapshot.DirtyCash != 0 ||
                 snapshot.CounterCash != 0 || loot.Length != 0))
                throw new ArgumentException("Save contains an unreachable arrest state.", nameof(snapshot));

            bool isLaundering = snapshot.Phase == HeistPhase.Laundering;
            bool validJob = isLaundering
                ? snapshot.LaunderingInput > 0 &&
                  snapshot.LaunderingPayout >= 0 &&
                  snapshot.LaunderingPayout <= snapshot.LaunderingInput &&
                  snapshot.LaunderingReadyAt > 0
                : snapshot.LaunderingInput == 0 &&
                  snapshot.LaunderingPayout == 0 &&
                  snapshot.LaunderingReadyAt == 0;

            // In the actual state transitions, beginning another heist
            // clears the previous alarm and guard-control flags.
            bool beforeHeist = snapshot.Phase == HeistPhase.Idle ||
                               snapshot.Phase == HeistPhase.Scouted;
            bool validAlertStage = !beforeHeist ||
                                   (!snapshot.AlarmRaised && !snapshot.StaffControlled);

            bool lootPhase = snapshot.Phase == HeistPhase.Robbing ||
                             snapshot.Phase == HeistPhase.Escaped;
            bool counterPhase = snapshot.Phase == HeistPhase.CashOnCounter;
            bool validMoneyStage = (lootPhase || loot.Length == 0) &&
                (snapshot.Phase != HeistPhase.Escaped || loot.Length > 0) &&
                (counterPhase ? snapshot.CounterCash > 0 : snapshot.CounterCash == 0) &&
                (snapshot.Phase != HeistPhase.DirtyCashCollected || snapshot.DirtyCash > 0);

            if (!validJob || !validMoneyStage || !validAlertStage)
                throw new ArgumentException("Save contains inconsistent heist state.", nameof(snapshot));

            var session = new HeistSession(snapshot.Zone, snapshot.Role)
            {
                Phase = snapshot.Phase,
                AlarmRaised = snapshot.AlarmRaised,
                StaffControlled = snapshot.StaffControlled,
                BankAccountOpened = snapshot.BankAccountOpened,
                CarryingCourierParcel = snapshot.CarryingCourierParcel,
                CounterCash = snapshot.CounterCash,
                DirtyCash = snapshot.DirtyCash,
                CleanCash = snapshot.CleanCash,
                BankBalance = snapshot.BankBalance,
            };
            session._loot.AddRange(loot);
            if (isLaundering)
            {
                session._laundering = new LaunderingJob(snapshot.LaunderingInput,
                                                       snapshot.LaunderingPayout,
                                                       snapshot.LaunderingReadyAt);
            }
            return session;
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
