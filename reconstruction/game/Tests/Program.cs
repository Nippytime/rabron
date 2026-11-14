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
