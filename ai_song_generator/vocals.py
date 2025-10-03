"""Utilities for vocal integration."""

from __future__ import annotations

import wave
from pathlib import Path
import numpy as np

from .generator import SAMPLE_RATE, SongProject


class VocalIntegration:
    """Add synthesized or uploaded vocals to a :class:`SongProject`."""

    def generate_vocals(self, lyrics: str, *, pitch: float = 440.0) -> np.ndarray:
        words = lyrics.split()
        duration_per_word = max(0.25, 2.5 / max(len(words), 1))
        audio_segments = []
        for index, _ in enumerate(words):
            vibrato = np.sin(np.linspace(0, np.pi * 4, int(SAMPLE_RATE * duration_per_word)))
            base = np.sin(np.linspace(0, pitch * duration_per_word * np.pi * 2, int(SAMPLE_RATE * duration_per_word)))
            envelope = np.linspace(0.1, 1.0, int(SAMPLE_RATE * duration_per_word))
            segment = base * (0.6 + 0.4 * vibrato) * envelope
            audio_segments.append(segment.astype(np.float32))
        if not audio_segments:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(audio_segments)

    def load_vocals(self, path: Path) -> np.ndarray:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767
        return data

    def blend(self, project: SongProject, vocals: np.ndarray, *, mix: float = 0.5) -> None:
        if vocals.size == 0:
            return
        song = project.audio
        if song.size == 0:
            project.audio = vocals
            return
        length = max(len(song), len(vocals))
        song = _pad(song, length)
        vocals = _pad(vocals, length)
        project.audio = ((1 - mix) * song + mix * vocals).astype(np.float32)


def _pad(audio: np.ndarray, length: int) -> np.ndarray:
    if len(audio) >= length:
        return audio[:length]
    return np.pad(audio, (0, length - len(audio)))
