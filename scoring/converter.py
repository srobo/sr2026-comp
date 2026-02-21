"""
Converter to assist the SRComp Scorer UI reading & writing score files.

This should be updated in tandem with `update.html` which is used to render the
scores and define the form inputs.

Required as part of a compstate, though the default implementation may suffice
for simple cases.
"""

from __future__ import annotations

from sr.comp.match_period import Match
from sr.comp.scorer.converter import (
    Converter as BaseConverter,
    InputForm,
    OutputForm,
    parse_int,
    render_int,
    Zone,
    ZoneId,
)
from sr.comp.types import ScoreArenaZonesData, ScoreData, ScoreTeamData, TLA

from sr2026 import RawZone


class SR2026ScoreTeamData(ScoreTeamData):
    left_starting_zone: bool


class Converter(BaseConverter):
    """
    Base class for converting between representations of a match's score.
    """

    def form_team_to_score(self, form: InputForm, zone_id: ZoneId) -> SR2026ScoreTeamData:
        """
        Prepare a team's scoring data for saving in a score dict.

        This is also given a `ZoneId` since form data are all keyed by zone.
        """
        return {
            **super().form_team_to_score(form, zone_id),
            'left_starting_zone':
                form.get(f'left_starting_zone_{zone_id}', None) is not None,
        }

    def form_zone_to_score(  # type: ignore[override]
        self,
        form: InputForm,
        zone: Zone,
    ) -> RawZone:
        """
        Prepare a zone's scoring data for saving in a score dict.
        """
        return RawZone({
            'red': parse_int(form.get(f'zone_{zone}_red', '')),
            'blue': parse_int(form.get(f'zone_{zone}_blue', '')),
        })

    def form_to_score(self, match: Match, form: InputForm) -> ScoreData:
        """
        Prepare a score dict for the given match and form dict.

        This is a copy of the base method, minus the inclusion of the 'other'
        zone.
        """
        zone_ids = range(len(match.teams))

        teams = {}
        for zone_id in zone_ids:
            tla = form.get(f'tla_{zone_id}', None)
            if tla:
                teams[TLA(tla)] = self.form_team_to_score(form, zone_id)

        zones = list(zone_ids)
        arena = ScoreArenaZonesData({
            zone: self.form_zone_to_score(form, zone)
            for zone in zones
        })

        return ScoreData({
            'arena_id': match.arena,
            'match_number': match.num,
            'teams': teams,
            'arena_zones': arena,
        })

    def score_team_to_form(self, tla: TLA, info: ScoreTeamData) -> OutputForm:
        zone_id = info['zone']
        return OutputForm({
            **super().score_team_to_form(tla, info),
            f'left_starting_zone_{zone_id}': info.get('left_starting_zone', False),
        })

    def score_zone_to_form(
        self,
        zone_id: Zone,
        zone_info: RawZone,  # type: ignore[override]
    ) -> OutputForm:
        return OutputForm({
            f'zone_{zone_id}_red': render_int(zone_info['red']),
            f'zone_{zone_id}_blue': render_int(zone_info['blue']),
        })

    def match_to_form(self, match: Match) -> OutputForm:
        """
        Prepare a fresh form dict for the given match.

        This method is used when there is no existing score for a match.
        """

        form = OutputForm({})

        for zone_id, tla in enumerate(match.teams):
            if tla:
                form[f'tla_{zone_id}'] = tla
                form[f'disqualified_{zone_id}'] = False
                form[f'present_{zone_id}'] = False
                form[f'left_starting_zone_{zone_id}'] = False

            form[f'zone_{zone_id}_red'] = None
            form[f'zone_{zone_id}_blue'] = None

        return form
