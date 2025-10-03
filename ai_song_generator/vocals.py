"""Utilities for vocal integration."""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import List

from .constants import SAMPLE_RATE
from .generator import SongProject


class VocalIntegration:
    """Add synthesized or uploaded vocals to a :class:`SongProject`."""

    def generate_vocals(self, lyrics: str, *, pitch: float = 440.0) -> List[float]:
        words = lyrics.split()
        duration_per_word = max(0.25, 2.5 / max(len(words), 1))
        audio_segments: List[List[float]] = []
        total_samples = int(SAMPLE_RATE * duration_per_word)
        if total_samples <= 0:
            return []
        for index, _ in enumerate(words):
            segment: List[float] = []
            for sample_index in range(total_samples):
                time = sample_index / SAMPLE_RATE
                vibrato = math.sin(math.pi * 4 * time)
                base = math.sin(2 * math.pi * pitch * time)
                envelope = 0.1 + 0.9 * (sample_index / max(total_samples - 1, 1))
                segment.append(float(base * (0.6 + 0.4 * vibrato) * envelope))
            audio_segments.append(segment)
        combined: List[float] = []
        for segment in audio_segments:
            combined.extend(segment)
        return combined

    def load_vocals(self, path: Path) -> List[float]:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            samples = list(frames)
        result: List[float] = []
        for index in range(0, len(samples), 2):
            if index + 1 >= len(samples):
                break
            value = int.from_bytes(bytes(samples[index : index + 2]), byteorder="little", signed=True)
            result.append(value / 32767.0)
        return result

    def blend(self, project: SongProject, vocals: List[float], *, mix: float = 0.5) -> None:
        if not vocals:
            return
        song = project.audio
        if not song:
            project.audio = vocals
            return
        length = max(len(song), len(vocals))
        song_padded = _pad(song, length)
        vocal_padded = _pad(vocals, length)
        blended = []
        for a, b in zip(song_padded, vocal_padded):
            blended.append((1 - mix) * a + mix * b)
        peak = max((abs(value) for value in blended), default=1.0) or 1.0
        project.audio = [value / peak for value in blended]


def _pad(audio: List[float], length: int) -> List[float]:
    if len(audio) >= length:
        return audio[:length]
    return audio + [0.0] * (length - len(audio))
