"""Audio synthesis helpers for constructing layered arrangements."""

from __future__ import annotations

import math
from typing import Iterable, List, Optional

import numpy as np

from .constants import SAMPLE_RATE
from .structures import SectionLayer, SongSection


def oscillator(waveform: str, frequency: float, duration: float, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Generate a basic oscillator waveform."""

    if duration <= 0:
        return np.zeros(0, dtype=np.float32)
    length = max(1, int(sample_rate * duration))
    t = np.linspace(0.0, duration, length, endpoint=False)
    phase = 2 * math.pi * frequency * t
    if waveform == "sine":
        signal = np.sin(phase)
    elif waveform == "square":
        signal = np.sign(np.sin(phase))
    elif waveform == "saw":
        signal = 2.0 * (phase / (2 * math.pi) - np.floor(0.5 + phase / (2 * math.pi)))
    elif waveform == "triangle":
        signal = 2.0 * np.abs(2.0 * (phase / (2 * math.pi) - np.floor(phase / (2 * math.pi) + 0.5))) - 1.0
    else:  # fallback to sine
        signal = np.sin(phase)
    return signal.astype(np.float32)


def render_layer(layer: SectionLayer, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Render a single :class:`SectionLayer` to audio samples."""

    segments: List[np.ndarray] = []
    rng = np.random.default_rng(layer.seed)
    envelope = layer.envelope or {"attack": 0.01, "release": 0.3}
    attack = float(envelope.get("attack", 0.01))
    release = float(envelope.get("release", 0.3))
    for note, duration in zip(layer.notes, layer.durations):
        duration = max(duration, 1.0 / sample_rate)
        if layer.noise:
            length = max(1, int(sample_rate * duration))
            tone = rng.uniform(-1.0, 1.0, length).astype(np.float32)
        elif note is None or note <= 0:
            length = max(1, int(sample_rate * duration))
            tone = np.zeros(length, dtype=np.float32)
        else:
            tone = oscillator(layer.waveform, float(note), duration, sample_rate=sample_rate)
        shaped = apply_envelope(tone, attack=attack, release=release)
        segments.append(shaped * float(layer.volume))
    if not segments:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(segments).astype(np.float32)


def apply_envelope(audio: np.ndarray, *, attack: float, release: float) -> np.ndarray:
    """Shape audio with a linear attack/release envelope."""

    if audio.size == 0:
        return audio
    attack = max(attack, 1.0 / SAMPLE_RATE)
    release = max(release, 1.0 / SAMPLE_RATE)
    length = audio.size
    attack_samples = min(length, int(SAMPLE_RATE * attack))
    release_samples = min(length, int(SAMPLE_RATE * release))
    sustain_samples = max(0, length - attack_samples - release_samples)
    envelope = np.ones(length, dtype=np.float32)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, endpoint=False)
    if release_samples > 0:
        start = length - release_samples
        envelope[start:] = np.linspace(1.0, 0.0, release_samples, endpoint=True)
    if sustain_samples > 0 and attack_samples < length:
        envelope[attack_samples : attack_samples + sustain_samples] = 1.0
    return (audio * envelope).astype(np.float32)


def render_section(section: SongSection, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Render an entire section by summing its layers."""

    if not section.layers:
        if not section.notes:
            return np.zeros(max(1, int(sample_rate * section.duration)), dtype=np.float32)
        return render_fallback(section.notes, section.duration, sample_rate=sample_rate)

    rendered_layers = [render_layer(layer, sample_rate=sample_rate) for layer in section.layers]
    return mix_layers(rendered_layers)


def mix_layers(layers: Iterable[np.ndarray]) -> np.ndarray:
    """Combine audio layers while matching their lengths."""

    rendered = [np.asarray(layer, dtype=np.float32) for layer in layers if layer.size]
    if not rendered:
        return np.zeros(0, dtype=np.float32)
    max_length = max(layer.size for layer in rendered)
    stack = []
    for layer in rendered:
        if layer.size < max_length:
            padded = np.pad(layer, (0, max_length - layer.size))
        else:
            padded = layer
        stack.append(padded)
    mixture = np.sum(stack, axis=0)
    peak = float(np.max(np.abs(mixture))) or 1.0
    return (mixture / peak).astype(np.float32)


def render_fallback(notes: Iterable[float], duration: float, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Legacy rendering used when no layers are present."""

    notes_list = list(notes)
    if not notes_list:
        return np.zeros(max(1, int(sample_rate * duration)), dtype=np.float32)
    note_count = max(len(notes_list), 1)
    samples_per_note = max(1, int(sample_rate * duration / note_count))
    audio = np.zeros(samples_per_note * note_count, dtype=np.float32)
    note_duration = duration / note_count
    for idx, freq in enumerate(notes_list):
        start = idx * samples_per_note
        t = np.linspace(0, note_duration, samples_per_note, endpoint=False)
        waveform = np.sin(2 * math.pi * freq * t)
        envelope = np.linspace(1.0, 0.05, samples_per_note)
        audio[start : start + samples_per_note] = waveform * envelope * 0.5
    peak = float(np.max(np.abs(audio))) or 1.0
    return (audio / peak).astype(np.float32)
