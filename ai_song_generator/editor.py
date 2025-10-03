"""Tools for customizing generated songs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .generator import SongProject
from .synthesis import render_section


@dataclass
class EditSummary:
    tempo_change: float = 1.0
    instruments_changed: bool = False
    structure_modified: bool = False


class SongEditor:
    """High-level editing utilities that operate on :class:`SongProject`."""

    def adjust_tempo(self, project: SongProject, tempo: int) -> EditSummary:
        if tempo <= 0:
            raise ValueError("Tempo must be positive")
        ratio = tempo / max(project.tempo, 1)
        project.audio = _time_stretch(project.audio, ratio)
        project.tempo = tempo
        return EditSummary(tempo_change=ratio)

    def apply_instrument_profile(self, project: SongProject, profile: Iterable[float]) -> EditSummary:
        project.audio = _apply_equalizer(project.audio, profile)
        return EditSummary(instruments_changed=True)

    def rearrange_sections(self, project: SongProject, order: Iterable[int]) -> EditSummary:
        order = list(order)
        if sorted(order) != list(range(len(project.sections))):
            raise ValueError("Order must reference each section exactly once")
        project.sections = [project.sections[i] for i in order]
        rendered = [render_section(section) for section in project.sections]
        if rendered:
            combined: List[float] = []
            for audio in rendered:
                combined.extend(audio)
            peak = max((abs(value) for value in combined), default=1.0) or 1.0
            project.audio = [value / peak for value in combined]
        else:
            project.audio = []
        return EditSummary(structure_modified=True)


def _time_stretch(audio: List[float], ratio: float) -> List[float]:
    if ratio <= 0:
        raise ValueError("Stretch ratio must be positive")
    if ratio == 1.0 or not audio:
        return list(audio)
    original_length = len(audio)
    new_length = max(1, int(round(original_length / ratio)))
    result: List[float] = []
    for index in range(new_length):
        position = index * ratio
        lower = int(position)
        upper = min(lower + 1, original_length - 1)
        fraction = position - lower
        interpolated = (1 - fraction) * audio[lower] + fraction * audio[upper]
        result.append(float(interpolated))
    return result


def _apply_equalizer(audio: List[float], profile: Iterable[float]) -> List[float]:
    if not audio:
        return list(audio)
    profile_list = [float(value) for value in profile]
    if not profile_list:
        raise ValueError("Profile must contain at least one value")
    segments = len(profile_list)
    length = len(audio)
    result: List[float] = []
    for index, sample in enumerate(audio):
        if length == 1:
            weight_position = 0.0
        else:
            weight_position = (index / (length - 1)) * (segments - 1)
        lower = int(weight_position)
        upper = min(lower + 1, segments - 1)
        fraction = weight_position - lower
        lower_gain = profile_list[lower]
        upper_gain = profile_list[upper]
        gain = (1 - fraction) * lower_gain + fraction * upper_gain
        result.append(float(sample) * gain)
    peak = max((abs(value) for value in result), default=1.0) or 1.0
    return [value / peak for value in result]
