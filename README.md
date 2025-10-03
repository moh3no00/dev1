# AI Song Generator Platform

This repository provides a lightweight, fully offline simulation of the AI song
creation workflow described in the brief. It includes utilities for
procedurally generating instrumental tracks, editing them, integrating vocals,
and storing projects in a cloud-like workspace.

## Features

- **AI Song Generator** – Combine text prompts or preset styles to produce
  royalty-free instrumental tracks.
- **Custom Song Editing** – Modify tempo, instrumentation, and structure through
  the programmatic editor utilities.
- **Genre & Mood Templates** – Start from curated styles such as lo-fi, pop,
  cinematic, EDM, jazz, and ambient.
- **Vocal Integration** – Generate synthetic vocal melodies from lyrics or blend
  user-provided vocal tracks.
- **Royalty-Free Downloads** – Export your songs as WAV by default, or MP3 when
  `pydub` and `ffmpeg` are available.
- **User-Friendly Interface** – Use the command-line interface to create tracks
  without any DAW experience.
- **Cloud-Based Workspace** – Save and load projects via a JSON-based storage
  directory that can be synced across machines.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Generate a song:

```bash
python -m ai_song_generator.cli create lofi --duration 20 --output tracks/my_song
```

Create a backing track with AI vocals:

```bash
python -m ai_song_generator.cli vocals "dreams in the neon skyline"
```

Exported files are stored in the `output` directory by default and are safe to
use in personal or commercial projects thanks to their procedural origin.

## Testing

```bash
pytest
```
