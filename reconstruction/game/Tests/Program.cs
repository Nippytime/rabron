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
            ControlledStaffPreventsFutureAlarmWithoutRewritingThePast,
            StaffControlMustOccurDuringHeist,
            SnapshotRestoresInFlightLootAndGuardState,
            SnapshotPreservesPhysicalCounterCash,
            SnapshotPreservesLaunderingDeadline,
            SnapshotPreservesBankAcrossHeists,
            SnapshotRejectsInvalidOrTamperedState,
            SnapshotRejectsUnreachablePoliceRobberyPhases,
            ConstructorRejectsUnknownRolesAndZones,
            SnapshotRejectsUnreachablePoliceEconomy,
            LaunderingRejectsUnrestorableTimestamps,
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
        game.BeginAnotherHeist();
        Eq(HeistPhase.Idle, game.Phase);
        Eq(60L, game.CleanCash);
        Eq(0, game.Loot.Count);
        True(!game.AlarmRaised);
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
