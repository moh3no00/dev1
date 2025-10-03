"""Tools for customizing generated songs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .generator import SongProject


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
        rendered = [_render_section(section) for section in project.sections]
        if rendered:
            combined = np.concatenate(rendered)
            peak = float(np.max(np.abs(combined))) or 1.0
            project.audio = (combined / peak).astype(np.float32)
        else:
            project.audio = np.zeros(0, dtype=np.float32)
        return EditSummary(structure_modified=True)


def _time_stretch(audio: np.ndarray, ratio: float) -> np.ndarray:
    if ratio <= 0:
        raise ValueError("Stretch ratio must be positive")
    if ratio == 1.0 or audio.size == 0:
        return audio
    indices = np.arange(0, len(audio), ratio)
    indices = indices[indices < len(audio)]
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)


def _apply_equalizer(audio: np.ndarray, profile: Iterable[float]) -> np.ndarray:
    if audio.size == 0:
        return audio
    profile = list(profile)
    if not profile:
        raise ValueError("Profile must contain at least one value")
    spectrum = np.fft.rfft(audio)
    bins = len(spectrum)
    eq = np.interp(np.linspace(0, len(profile) - 1, bins), np.arange(len(profile)), profile)
    adjusted = np.fft.irfft(spectrum * eq)
    return np.real(adjusted).astype(np.float32)


def _render_section(section) -> np.ndarray:
    from .generator import _render_waveform

    return _render_waveform(section.notes, section.duration)
