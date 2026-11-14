"""Evidence-backed ROB RUN behavioral rules.

This is a small executable specification, NOT a recovered Unity implementation.
Sources: Kefir help articles linked in reconstruction/docs/evidence.md.
All unpublished payout, time, damage, and tax coefficients are deliberately absent.
"""

from dataclasses import dataclass, replace
from enum import Enum


class Role(str, Enum):
    CIVILIAN = "civilian"
    CRIMINAL = "criminal"
    POLICE = "police"


class Zone(str, Enum):
    CITY = "city"
    DESERT = "desert"


class Encounter(str, Enum):
    DEATH = "death"
    SURRENDER = "surrender"
    BRIBE_ACCEPTED = "bribe_accepted"


@dataclass(frozen=True)
class Loss:
    bag: bool
    equipped: bool
    department_issued: bool


@dataclass(frozen=True)
class Player:
    role: Role = Role.CIVILIAN
    zone: Zone = Zone.DESERT

    def enter_city(self) -> "Player":
        return replace(self, zone=Zone.CITY)

    def put_on_mask(self) -> "Player":
        if self.zone != Zone.CITY or self.role != Role.CIVILIAN:
            raise ValueError("Only a civilian in Looty Bay can enter criminal mode")
        return replace(self, role=Role.CRIMINAL)

    def leave_city(self) -> "Player":
        # Official rule: criminal status clears only when leaving the city.
        role = Role.CIVILIAN if self.role == Role.CRIMINAL else self.role
        return replace(self, role=role, zone=Zone.DESERT)


def loss_on_encounter(player: Player, event: Encounter) -> Loss:
    """Return what gets confiscated or lost; no inventory mutations.

    Death:
      - city civilian keeps bag + equipped gear
      - city police loses department-issued gear only
      - city criminal loses bag + equipment
      - desert death loses all carried loot (exact category exceptions TBD)
    Surrender/bribe are specified only for a criminal in the city.
    """
    if event in (Encounter.SURRENDER, Encounter.BRIBE_ACCEPTED):
        if player.zone != Zone.CITY or player.role != Role.CRIMINAL:
            raise ValueError("Surrender/bribe rule only verified for city criminals")
        return Loss(bag=event == Encounter.SURRENDER,
                    equipped=False, department_issued=False)
    if event != Encounter.DEATH:
        raise ValueError(f"Unsupported event: {event}")
    if player.zone == Zone.DESERT:
        return Loss(bag=True, equipped=True, department_issued=True)
    if player.role == Role.CIVILIAN:
        return Loss(bag=False, equipped=False, department_issued=False)
    if player.role == Role.POLICE:
        return Loss(bag=False, equipped=False, department_issued=True)
    return Loss(bag=True, equipped=True, department_issued=False)


@dataclass(frozen=True)
class WipeConversion:
    """Values must come from later verified balancing data, never guessed."""
    new_jail_time: int
    new_authority: int

    def __post_init__(self) -> None:
        if self.new_jail_time < 0 or self.new_authority < 0:
            raise ValueError("Conversion rewards cannot be negative")


@dataclass(frozen=True)
class CycleState:
    player_name: str
    cosmetics: tuple[str, ...] = ()
    tutorial_completed: bool = False
    settings: tuple[tuple[str, str], ...] = ()
    accumulated_jail_time: int = 0
    authority: int = 0
    cash: int = 0
    bank_balance: int = 0
    weapons: tuple[str, ...] = ()
    plots: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()

    def federal_raid(self, conversion: WipeConversion) -> "CycleState":
        """Apply known wipe categories and externally supplied conversion amounts.

        The conversion coefficients and treatment of pre-wipe authority are not
        published. The authority amount passed here is the authoritative post-wipe
        authority, NOT an inferred additive reward.
        """
        return replace(
            self,
            cash=0,
            bank_balance=0,
            weapons=(),
            plots=(),
            bases=(),
            accumulated_jail_time=self.accumulated_jail_time + conversion.new_jail_time,
            authority=conversion.new_authority,
        )
