"""Core AI song generation utilities.

This module simulates AI-driven music creation by procedurally generating
waveform data. While it is not intended to rival a professional digital audio
workstation, it offers a fully offline, dependency-light experience that makes
it easy to prototype ideas. The generator combines genre templates with user
preferences to craft short tracks that can later be edited, rearranged, or
augmented with vocals.
"""

from __future__ import annotations

import random
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

from .constants import SAMPLE_RATE
from .structures import SectionLayer, SongSection
from .synthesis import render_section
from .templates import GENRE_TEMPLATES


def _normalize(audio: np.ndarray) -> np.ndarray:
    max_val = np.max(np.abs(audio)) or 1.0
    return audio / max_val


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

        sections = self._build_sections(template, duration, tempo, rng)
        audio = self._stitch_sections(sections)

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

    def _build_sections(self, template: Dict, duration: float, tempo: int, rng: random.Random) -> List[SongSection]:
        sections: List[SongSection] = []
        remaining = duration
        available_sections = template.get("sections", ["intro", "verse", "chorus", "bridge"])
        scale = template.get("scale", [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88])
        instrument_presets = template.get("instruments", [])
        while remaining > 0:
            name = rng.choice(available_sections)
            section_duration = min(max(4.0, rng.uniform(6.0, 12.0)), remaining)
            remaining -= section_duration
            notes = [rng.choice(scale) * rng.uniform(0.5, 1.5) for _ in range(rng.randint(4, 8))]
            layers = self._build_layers(
                name,
                instrument_presets or _default_instruments(scale),
                section_duration,
                tempo,
                scale,
                rng,
            )
            lead_layer = layers[0] if layers else None
            lead_notes: List[float] = [float(note) for note in (lead_layer.notes if lead_layer else notes)]
            sections.append(SongSection(name=name, notes=lead_notes, duration=section_duration, layers=layers))
        return sections

    def _build_layers(
        self,
        section_name: str,
        presets: Iterable[Dict],
        section_duration: float,
        tempo: int,
        scale: List[float],
        rng: random.Random,
    ) -> List[SectionLayer]:
        beat_duration = 60.0 / max(tempo, 1)
        layers: List[SectionLayer] = []
        for preset in presets:
            pattern = list(preset.get("pattern", []))
            rhythm = list(preset.get("rhythm", []))
            if not pattern or not rhythm:
                continue
            layer_notes: List[Optional[float]] = []
            layer_durations: List[float] = []
            elapsed = 0.0
            step = 0
            while elapsed + 1e-6 < section_duration:
                note_index = pattern[step % len(pattern)]
                beat_length = float(rhythm[step % len(rhythm)])
                note_duration = max(beat_duration * beat_length, beat_duration * 0.25)
                if elapsed + note_duration > section_duration:
                    note_duration = section_duration - elapsed
                note_value: Optional[float]
                if note_index is None:
                    note_value = None
                else:
                    scale_index = int(note_index) % len(scale)
                    octave_shift = preset.get("octave", 0)
                    note_value = scale[scale_index] * (2 ** octave_shift)
                layer_notes.append(note_value)
                layer_durations.append(float(max(note_duration, 1.0 / SAMPLE_RATE)))
                elapsed += note_duration
                step += 1
            if not layer_notes:
                continue
            layer = SectionLayer(
                name=f"{section_name}-{preset.get('name', 'layer')}",
                notes=layer_notes,
                durations=layer_durations,
                waveform=preset.get("waveform", "sine"),
                volume=float(preset.get("volume", 0.5)),
                envelope=dict(preset.get("envelope", {"attack": 0.01, "release": 0.3})),
                seed=rng.randint(0, 2**32 - 1),
                noise=bool(preset.get("waveform") == "noise"),
            )
            layers.append(layer)
        return layers

    def _stitch_sections(self, sections: List[SongSection]) -> np.ndarray:
        audio_pieces = []
        for section in sections:
            piece = render_section(section)
            if piece.size:
                audio_pieces.append(piece)
        if not audio_pieces:
            return np.zeros(0, dtype=np.float32)
        combined = np.concatenate(audio_pieces)
        return _normalize(combined)


def _write_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        pcm = np.int16(audio * 32767)
        wav_file.writeframes(pcm.tobytes())


def _default_instruments(scale: Iterable[float]) -> List[Dict]:
    del scale  # Scale is unused but kept for API symmetry.
    return [
        {
            "name": "lead",
            "waveform": "saw",
            "pattern": [0, 2, 4, 5],
            "rhythm": [1, 1, 1, 1],
            "volume": 0.5,
            "envelope": {"attack": 0.02, "release": 0.4},
        },
        {
            "name": "bass",
            "waveform": "square",
            "pattern": [0, 0, 3, 4],
            "rhythm": [2, 2, 2, 2],
            "volume": 0.35,
            "octave": -1,
            "envelope": {"attack": 0.01, "release": 0.2},
        },
        {
            "name": "drums",
            "waveform": "noise",
            "pattern": [None, None, None, None],
            "rhythm": [0.5, 0.5, 0.5, 0.5],
            "volume": 0.25,
            "envelope": {"attack": 0.005, "release": 0.1},
        },
    ]
