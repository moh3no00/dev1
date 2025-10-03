"""Core dataclasses shared across generator components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SectionLayer:
    """Individual instrument layer rendered inside a song section."""

    name: str
    notes: List[Optional[float]]
    durations: List[float]
    waveform: str = "sine"
    volume: float = 0.5
    envelope: Dict[str, float] = field(default_factory=lambda: {"attack": 0.01, "release": 0.3})
    seed: Optional[int] = None
    noise: bool = False

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "notes": [None if note is None else float(note) for note in self.notes],
            "durations": [float(value) for value in self.durations],
            "waveform": self.waveform,
            "volume": float(self.volume),
            "envelope": dict(self.envelope),
            "seed": self.seed,
            "noise": self.noise,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "SectionLayer":
        return cls(
            name=payload["name"],
            notes=[None if note is None else float(note) for note in payload.get("notes", [])],
            durations=[float(value) for value in payload.get("durations", [])],
            waveform=payload.get("waveform", "sine"),
            volume=float(payload.get("volume", 0.5)),
            envelope=dict(payload.get("envelope", {"attack": 0.01, "release": 0.3})),
            seed=payload.get("seed"),
            noise=bool(payload.get("noise", False)),
        )


@dataclass
class SongSection:
    """Simple representation of a song section."""

    name: str
    notes: List[float]
    duration: float
    layers: List[SectionLayer] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "notes": [float(note) for note in self.notes],
            "duration": float(self.duration),
            "layers": [layer.to_dict() for layer in self.layers],
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "SongSection":
        from_dict_layers = [SectionLayer.from_dict(item) for item in payload.get("layers", [])]
        return cls(
            name=payload["name"],
            notes=[float(note) for note in payload.get("notes", [])],
            duration=float(payload["duration"]),
            layers=from_dict_layers,
        )


__all__ = ["SectionLayer", "SongSection"]
