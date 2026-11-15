using System;
using System.Collections.Generic;
using Rabron.Reconstruction;

internal static class Program
{
    private static int Main()
    {
        Action[] tests =
        {
            FullLootToBankLoop,
            EnforcesRoleAndZoneRequirements,
            RequiresCollectedPhysicalCash,
            SaleQuotesAreAtomicAndPositive,
            EnforcesLaunderingDeadlineAndInput,
            RejectsDuplicateItems,
            ResetsOnlyTheHeistCycle,
            CompletedHeistRequiresCivilianCityReturnBeforeReset,
            ControlledStaffPreventsFutureAlarmWithoutRewritingThePast,
            StaffControlMustOccurDuringHeist,
            SnapshotRestoresInFlightLootAndGuardState,
            SnapshotPreservesPhysicalCounterCash,
            SnapshotPreservesLaunderingDeadline,
            SnapshotPreservesBankAcrossHeists,
            SnapshotRejectsInvalidOrTamperedState,
            SnapshotRejectsUnreachablePoliceRobberyPhases,
            SnapshotRejectsCivilianInActiveHeistStages,
            ConstructorRejectsUnknownRolesAndZones,
            SnapshotRejectsUnreachablePoliceEconomy,
            LaunderingRejectsUnrestorableTimestamps,
            CourierDeliveryPaysOnceAndDepositsCleanCash,
            CourierCargoPersistsAndRejectsUnreachableSaves,
            CourierDeliveryOverflowIsAtomic,
            CourierCancellationNeverCreditsCash,
            ArrestConfiscatesLootAndPreservesLegalMoney,
            ArrestSnapshotCannotForgeRolesOrRewards,
            EmptyHandedWithdrawalRestoresPlayWithoutEarningCash,
            EmptyEscapeAndForgedCheckpointAreRejected,
            ActiveHeistsCannotLeaveCityOrForgeDesertSaves,
            IdleScoutedAndLaunderedCanTravelWithBalances,
            RejectsUnreachableDesertCriminalRoles,
        };

        foreach (Action test in tests)
        {
            try
            {
                test();
                Console.WriteLine("PASS " + test.Method.Name);
            }
            catch (Exception error)
            {
                Console.Error.WriteLine("FAIL " + test.Method.Name + ": " + error);
                return 1;
            }
        }

        Console.WriteLine("All " + tests.Length + " independent gameplay tests passed.");
        return 0;
    }

    private static void FullLootToBankLoop()
    {
        var game = new HeistSession();
        game.OpenBankAccount();
        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.TakeLoot("painting-1");
        game.TakeLoot("watch-1");
        game.RaiseAlarm();
        game.Escape();
        game.SellLoot(new Dictionary<string, long>
        {
            ["painting-1"] = 120,
            ["watch-1"] = 80,
        });

        Eq(HeistPhase.CashOnCounter, game.Phase);
        Eq(200L, game.CounterCash);
        Eq(0L, game.DirtyCash);
        Eq(0, game.Loot.Count);
        game.CollectCounterCash();
        Eq(0L, game.CounterCash);
        Eq(200L, game.DirtyCash);

        // These quotes and times are TEST FIXTURES, not original game values.
        game.StartLaundering(200, 160, nowSeconds: 5000, durationSeconds: 30);
        Eq(0L, game.DirtyCash);
        Throws<InvalidOperationException>(() => game.CompleteLaundering(5029));
        game.CompleteLaundering(5030);
        Eq(160L, game.CleanCash);

        Throws<InvalidOperationException>(() => game.DepositCleanCash(160));
        game.LeaveCity();
        Eq(PlayerRole.Civilian, game.CurrentRole);
        game.EnterCity();
        game.DepositCleanCash(160);
        Eq(160L, game.BankBalance);
        Eq(0L, game.CleanCash);
        True(game.AlarmRaised);
    }

    private static void EnforcesRoleAndZoneRequirements()
    {
        var desert = new HeistSession(Zone.Desert);
        Throws<InvalidOperationException>(() => desert.Scout());
        Throws<InvalidOperationException>(() => desert.PutOnMask());
        Throws<InvalidOperationException>(() => desert.OpenBankAccount());
        desert.EnterCity();
        desert.Scout();
        Throws<InvalidOperationException>(() => desert.StartHeist());
        desert.PutOnMask();
        Throws<InvalidOperationException>(() => desert.OpenBankAccount());

        var police = new HeistSession(Zone.City, PlayerRole.Police);
        Throws<InvalidOperationException>(() => police.PutOnMask());
    }

