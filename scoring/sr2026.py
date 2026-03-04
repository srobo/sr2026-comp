from typing import TypedDict

from sr.comp.types import ScoreTeamData


class RawZone(TypedDict):
    red: int
    blue: int


class SR2026ScoreTeamData(ScoreTeamData):
    left_starting_zone: bool
