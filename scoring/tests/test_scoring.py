#!/usr/bin/env python3

"""
Tests for the scoring logic.

Not really part of a compstate, though the SRComp validation GitHub Action will
auto detect this and run the tests.
"""

import pathlib
import random
import sys
import unittest

import yaml

# Path hackery
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from score import (  # type: ignore[import-not-found]  # noqa: E402
    InvalidScoresheetException,
    Scorer,
)
from sr2026 import RawZone  # type: ignore[import-not-found]  # noqa: E402


def shuffled(text: str) -> str:
    values = list(text)
    random.shuffle(values)
    return ''.join(values)


class ScorerTests(unittest.TestCase):
    longMessage = True

    def construct_scorer(self, zones):
        return Scorer(self.teams_data, zones)

    def assertScores(self, expected_scores, zones):
        scorer = self.construct_scorer(zones)
        scorer.validate(None)
        actual_scores = scorer.calculate_scores()

        self.assertEqual(expected_scores, actual_scores, "Wrong scores")

    def assertInvalidScoresheet(self, zones, *, code):
        scorer = self.construct_scorer(zones)

        with self.assertRaises(InvalidScoresheetException) as cm:
            scorer.validate(None)

        self.assertEqual(
            code,
            cm.exception.code,
            f"Wrong error code, message was: {cm.exception}",
        )

    def setUp(self) -> None:
        self.teams_data = {
            'GGG': {'zone': 0, 'present': True, 'left_starting_zone': False},
            'OOO': {'zone': 1, 'present': True, 'left_starting_zone': False},
        }
        self.zones: dict[int, RawZone] = {
            zone_id: RawZone({
                'red': 0,
                'blue': 0,
            })
            for zone_id in range(4)
        }

    def test_template(self):
        template_path = ROOT / 'template.yaml'
        with template_path.open() as f:
            data = yaml.safe_load(f)

        teams_data = data['teams']
        arena_data = data.get('arena_zones')
        extra_data = data.get('other')

        scorer = Scorer(teams_data, arena_data)
        scores = scorer.calculate_scores()

        scorer.validate(extra_data)

        self.assertEqual(
            teams_data.keys(),
            scores.keys(),
            "Should return score values for every team",
        )

    # Scoring logic

    def test_left_starting_zone(self) -> None:
        self.teams_data['GGG']['left_starting_zone'] = True
        self.assertScores(
            {
                'GGG': 1,
                'OOO': 0,
            },
            self.zones,
        )

    def test_single_token(self) -> None:
        self.zones[0]['blue'] = 1
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 0,
            },
            self.zones,
        )

    def test_two_similar_tokens(self) -> None:
        self.zones[0]['blue'] = 2
        self.assertScores(
            {
                'GGG': 3,
                'OOO': 0,
            },
            self.zones,
        )

    def test_two_different_tokens(self) -> None:
        self.zones[0]['red'] = 1
        self.zones[0]['blue'] = 1
        self.assertScores(
            {
                'GGG': 1,
                'OOO': 0,
            },
            self.zones,
        )

    def test_mixed_tokens(self) -> None:
        self.zones[0]['red'] = 3
        self.zones[0]['blue'] = 1
        self.assertScores(
            {
                'GGG':  3,
                'OOO': 0,
            },
            self.zones,
        )

    # Impossible scenarios

    def test_too_many_tokens_simple(self) -> None:
        self.zones[0]['red'] = 100
        self.assertInvalidScoresheet(
            self.zones,
            code='too_many_tokens',
        )

    def test_too_many_tokens_spread(self) -> None:
        self.zones[0]['red'] = 7
        self.zones[1]['red'] = 7
        self.assertInvalidScoresheet(
            self.zones,
            code='too_many_tokens',
        )


if __name__ == '__main__':
    unittest.main()
