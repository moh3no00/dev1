"""Audio synthesis helpers for constructing layered arrangements."""

from __future__ import annotations

import math
import random
from typing import Iterable, List, Optional

from .constants import SAMPLE_RATE
from .structures import SectionLayer, SongSection


def _linspace(start: float, stop: float, num: int, *, endpoint: bool = True) -> List[float]:
    if num <= 0:
        return []
    if num == 1:
        return [float(start)]
    step = (stop - start) / (num - (1 if endpoint else 0))
    values = []
    for index in range(num):
        if endpoint:
            values.append(float(start + step * index))
        else:
            values.append(float(start + step * index))
    if endpoint:
        values[-1] = float(stop)
    return values


def _zeros(length: int) -> List[float]:
    return [0.0 for _ in range(max(length, 0))]


def oscillator(waveform: str, frequency: float, duration: float, *, sample_rate: int = SAMPLE_RATE) -> List[float]:
    """Generate a basic oscillator waveform."""

    if duration <= 0:
        return []
    length = max(1, int(sample_rate * duration))
    t = _linspace(0.0, duration, length, endpoint=False)
    signal: List[float] = []
    for time in t:
        phase = 2 * math.pi * frequency * time
        if waveform == "sine":
            value = math.sin(phase)
        elif waveform == "square":
            value = 1.0 if math.sin(phase) >= 0 else -1.0
        elif waveform == "saw":
            cycles = phase / (2 * math.pi)
            value = 2.0 * (cycles - math.floor(0.5 + cycles))
        elif waveform == "triangle":
            cycles = phase / (2 * math.pi)
            value = 2.0 * abs(2.0 * (cycles - math.floor(cycles + 0.5))) - 1.0
        else:
            value = math.sin(phase)
        signal.append(float(value))
    return signal


def render_layer(layer: SectionLayer, *, sample_rate: int = SAMPLE_RATE) -> List[float]:
    """Render a single :class:`SectionLayer` to audio samples."""

    segments: List[List[float]] = []
    rng = random.Random(layer.seed)
    envelope = layer.envelope or {"attack": 0.01, "release": 0.3}
    attack = float(envelope.get("attack", 0.01))
    release = float(envelope.get("release", 0.3))
    for note, duration in zip(layer.notes, layer.durations):
        duration = max(duration, 1.0 / sample_rate)
        if layer.noise:
            length = max(1, int(sample_rate * duration))
            tone = [rng.uniform(-1.0, 1.0) for _ in range(length)]
        elif note is None or note <= 0:
            length = max(1, int(sample_rate * duration))
            tone = _zeros(length)
        else:
            tone = oscillator(layer.waveform, float(note), duration, sample_rate=sample_rate)
        shaped = apply_envelope(tone, attack=attack, release=release)
        segments.append([sample * float(layer.volume) for sample in shaped])
    if not segments:
        return []
    combined: List[float] = []
    for segment in segments:
        combined.extend(segment)
    return combined


def apply_envelope(audio: List[float], *, attack: float, release: float) -> List[float]:
    """Shape audio with a linear attack/release envelope."""

    if not audio:
        return list(audio)
    attack = max(attack, 1.0 / SAMPLE_RATE)
    release = max(release, 1.0 / SAMPLE_RATE)
    length = len(audio)
    attack_samples = min(length, int(SAMPLE_RATE * attack))
    release_samples = min(length, int(SAMPLE_RATE * release))
    sustain_samples = max(0, length - attack_samples - release_samples)
    envelope = [1.0 for _ in range(length)]
    if attack_samples > 0:
        attack_curve = _linspace(0.0, 1.0, attack_samples, endpoint=False)
        for index in range(attack_samples):
            envelope[index] = attack_curve[index]
    if release_samples > 0:
        start = length - release_samples
        release_curve = _linspace(1.0, 0.0, release_samples, endpoint=True)
        for offset, value in enumerate(release_curve):
            envelope[start + offset] = value
    shaped = []
    for index, sample in enumerate(audio):
        shaped.append(float(sample) * float(envelope[index]))
    return shaped


def render_section(section: SongSection, *, sample_rate: int = SAMPLE_RATE) -> List[float]:
    """Render an entire section by summing its layers."""

    if not section.layers:
        if not section.notes:
            return _zeros(max(1, int(sample_rate * section.duration)))
        return render_fallback(section.notes, section.duration, sample_rate=sample_rate)

    rendered_layers = [render_layer(layer, sample_rate=sample_rate) for layer in section.layers]
    return mix_layers(rendered_layers)


def mix_layers(layers: Iterable[List[float]]) -> List[float]:
    """Combine audio layers while matching their lengths."""

    rendered = [list(layer) for layer in layers if layer]
    if not rendered:
        return []
    max_length = max(len(layer) for layer in rendered)
    stack: List[List[float]] = []
    for layer in rendered:
        if len(layer) < max_length:
            padded = layer + [0.0] * (max_length - len(layer))
        else:
            padded = layer[:max_length]
        stack.append(padded)
    mixture: List[float] = []
    for index in range(max_length):
        total = sum(buffer[index] for buffer in stack)
        mixture.append(total)
    peak = max((abs(value) for value in mixture), default=1.0) or 1.0
    return [value / peak for value in mixture]


def render_fallback(notes: Iterable[float], duration: float, *, sample_rate: int = SAMPLE_RATE) -> List[float]:
    """Legacy rendering used when no layers are present."""

    notes_list = list(notes)
    if not notes_list:
        return _zeros(max(1, int(sample_rate * duration)))
    note_count = max(len(notes_list), 1)
    samples_per_note = max(1, int(sample_rate * duration / note_count))
    audio = _zeros(samples_per_note * note_count)
    note_duration = duration / note_count
    for idx, freq in enumerate(notes_list):
        start = idx * samples_per_note
        t = _linspace(0.0, note_duration, samples_per_note, endpoint=False)
        for offset, time in enumerate(t):
            waveform = math.sin(2 * math.pi * freq * time)
            envelope = 1.0 - 0.95 * (offset / max(samples_per_note - 1, 1))
            audio[start + offset] = waveform * envelope * 0.5
    peak = max((abs(value) for value in audio), default=1.0) or 1.0
    return [value / peak for value in audio]
