"""
Scoring calculator used to assign points.

Required as part of a compstate.
"""

from __future__ import annotations

import collections
import typing
from collections.abc import Mapping

if typing.TYPE_CHECKING:
    from sr2026 import RawZone, SR2026ScoreTeamData


class InvalidScoresheetException(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class Scorer:
    def __init__(
        self,
        teams_data: Mapping[str, SR2026ScoreTeamData],
        arena_data: Mapping[int, RawZone],
    ) -> None:
        self._teams_data = teams_data
        self._arena_data = arena_data

    def calculate_scores(self) -> Mapping[str, int]:
        scores = {}

        for tla, info in self._teams_data.items():
            zone_info: RawZone = self._arena_data[info['zone']]

            pH_change = abs(zone_info['blue'] - zone_info['red'])

            # Robots earn one point for each pH level away from neutral (7) that
            # their laboratory is.
            score = pH_change

            # Robots earn a bonus point for having any sample at all in their
            # laboratory.
            if (zone_info['blue'] + zone_info['red']) > 0:
                score += 1

            # Robots earn a bonus point for at any point moving entirely out of
            # their laboratory.
            if info['left_starting_zone']:
                score += 1

            scores[tla] = score

        return scores

    def validate(self, other_data):
        totals = collections.Counter()

        samples = {
            f'zone-{zone_id}-{colour}': info[colour]
            for zone_id, info in self._arena_data.items()
            for colour in ('red', 'blue')
        }
        negative_samples = {x: y for x, y in samples.items() if y < 0}
        if negative_samples:
            raise InvalidScoresheetException(
                "Cannot record negative numbers of samples (in a laboratory), "
                f"got {negative_samples!r}.",
                code='negative_sample_input',
            )

        for zone_info in self._arena_data.values():
            totals.update(zone_info)

        for colour, count in totals.items():
            if count > 8:
                raise InvalidScoresheetException(
                    f"Too many {colour} tokens observed",
                    code='too_many_tokens',
                )


if __name__ == '__main__':
    import libproton
    libproton.main(Scorer)
