"""Run from repository root: python -m unittest discover -s reconstruction/tests."""

import unittest

from reconstruction.rules import (
    CycleState, Encounter, Loss, Player, Role, WipeConversion, Zone,
    loss_on_encounter,
)


class RoleTransitionTests(unittest.TestCase):
    def test_mask_and_extraction(self):
        player = Player().enter_city()
        self.assertEqual(player.role, Role.CIVILIAN)
        criminal = player.put_on_mask()
        self.assertEqual(criminal.role, Role.CRIMINAL)
        self.assertEqual(criminal.leave_city(), Player())

    def test_mask_requires_city_civilian(self):
        for player in (Player(), Player(Role.POLICE, Zone.CITY),
                       Player(Role.CRIMINAL, Zone.CITY)):
            with self.subTest(player=player), self.assertRaises(ValueError):
                player.put_on_mask()


class LossTests(unittest.TestCase):
    def test_death_matrix(self):
        cases = (
            (Zone.CITY, Role.CIVILIAN, Loss(False, False, False)),
            (Zone.CITY, Role.CRIMINAL, Loss(True, True, False)),
            (Zone.CITY, Role.POLICE, Loss(False, False, True)),
            (Zone.DESERT, Role.CIVILIAN, Loss(True, True, True)),
            (Zone.DESERT, Role.CRIMINAL, Loss(True, True, True)),
            (Zone.DESERT, Role.POLICE, Loss(True, True, True)),
        )
        for zone, role, expected in cases:
            with self.subTest(zone=zone, role=role):
                self.assertEqual(loss_on_encounter(Player(role, zone),
                                                   Encounter.DEATH), expected)

    def test_surrender_and_bribe(self):
        criminal = Player(Role.CRIMINAL, Zone.CITY)
        self.assertEqual(loss_on_encounter(criminal, Encounter.SURRENDER),
                         Loss(True, False, False))
        self.assertEqual(loss_on_encounter(criminal, Encounter.BRIBE_ACCEPTED),
                         Loss(False, False, False))

    def test_invalid_surrender_context(self):
        for player in (Player(), Player(Role.CIVILIAN, Zone.CITY),
                       Player(Role.POLICE, Zone.CITY)):
            with self.subTest(player=player), self.assertRaises(ValueError):
                loss_on_encounter(player, Encounter.SURRENDER)


class WipeTests(unittest.TestCase):
    def test_wipe_preserves_only_verified_persistence(self):
        previous = CycleState(
            player_name="player", cosmetics=("jacket",), tutorial_completed=True,
            settings=(("sensitivity", "2"),), accumulated_jail_time=9,
            authority=17, cash=120, bank_balance=300, weapons=("rifle",),
            plots=("plot-1",), bases=("house",),
        )
        result = previous.federal_raid(WipeConversion(new_jail_time=5, new_authority=2))
        self.assertEqual(result.player_name, "player")
        self.assertEqual(result.cosmetics, ("jacket",))
        self.assertTrue(result.tutorial_completed)
        self.assertEqual(result.settings, (("sensitivity", "2"),))
        self.assertEqual(result.accumulated_jail_time, 14)
        self.assertEqual(result.authority, 2)
        self.assertEqual((result.cash, result.bank_balance), (0, 0))
        self.assertEqual((result.weapons, result.plots, result.bases), ((), (), ()))
        self.assertEqual(previous.cash, 120)  # immutable

    def test_rejects_negative_conversion(self):
        with self.assertRaises(ValueError):
            WipeConversion(new_jail_time=-1, new_authority=2)


if __name__ == "__main__":
    unittest.main()