    private static void RequiresCollectedPhysicalCash()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 50 });
        Throws<InvalidOperationException>(() =>
            game.StartLaundering(50, 40, 100, 10));
        Eq(50L, game.CounterCash);
        Eq(0L, game.DirtyCash);
    }

    private static void SaleQuotesAreAtomicAndPositive()
    {
        var game = StartHeistWithOneItem();
        game.TakeLoot("watch");
        game.Escape();
        Throws<ArgumentException>(() =>
            game.SellLoot(new Dictionary<string, long> { ["camera"] = 10 }));
        Throws<ArgumentException>(() =>
            game.SellLoot(new Dictionary<string, long>
            {
                ["camera"] = 10, ["watch"] = -1,
            }));
        Eq(0L, game.CounterCash);
        Eq(2, game.Loot.Count);
        Eq(HeistPhase.Escaped, game.Phase);
    }

    private static void EnforcesLaunderingDeadlineAndInput()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 50 });
        game.CollectCounterCash();
        Throws<InvalidOperationException>(() =>
            game.StartLaundering(51, 1, 100, 10));
        Throws<InvalidOperationException>(() =>
            game.StartLaundering(50, 51, 100, 10));
        Throws<InvalidOperationException>(() =>
            game.StartLaundering(50, 25, 100, 0));
        Eq(50L, game.DirtyCash);
        game.StartLaundering(50, 45, 100, 10);
        Throws<InvalidOperationException>(() => game.BeginAnotherHeist());
        game.CompleteLaundering(110);
        Eq(45L, game.CleanCash);
    }

    private static void RejectsDuplicateItems()
    {
        var game = StartHeistWithOneItem();
        Throws<InvalidOperationException>(() => game.TakeLoot("camera"));
        Throws<ArgumentException>(() => game.TakeLoot(""));
        Eq(1, game.Loot.Count);
    }

    private static void ResetsOnlyTheHeistCycle()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        game.CollectCounterCash();
        game.StartLaundering(100, 60, 1000, 20);
        game.CompleteLaundering(1020);
        game.LeaveCity();
        game.EnterCity();
        game.BeginAnotherHeist();
        Eq(HeistPhase.Idle, game.Phase);
        Eq(60L, game.CleanCash);
        Eq(0, game.Loot.Count);
        True(!game.AlarmRaised);
        game.Scout();
    }

    private static void CompletedHeistRequiresCivilianCityReturnBeforeReset()
    {
        var game = new HeistSession();
        game.OpenBankAccount();
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(30);
        game.DepositCleanCash(10);

        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.RaiseAlarm();
        game.ControlStaff();
        game.TakeLoot("camera");
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        game.CollectCounterCash();
        game.StartLaundering(100, 70, 1000, 5);
        game.CompleteLaundering(1005);

        Eq(HeistPhase.Laundered, game.Phase);
        Eq(PlayerRole.Criminal, game.CurrentRole);
        Eq(90L, game.CleanCash);
        Eq(10L, game.BankBalance);
        Throws<InvalidOperationException>(() => game.BeginAnotherHeist());
        Eq(HeistPhase.Laundered, game.Phase);
        True(game.AlarmRaised && game.StaffControlled);
        Eq(90L, game.CleanCash);
        Eq(10L, game.BankBalance);

        game.LeaveCity();
        Eq(PlayerRole.Civilian, game.CurrentRole);
        Eq(Zone.Desert, game.CurrentZone);
        Throws<InvalidOperationException>(() => game.BeginAnotherHeist());
        Eq(HeistPhase.Laundered, game.Phase);
        Eq(90L, game.CleanCash);
        Eq(10L, game.BankBalance);

        // Only after returning as a civilian may the next-heist marker
        // semantics be satisfied by the portable state machine itself.
        game.EnterCity();
        game.BeginAnotherHeist();
        Eq(HeistPhase.Idle, game.Phase);
        Eq(PlayerRole.Civilian, game.CurrentRole);
        Eq(Zone.City, game.CurrentZone);
        True(!game.AlarmRaised && !game.StaffControlled);
        Eq(90L, game.CleanCash);
        Eq(10L, game.BankBalance);
        game.Scout();
    }

    private static void ControlledStaffPreventsFutureAlarmWithoutRewritingThePast()
    {
        var session = StartHeistWithOneItem();
        session.RaiseAlarm();
        session.ControlStaff();
        True(session.StaffControlled);
        True(session.AlarmRaised);

        // The next heist must start with a fresh staff/alarm state.
        session.Escape();
        session.SellLoot(new Dictionary<string, long> { ["camera"] = 20 });
        session.CollectCounterCash();
        session.StartLaundering(20, 15, 100, 2);
        session.CompleteLaundering(102);
        session.LeaveCity();
        session.EnterCity();
        session.BeginAnotherHeist();
        True(!session.StaffControlled);
        True(!session.AlarmRaised);
    }

    private static void StaffControlMustOccurDuringHeist()
    {
        var session = new HeistSession();
        Throws<InvalidOperationException>(() => session.ControlStaff());
        session.Scout();
        session.PutOnMask();
        Throws<InvalidOperationException>(() => session.ControlStaff());
        session.StartHeist();
        session.ControlStaff();
        Throws<InvalidOperationException>(() => session.ControlStaff());
        True(session.StaffControlled);
        // Escaping is now legal only when a real loot item was collected.
        session.TakeLoot("control-guard-fixture");
        session.Escape();
        Throws<InvalidOperationException>(() => session.ControlStaff());
    }

    private static void SnapshotRestoresInFlightLootAndGuardState()
    {
        var game = StartHeistWithOneItem();
        game.ControlStaff();
        game.RaiseAlarm();

        HeistSessionSnapshot data = game.ExportSnapshot();
        Eq(HeistSessionSnapshot.CurrentVersion, data.Version);
        Eq(1, data.LootIds.Length);

        // Exporting cannot let a caller mutate the live inventory.
        data.LootIds[0] = "external-modification";
        Eq("camera", game.Loot[0]);

        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());
        Eq(HeistPhase.Robbing, restored.Phase);
        Eq(PlayerRole.Criminal, restored.CurrentRole);
        True(restored.AlarmRaised);
        True(restored.StaffControlled);
        Eq("camera", restored.Loot[0]);
        restored.TakeLoot("watch");
        Eq(2, restored.Loot.Count);
        Eq(1, game.Loot.Count);
    }

    private static void SnapshotPreservesPhysicalCounterCash()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 75 });

        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());
        Eq(HeistPhase.CashOnCounter, restored.Phase);
        Eq(75L, restored.CounterCash);
        Eq(0L, restored.DirtyCash);
        restored.CollectCounterCash();
        Eq(0L, restored.CounterCash);
        Eq(75L, restored.DirtyCash);
    }

    private static void SnapshotPreservesLaunderingDeadline()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 50 });
        game.CollectCounterCash();
        game.StartLaundering(50, 40, nowSeconds: 1000, durationSeconds: 20);

        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());
        Eq(HeistPhase.Laundering, restored.Phase);
        Eq(1020L, restored.LaunderingReadyAt!.Value);
        Eq(0L, restored.CleanCash);
        Throws<InvalidOperationException>(() => restored.CompleteLaundering(1019));
        restored.CompleteLaundering(1020);
        Eq(40L, restored.CleanCash);
        Eq(0L, restored.DirtyCash);
        Eq(null, restored.LaunderingReadyAt);
    }

    private static void SnapshotPreservesBankAcrossHeists()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        game.CollectCounterCash();
        game.StartLaundering(100, 80, 100, 10);
        game.CompleteLaundering(110);
        game.LeaveCity();
        game.EnterCity();
        game.OpenBankAccount();
        game.DepositCleanCash(80);
        game.BeginAnotherHeist();
        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());

        Eq(HeistPhase.Idle, restored.Phase);
        Eq(80L, restored.BankBalance);
        Eq(PlayerRole.Civilian, restored.CurrentRole);
        True(restored.BankAccountOpened);
        restored.Scout();
        restored.PutOnMask();
        restored.StartHeist();
        Eq(80L, restored.BankBalance);
    }

    private static void SnapshotRejectsInvalidOrTamperedState()
    {
        var game = StartHeistWithOneItem();
        var unsupported = game.ExportSnapshot();
        unsupported.Version = 99;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(unsupported));

        var invalidEnum = game.ExportSnapshot();
        invalidEnum.Phase = (HeistPhase)999;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(invalidEnum));

        var duplicate = game.ExportSnapshot();
        duplicate.LootIds = new[] { "camera", "camera" };
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(duplicate));

        var blank = game.ExportSnapshot();
        blank.LootIds = new[] { " " };
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(blank));

        var negative = game.ExportSnapshot();
        negative.BankBalance = -1;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(negative));

        var withoutAccount = game.ExportSnapshot();
        withoutAccount.BankBalance = 20;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(withoutAccount));

        var fakeCounter = game.ExportSnapshot();
        fakeCounter.CounterCash = 200;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeCounter));

        var impossibleEarlyAlarm = new HeistSession().ExportSnapshot();
        impossibleEarlyAlarm.AlarmRaised = true;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(impossibleEarlyAlarm));

        var impossibleEarlyGuard = new HeistSession().ExportSnapshot();
        impossibleEarlyGuard.StaffControlled = true;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(impossibleEarlyGuard));

        var invalidJob = game.ExportSnapshot();
        invalidJob.Phase = HeistPhase.Laundering;
        invalidJob.LootIds = Array.Empty<string>();
        invalidJob.LaunderingInput = 10;
        invalidJob.LaunderingPayout = 11;
        invalidJob.LaunderingReadyAt = 1000;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(invalidJob));

        var missingJob = game.ExportSnapshot();
        missingJob.Phase = HeistPhase.Laundering;
        missingJob.LootIds = Array.Empty<string>();
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(missingJob));

        Throws<ArgumentNullException>(() => HeistSession.FromSnapshot(null!));
    }

    private static void SnapshotRejectsCivilianInActiveHeistStages()
    {
        var game = new HeistSession();
        game.OpenBankAccount();
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(20);
        game.DepositCleanCash(10);
        game.Scout();
        Eq(PlayerRole.Civilian, HeistSession.FromSnapshot(
            game.ExportSnapshot()).CurrentRole);

        game.PutOnMask();
        game.StartHeist();

        void AssertStage()
        {
            // The actual criminal save must remain reloadable.
            var checkpoint = game.ExportSnapshot();
            Eq(PlayerRole.Criminal, HeistSession.FromSnapshot(checkpoint).CurrentRole);
            checkpoint.Role = PlayerRole.Civilian;
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(checkpoint));
        }

        AssertStage(); // Robbing without loot
        game.TakeLoot("camera");
        AssertStage(); // Robbing with loot
        game.Escape();
        AssertStage(); // Escaped
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 30 });
        AssertStage(); // Cash on counter
        game.CollectCounterCash();
        AssertStage(); // Dirty cash collected
        game.StartLaundering(30, 25, 100, 2);
        AssertStage(); // Laundering in progress

        game.CompleteLaundering(102);
        Eq(PlayerRole.Criminal, HeistSession.FromSnapshot(
            game.ExportSnapshot()).CurrentRole);
        game.LeaveCity(); // Legitimate transition to civilian after laundering
        Eq(PlayerRole.Civilian, HeistSession.FromSnapshot(
            game.ExportSnapshot()).CurrentRole);
        game.EnterCity();
        Eq(PlayerRole.Civilian, HeistSession.FromSnapshot(
            game.ExportSnapshot()).CurrentRole);
        Eq(10L, game.BankBalance);
        Eq(35L, game.CleanCash); // Prior legal cash plus completed laundering
    }

    private static void SnapshotRejectsUnreachablePoliceRobberyPhases()
    {
        var police = new HeistSession(Zone.City, PlayerRole.Police);
        Eq(PlayerRole.Police, HeistSession.FromSnapshot(police.ExportSnapshot()).CurrentRole);
        police.Scout();
        Eq(HeistPhase.Scouted, HeistSession.FromSnapshot(police.ExportSnapshot()).Phase);

        var game = StartHeistWithOneItem();
        void RejectSpoofedPolice()
        {
            var snapshot = game.ExportSnapshot();
            snapshot.Role = PlayerRole.Police;
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(snapshot));
        }

        RejectSpoofedPolice(); // Robbing
        game.Escape();
        RejectSpoofedPolice(); // Escaped
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 30 });
        RejectSpoofedPolice(); // CashOnCounter
        game.CollectCounterCash();
        RejectSpoofedPolice(); // DirtyCashCollected
        game.StartLaundering(30, 25, 0, 2);
        RejectSpoofedPolice(); // Laundering
        game.CompleteLaundering(2);
        RejectSpoofedPolice(); // Laundered

        // Leaving the city legitimately resets a criminal to civilian.
        game.LeaveCity();
        Eq(PlayerRole.Civilian, HeistSession.FromSnapshot(game.ExportSnapshot()).CurrentRole);
    }

    private static void ConstructorRejectsUnknownRolesAndZones()
    {
        Throws<ArgumentOutOfRangeException>(() => new HeistSession((Zone)123));
        Throws<ArgumentOutOfRangeException>(() => new HeistSession((Zone)(-1)));
        Throws<ArgumentOutOfRangeException>(() =>
            new HeistSession(Zone.City, (PlayerRole)123));
        Throws<ArgumentOutOfRangeException>(() =>
            new HeistSession(Zone.Desert, (PlayerRole)(-1)));

        // Legitimate Police and civilian initial states remain available in both zones.
        foreach (Zone zone in new[] { Zone.City, Zone.Desert })
        {
            Eq(zone, new HeistSession(zone, PlayerRole.Police).CurrentZone);
            Eq(zone, new HeistSession(zone, PlayerRole.Civilian).CurrentZone);
        }
    }

    private static void SnapshotRejectsUnreachablePoliceEconomy()
    {
        // Police can legitimately be idle or scouted, in the city or desert.
        // Neither opening an account nor earning cash is reachable for Police.
        foreach (Zone zone in new[] { Zone.City, Zone.Desert })
        {
            foreach (bool scouted in new[] { false, true })
            {
                var police = new HeistSession(Zone.City, PlayerRole.Police);
                if (scouted)
                    police.Scout();
                if (zone == Zone.Desert)
                    police.LeaveCity();

                var baseline = police.ExportSnapshot();
                Eq(zone, HeistSession.FromSnapshot(baseline).CurrentZone);
                Eq(scouted ? HeistPhase.Scouted : HeistPhase.Idle,
                   HeistSession.FromSnapshot(baseline).Phase);
                Eq(PlayerRole.Police, HeistSession.FromSnapshot(baseline).CurrentRole);

                var fakeAccount = police.ExportSnapshot();
                fakeAccount.BankAccountOpened = true;
                Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeAccount));

                var fakeCounter = police.ExportSnapshot();
                fakeCounter.CounterCash = 1;
                Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeCounter));

                var fakeDirty = police.ExportSnapshot();
                fakeDirty.DirtyCash = 1;
                Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeDirty));

                var fakeClean = police.ExportSnapshot();
                fakeClean.CleanCash = 1;
                Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeClean));

                var fakeBank = police.ExportSnapshot();
                fakeBank.BankAccountOpened = true;
                fakeBank.BankBalance = 1;
                Throws<ArgumentException>(() => HeistSession.FromSnapshot(fakeBank));
            }
        }

        // A civilian may legitimately hold an opened account with no funds.
        var civilian = new HeistSession(Zone.City, PlayerRole.Civilian);
        civilian.OpenBankAccount();
        True(HeistSession.FromSnapshot(civilian.ExportSnapshot()).BankAccountOpened);

        // A criminal's legitimate funds and bank account must not be rejected.
        civilian.Scout();
        civilian.PutOnMask();
        civilian.StartHeist();
        civilian.TakeLoot("camera");
        civilian.Escape();
        civilian.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        civilian.CollectCounterCash();
        civilian.StartLaundering(60, 45, 10, 2);
        civilian.CompleteLaundering(12);
        var criminal = HeistSession.FromSnapshot(civilian.ExportSnapshot());
        Eq(40L, criminal.DirtyCash);
        Eq(45L, criminal.CleanCash);
        True(criminal.BankAccountOpened);

        criminal.LeaveCity();
        criminal.EnterCity();
        criminal.DepositCleanCash(45);
        var returnedCivilian = HeistSession.FromSnapshot(criminal.ExportSnapshot());
        Eq(PlayerRole.Civilian, returnedCivilian.CurrentRole);
        Eq(45L, returnedCivilian.BankBalance);
        Eq(40L, returnedCivilian.DirtyCash);
    }

    private static void LaunderingRejectsUnrestorableTimestamps()
    {
        var game = StartHeistWithOneItem();
        game.Escape();
        game.SellLoot(new Dictionary<string, long> { ["camera"] = 30 });
        game.CollectCounterCash();

        Throws<InvalidOperationException>(() => game.StartLaundering(30, 25, -1, 10));
        Throws<OverflowException>(() => game.StartLaundering(30, 25, long.MaxValue, 1));
        Eq(HeistPhase.DirtyCashCollected, game.Phase);
        Eq(30L, game.DirtyCash);

        // Time zero is valid and the produced job survives save/reload.
        game.StartLaundering(30, 25, 0, 1);
        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());
        Eq(1L, restored.LaunderingReadyAt!.Value);
        Throws<InvalidOperationException>(() => restored.CompleteLaundering(0));
        restored.CompleteLaundering(1);
        Eq(25L, restored.CleanCash);
    }

    private static void CourierDeliveryPaysOnceAndDepositsCleanCash()
    {
        var game = new HeistSession();
        game.OpenBankAccount();
        Throws<InvalidOperationException>(() => game.DeliverCourierParcel(40));

        game.PickUpCourierParcel();
        True(game.CarryingCourierParcel);
        Throws<InvalidOperationException>(() => game.PickUpCourierParcel());
        Throws<InvalidOperationException>(() => game.DeliverCourierParcel(0));
        Throws<InvalidOperationException>(() => game.DeliverCourierParcel(-1));
        Eq(0L, game.CleanCash);
        True(game.CarryingCourierParcel);

        game.DeliverCourierParcel(40); // Fixture, not an original courier quote.
        True(!game.CarryingCourierParcel);
        Eq(40L, game.CleanCash);
        Eq(0L, game.DirtyCash);
        Eq(0L, game.CounterCash);
        Throws<InvalidOperationException>(() => game.DeliverCourierParcel(40));
        game.DepositCleanCash(40);
        Eq(40L, game.BankBalance);

        // Another reward requires another explicit pickup; no replay credit.
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(25);
        Eq(25L, game.CleanCash);
        Eq(40L, game.BankBalance);
        Eq(HeistPhase.Idle, game.Phase);
    }

    private static void CourierCargoPersistsAndRejectsUnreachableSaves()
    {
        var game = new HeistSession();
        game.PickUpCourierParcel();
        Throws<InvalidOperationException>(() => game.Scout());
        Throws<InvalidOperationException>(() => game.PutOnMask());
        Throws<InvalidOperationException>(() => game.LeaveCity());

        var checkpoint = game.ExportSnapshot();
        var resumed = HeistSession.FromSnapshot(checkpoint);
        True(resumed.CarryingCourierParcel);
        Eq(0L, resumed.CleanCash);
        resumed.DeliverCourierParcel(15);
        Eq(15L, resumed.CleanCash);
        Throws<InvalidOperationException>(() => resumed.DeliverCourierParcel(15));
        // Mutating the exported checkpoint cannot affect the restored session.
        checkpoint.CarryingCourierParcel = false;
        Eq(15L, resumed.CleanCash);

        void Reject(Action<HeistSessionSnapshot> mutate)
        {
            var forged = game.ExportSnapshot();
            mutate(forged);
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(forged));
        }

        Reject(data => data.Zone = Zone.Desert);
        Reject(data => data.Role = PlayerRole.Criminal);
        Reject(data => data.Role = PlayerRole.Police);
        Reject(data => data.Phase = HeistPhase.Scouted);
        Reject(data => data.Phase = HeistPhase.Robbing);
        Reject(data => data.Phase = HeistPhase.Laundered);

        // Legacy v1 checkpoints have no cargo field, thus read as false.
        var legacy = new HeistSession().ExportSnapshot();
        legacy.CarryingCourierParcel = false;
        True(!HeistSession.FromSnapshot(legacy).CarryingCourierParcel);

        Throws<InvalidOperationException>(() =>
            new HeistSession(Zone.Desert).PickUpCourierParcel());
        Throws<InvalidOperationException>(() =>
            new HeistSession(Zone.City, PlayerRole.Police).PickUpCourierParcel());
        var criminal = new HeistSession();
        criminal.PutOnMask();
        Throws<InvalidOperationException>(() => criminal.PickUpCourierParcel());
        var scouted = new HeistSession();
        scouted.Scout();
        Throws<InvalidOperationException>(() => scouted.PickUpCourierParcel());
    }

    private static void CourierDeliveryOverflowIsAtomic()
    {
        var game = new HeistSession();
        game.OpenBankAccount();
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(long.MaxValue);
        Eq(long.MaxValue, game.CleanCash);

        game.PickUpCourierParcel();
        Throws<OverflowException>(() => game.DeliverCourierParcel(1));
        Eq(long.MaxValue, game.CleanCash);
        True(game.CarryingCourierParcel);

        game.DepositCleanCash(long.MaxValue);
        game.DeliverCourierParcel(1);
        Eq(1L, game.CleanCash);
        Eq(long.MaxValue, game.BankBalance);
        True(!game.CarryingCourierParcel);
    }

    private static void CourierCancellationNeverCreditsCash()
    {
        var session = new HeistSession();
        Throws<InvalidOperationException>(() => session.CancelCourierParcel());
        session.PickUpCourierParcel();

        // Cargo survives a checkpoint; the return must not pay a reward.
        var resumed = HeistSession.FromSnapshot(session.ExportSnapshot());
        True(resumed.CarryingCourierParcel);
        resumed.CancelCourierParcel();
        True(!resumed.CarryingCourierParcel);
        Eq(0L, resumed.CleanCash);
        Eq(0L, resumed.BankBalance);
        Eq(0L, resumed.DirtyCash);
        Eq(0L, resumed.CounterCash);
        Throws<InvalidOperationException>(() => resumed.CancelCourierParcel());
        Throws<InvalidOperationException>(() => resumed.DeliverCourierParcel(20));

        // Returning the parcel unlocks the criminal path without a payout.
        resumed.Scout();
        resumed.PutOnMask();
        resumed.StartHeist();
        Eq(HeistPhase.Robbing, resumed.Phase);
        Eq(PlayerRole.Criminal, resumed.CurrentRole);
        True(!HeistSession.FromSnapshot(resumed.ExportSnapshot()).CarryingCourierParcel);

        var courier = new HeistSession();
        courier.PickUpCourierParcel();
        courier.CancelCourierParcel();
        courier.PickUpCourierParcel();
        courier.DeliverCourierParcel(20);
        Eq(20L, courier.CleanCash); // Only the completed second job pays.
        Throws<InvalidOperationException>(() => courier.CancelCourierParcel());
    }

    private static void ArrestConfiscatesLootAndPreservesLegalMoney()
    {
        var game = new HeistSession();
        Throws<InvalidOperationException>(() => game.ArrestAfterAlarm());
        Throws<InvalidOperationException>(() => game.ReleaseFromCustody());

        game.OpenBankAccount();
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(90); // Independent fixture, not original game balance.
        game.DepositCleanCash(40);
        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.TakeLoot("artwork");

        // Seeing a player raises an alarm, but cannot arrest until then.
        Throws<InvalidOperationException>(() => game.ArrestAfterAlarm());
        game.RaiseAlarm();
        game.ArrestAfterAlarm();

        Eq(HeistPhase.Arrested, game.Phase);
        Eq(PlayerRole.Criminal, game.CurrentRole);
        Eq(0, game.Loot.Count);
        Eq(0L, game.CounterCash);
        Eq(0L, game.DirtyCash);
        Eq(50L, game.CleanCash);
        Eq(40L, game.BankBalance);
        True(game.AlarmRaised);
        Throws<InvalidOperationException>(() => game.ArrestAfterAlarm());
        Throws<InvalidOperationException>(() => game.LeaveCity());
        Throws<InvalidOperationException>(() => game.Escape());
        Throws<InvalidOperationException>(() => game.Scout());

        // Save/reload during custody never revives confiscated loot.
        var restored = HeistSession.FromSnapshot(game.ExportSnapshot());
        Eq(HeistPhase.Arrested, restored.Phase);
        Eq(0, restored.Loot.Count);
        restored.ReleaseFromCustody();
        Eq(HeistPhase.Idle, restored.Phase);
        Eq(PlayerRole.Civilian, restored.CurrentRole);
        True(!restored.AlarmRaised && !restored.StaffControlled);
        Eq(50L, restored.CleanCash);
        Eq(40L, restored.BankBalance);
        Throws<InvalidOperationException>(() => restored.ReleaseFromCustody());
        restored.Scout();
        restored.PutOnMask();
        restored.StartHeist();
        Eq(HeistPhase.Robbing, restored.Phase);

        // A controlled guard cannot initiate the arrest outcome.
        var guarded = StartHeistWithOneItem();
        guarded.RaiseAlarm();
        guarded.ControlStaff();
        Throws<InvalidOperationException>(() => guarded.ArrestAfterAlarm());
        Eq(HeistPhase.Robbing, guarded.Phase);
        Eq(1, guarded.Loot.Count);
    }

    private static void ArrestSnapshotCannotForgeRolesOrRewards()
    {
        var game = StartHeistWithOneItem();
        game.RaiseAlarm();
        game.ArrestAfterAlarm();

        void Reject(Action<HeistSessionSnapshot> mutate)
        {
            var forged = game.ExportSnapshot();
            mutate(forged);
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(forged));
        }

        Reject(data => data.Zone = Zone.Desert);
        Reject(data => data.Role = PlayerRole.Civilian);
        Reject(data => data.Role = PlayerRole.Police);
        Reject(data => data.AlarmRaised = false);
        Reject(data => data.StaffControlled = true);
        Reject(data => data.LootIds = new[] { "resurrected-loot" });
        Reject(data => data.CounterCash = 1);
        Reject(data => data.DirtyCash = 1);
        Reject(data => data.CarryingCourierParcel = true);

        var valid = HeistSession.FromSnapshot(game.ExportSnapshot());
        valid.ReleaseFromCustody();
        True(!valid.AlarmRaised);
        Throws<InvalidOperationException>(() => valid.ArrestAfterAlarm());
    }

    private static void EmptyHandedWithdrawalRestoresPlayWithoutEarningCash()
    {
        var session = new HeistSession();
        session.OpenBankAccount();
        session.PickUpCourierParcel();
        session.DeliverCourierParcel(60);
        session.DepositCleanCash(20);

        // Deliberately carry legal cash, bank money and previously earned
        // dirty cash into another attempt; withdrawal must not erase them.
        session.Scout();
        session.PutOnMask();
        session.StartHeist();
        session.TakeLoot("camera");
        session.Escape();
        session.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        session.CollectCounterCash();
        session.StartLaundering(40, 35, 100, 1);
        session.CompleteLaundering(101);
        session.LeaveCity();
        session.EnterCity();
        session.BeginAnotherHeist();
        session.Scout();
        session.PutOnMask();
        session.StartHeist();

        Throws<InvalidOperationException>(() => session.SellLoot(
            new Dictionary<string, long>()));
        session.RaiseAlarm();
        session.ControlStaff();
        var saved = HeistSession.FromSnapshot(session.ExportSnapshot());
        Eq(HeistPhase.Robbing, saved.Phase);
        Eq(0, saved.Loot.Count);
        saved.WithdrawEmptyHanded();

        Eq(HeistPhase.Idle, saved.Phase);
        Eq(PlayerRole.Civilian, saved.CurrentRole);
        Eq(Zone.City, saved.CurrentZone);
        Eq(0, saved.Loot.Count);
        Eq(0L, saved.CounterCash);
        Eq(60L, saved.DirtyCash);
        Eq(75L, saved.CleanCash);
        Eq(20L, saved.BankBalance);
        True(saved.BankAccountOpened);
        True(!saved.AlarmRaised && !saved.StaffControlled);
        Throws<InvalidOperationException>(() => saved.WithdrawEmptyHanded());
        Eq(HeistPhase.Idle, HeistSession.FromSnapshot(saved.ExportSnapshot()).Phase);

        // Withdrawal is not a reset of the economy: another robbery is legal.
        saved.Scout();
        saved.PutOnMask();
        saved.StartHeist();
        saved.TakeLoot("painting");
        Throws<InvalidOperationException>(() => saved.WithdrawEmptyHanded());
        Eq(1, saved.Loot.Count);
        Eq(PlayerRole.Criminal, saved.CurrentRole);
        saved.Escape();
        Eq(HeistPhase.Escaped, saved.Phase);
    }

    private static void EmptyEscapeAndForgedCheckpointAreRejected()
    {
        var game = new HeistSession();
        Throws<InvalidOperationException>(() => game.WithdrawEmptyHanded());
        game.Scout();
        Throws<InvalidOperationException>(() => game.WithdrawEmptyHanded());
        game.PutOnMask();
        game.StartHeist();

        Throws<InvalidOperationException>(() => game.Escape());
        Eq(HeistPhase.Robbing, game.Phase);
        Eq(0, game.Loot.Count);

        var forged = game.ExportSnapshot();
        forged.Phase = HeistPhase.Escaped;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(forged));

        var police = new HeistSession(Zone.City, PlayerRole.Police);
        Throws<InvalidOperationException>(() => police.WithdrawEmptyHanded());
        game.WithdrawEmptyHanded();
        Eq(PlayerRole.Civilian, game.CurrentRole);
        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.TakeLoot("art");
        Throws<InvalidOperationException>(() => game.WithdrawEmptyHanded());
        game.Escape();
        Throws<InvalidOperationException>(() => game.WithdrawEmptyHanded());
        Eq(HeistPhase.Escaped, HeistSession.FromSnapshot(game.ExportSnapshot()).Phase);
    }

    private static void ActiveHeistsCannotLeaveCityOrForgeDesertSaves()
    {
        // Local game core must enforce the same city-only heist boundary as
        // Unity's ExitCity pillar. The save loader cannot be a second bypass.
        var game = new HeistSession();
        game.OpenBankAccount();
        game.PickUpCourierParcel();
        game.DeliverCourierParcel(90);
        game.DepositCleanCash(40);
        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.TakeLoot("painting");

        void RejectExitAndForgedDesert()
        {
            HeistSessionSnapshot before = game.ExportSnapshot();
            Throws<InvalidOperationException>(() => game.LeaveCity());
            HeistSessionSnapshot after = game.ExportSnapshot();
            Eq(before.Zone, after.Zone);
            Eq(before.Role, after.Role);
            Eq(before.Phase, after.Phase);
            Eq(before.LootIds.Length, after.LootIds.Length);
            Eq(before.CounterCash, after.CounterCash);
            Eq(before.DirtyCash, after.DirtyCash);
            Eq(before.CleanCash, after.CleanCash);
            Eq(before.BankBalance, after.BankBalance);
            Eq(before.LaunderingReadyAt, after.LaunderingReadyAt);

            var tampered = game.ExportSnapshot();
            tampered.Zone = Zone.Desert;
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(tampered));
        }

        RejectExitAndForgedDesert(); // Robbing, loot in inventory
        game.Escape();
        RejectExitAndForgedDesert(); // Escaped, awaiting sale
        game.SellLoot(new Dictionary<string, long> { ["painting"] = 100 });
        RejectExitAndForgedDesert(); // CashOnCounter, must collect
        game.CollectCounterCash();
        RejectExitAndForgedDesert(); // DirtyCashCollected, must launder
        game.StartLaundering(80, 60, 1000, 10);
        RejectExitAndForgedDesert(); // Laundering, must complete
        game.CompleteLaundering(1010);
        Eq(HeistPhase.Laundered, game.Phase);

        var custody = StartHeistWithOneItem();
        custody.RaiseAlarm();
        custody.ArrestAfterAlarm();
        var originalCustody = custody.ExportSnapshot();
        Throws<InvalidOperationException>(() => custody.LeaveCity());
        Eq(originalCustody.Phase, custody.Phase);
        Eq(Zone.City, custody.CurrentZone);
        var forgedCustody = custody.ExportSnapshot();
        forgedCustody.Zone = Zone.Desert;
        Throws<ArgumentException>(() => HeistSession.FromSnapshot(forgedCustody));
    }

    private static void IdleScoutedAndLaunderedCanTravelWithBalances()
    {
        // Normal, scouted and completed-game travel stays valid in v1 saves.
        var civilian = new HeistSession();
        civilian.OpenBankAccount();
        civilian.PickUpCourierParcel();
        Throws<InvalidOperationException>(() => civilian.LeaveCity());
        civilian.CancelCourierParcel();
        civilian.LeaveCity();
        Eq(HeistPhase.Idle, HeistSession.FromSnapshot(
            civilian.ExportSnapshot()).Phase);
        civilian.EnterCity();
        civilian.Scout();
        civilian.PutOnMask();
        civilian.LeaveCity();
        Eq(Zone.Desert, civilian.CurrentZone);
        Eq(PlayerRole.Civilian, civilian.CurrentRole);
        Eq(HeistPhase.Scouted, HeistSession.FromSnapshot(
            civilian.ExportSnapshot()).Phase);
        civilian.EnterCity();
        civilian.PutOnMask();
        civilian.StartHeist();
        civilian.TakeLoot("painting");
        civilian.Escape();
        civilian.SellLoot(new Dictionary<string, long> { ["painting"] = 100 });
        civilian.CollectCounterCash();
        civilian.StartLaundering(80, 60, 1000, 10);
        civilian.CompleteLaundering(1010);
        civilian.LeaveCity();
        var saved = HeistSession.FromSnapshot(civilian.ExportSnapshot());
        Eq(Zone.Desert, saved.CurrentZone);
        Eq(PlayerRole.Civilian, saved.CurrentRole);
        Eq(HeistPhase.Laundered, saved.Phase);
        Eq(20L, saved.DirtyCash);
        Eq(60L, saved.CleanCash);
        Eq(0L, saved.BankBalance);
        True(saved.BankAccountOpened);
        saved.EnterCity();
        saved.DepositCleanCash(60);
        Eq(60L, saved.BankBalance);
    }

    private static void RejectsUnreachableDesertCriminalRoles()
    {
        // No legitimate constructor or city-exit transition leaves a
        // criminal outside the city. Other roles may still start there.
        Throws<ArgumentException>(() =>
            new HeistSession(Zone.Desert, PlayerRole.Criminal));
        Eq(PlayerRole.Civilian, new HeistSession(Zone.Desert).CurrentRole);
        Eq(PlayerRole.Police,
            new HeistSession(Zone.Desert, PlayerRole.Police).CurrentRole);

        var idle = new HeistSession();
        idle.OpenBankAccount();
        idle.PickUpCourierParcel();
        idle.DeliverCourierParcel(25);
        idle.DepositCleanCash(10);
        idle.LeaveCity();

        var scouted = new HeistSession();
        scouted.Scout();
        scouted.PutOnMask();
        scouted.LeaveCity();

        var finished = StartHeistWithOneItem();
        finished.Escape();
        finished.SellLoot(new Dictionary<string, long> { ["camera"] = 100 });
        finished.CollectCounterCash();
        finished.StartLaundering(100, 80, 1000, 10);
        finished.CompleteLaundering(1010);
        finished.LeaveCity();

        foreach (HeistSession legal in new[] { idle, scouted, finished })
        {
            var original = legal.ExportSnapshot();
            Eq(Zone.Desert, original.Zone);
            Eq(PlayerRole.Civilian, original.Role);
            var restored = HeistSession.FromSnapshot(original);
            Eq(legal.Phase, restored.Phase);
            Eq(legal.CleanCash, restored.CleanCash);
            Eq(legal.BankBalance, restored.BankBalance);

            // Forging the role on an otherwise legitimate v1 checkpoint
            // must not enable a criminal to load into the desert.
            var forged = legal.ExportSnapshot();
            forged.Role = PlayerRole.Criminal;
            Throws<ArgumentException>(() => HeistSession.FromSnapshot(forged));
            Eq(PlayerRole.Civilian, legal.CurrentRole);
            Eq(original.CleanCash, legal.CleanCash);
            Eq(original.BankBalance, legal.BankBalance);
        }

        var police = new HeistSession(Zone.City, PlayerRole.Police);
        police.Scout();
        police.LeaveCity();
        var policeRestored = HeistSession.FromSnapshot(police.ExportSnapshot());
        Eq(Zone.Desert, policeRestored.CurrentZone);
        Eq(PlayerRole.Police, policeRestored.CurrentRole);
        Eq(HeistPhase.Scouted, policeRestored.Phase);
        Eq(15L, idle.CleanCash);
        Eq(10L, idle.BankBalance);
    }

    private static HeistSession StartHeistWithOneItem()
    {
        var game = new HeistSession();
        game.Scout();
        game.PutOnMask();
        game.StartHeist();
        game.TakeLoot("camera");
        return game;
    }

    private static void Eq<T>(T expected, T actual)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new Exception("Expected " + expected + ", got " + actual);
    }

    private static void True(bool condition)
    {
        if (!condition)
            throw new Exception("Expected condition to be true.");
    }

    private static void Throws<T>(Action action) where T : Exception
    {
        try
        {
            action();
        }
        catch (T)
        {
            return;
        }
        throw new Exception("Expected exception: " + typeof(T).Name);
    }
}
