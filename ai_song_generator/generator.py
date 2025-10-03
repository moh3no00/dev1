"""Core AI song generation utilities.

This module simulates AI-driven music creation by procedurally generating
waveform data. While it is not intended to rival a professional digital audio
workstation, it offers a fully offline, dependency-light experience that makes
it easy to prototype ideas. The generator combines genre templates with user
preferences to craft short tracks that can later be edited, rearranged, or
augmented with vocals.
"""

from __future__ import annotations

import math
import random
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

from .templates import GENRE_TEMPLATES

SAMPLE_RATE = 44_100


def _normalize(audio: np.ndarray) -> np.ndarray:
    max_val = np.max(np.abs(audio)) or 1.0
    return audio / max_val


def _render_waveform(notes: Iterable[float], duration: float, volume: float = 0.5) -> np.ndarray:
    notes_list = list(notes)
    if not notes_list:
        length = max(1, int(SAMPLE_RATE * duration))
        return np.zeros(length, dtype=np.float32)
    note_count = max(len(notes_list), 1)
    samples_per_note = max(1, int(SAMPLE_RATE * duration / note_count))
    audio = np.zeros(samples_per_note * note_count, dtype=np.float32)
    note_duration = duration / note_count
    for idx, freq in enumerate(notes_list):
        start = idx * samples_per_note
        t = np.linspace(0, note_duration, samples_per_note, endpoint=False)
        waveform = np.sin(2 * math.pi * freq * t)
        envelope = np.linspace(1.0, 0.05, samples_per_note)
        audio[start : start + samples_per_note] = waveform * envelope * volume
    return audio


@dataclass
class SongSection:
    """Simple representation of a song section."""

    name: str
    notes: List[float]
    duration: float


@dataclass
class SongProject:
    """In-memory representation of a generated song."""

    title: str
    genre: str
    mood: str
    tempo: int
    sections: List[SongSection] = field(default_factory=list)
    audio: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))

    def export(self, path: Path, format: str = "wav") -> Path:
        """Export the song to ``path`` in the requested format."""
        format = format.lower()
        path = Path(path)
        if format not in {"wav", "mp3"}:
            raise ValueError("Only wav and mp3 exports are supported")
        if format == "wav":
            _write_wav(path.with_suffix(".wav"), self.audio)
            return path.with_suffix(".wav")
        try:
            from pydub import AudioSegment

            tmp_path = path.with_suffix(".wav")
            _write_wav(tmp_path, self.audio)
            song = AudioSegment.from_wav(tmp_path)
            export_path = path.with_suffix(".mp3")
            song.export(export_path, format="mp3")
            tmp_path.unlink(missing_ok=True)
            return export_path
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("MP3 export requires pydub and ffmpeg") from exc


class AISongGenerator:
    """Generate songs given simple textual prompts or presets."""

    def __init__(self, templates: Optional[Dict[str, Dict]] = None) -> None:
        self.templates = templates or GENRE_TEMPLATES

    def generate(
        self,
        *,
        style: Optional[str] = None,
        description: Optional[str] = None,
        duration: float = 30.0,
        tempo: Optional[int] = None,
        mood: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> SongProject:
        """Create a new :class:`SongProject`.

        ``style`` should reference a known template. ``description`` is used as a
        fallback when selecting a template by keyword matching. The resulting
        audio is a lightweight procedural composition that captures the desired
        mood via tempo, scale, and instrumentation hints from the template.
        """

        rng = random.Random(seed)
        template = self._resolve_template(style, description)
        tempo = tempo or template["tempo"]
        mood = mood or template["mood"]
        title = self._derive_title(template, mood, rng)

        sections = self._build_sections(template, duration, rng)
        audio = self._stitch_sections(sections, tempo)

        return SongProject(title=title, genre=template["genre"], mood=mood, tempo=tempo, sections=sections, audio=audio)

    # ------------------------------------------------------------------
    # Private helpers

    def _resolve_template(self, style: Optional[str], description: Optional[str]) -> Dict:
        if style and style in self.templates:
            return self.templates[style]
        if description:
            lowered = description.lower()
            for key, template in self.templates.items():
                keywords = template.get("keywords", [])
                if any(word in lowered for word in keywords):
                    return template
        # default fallback
        return next(iter(self.templates.values()))

    def _derive_title(self, template: Dict, mood: str, rng: random.Random) -> str:
        adjectives = ["Crimson", "Electric", "Crystal", "Midnight", "Golden", "Velvet"]
        nouns = ["Echo", "Dream", "Pulse", "Canvas", "Mirage", "Cascade"]
        adjective = rng.choice(adjectives)
        noun = rng.choice(nouns)
        return f"{adjective} {noun} ({template['genre']} - {mood})"

    def _build_sections(self, template: Dict, duration: float, rng: random.Random) -> List[SongSection]:
        sections: List[SongSection] = []
        remaining = duration
        available_sections = template.get("sections", ["intro", "verse", "chorus", "bridge"])
        scale = template.get("scale", [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88])
        while remaining > 0:
            name = rng.choice(available_sections)
            section_duration = min(max(4.0, rng.uniform(6.0, 12.0)), remaining)
            remaining -= section_duration
            notes = [rng.choice(scale) * rng.uniform(0.5, 1.5) for _ in range(rng.randint(4, 8))]
            sections.append(SongSection(name=name, notes=notes, duration=section_duration))
        return sections

    def _stitch_sections(self, sections: List[SongSection], tempo: int) -> np.ndarray:
        tempo_factor = tempo / 120
        audio_pieces = []
        for section in sections:
            base_duration = section.duration / tempo_factor
            piece = _render_waveform(section.notes, base_duration)
            audio_pieces.append(piece)
        if audio_pieces:
            combined = np.concatenate(audio_pieces)
            return _normalize(combined)
        return np.zeros(0, dtype=np.float32)


def _write_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        pcm = np.int16(audio * 32767)
        wav_file.writeframes(pcm.tobytes())
