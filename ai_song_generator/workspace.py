"""Simple cloud-like storage for song projects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .generator import SongProject
from .structures import SongSection


class CloudWorkspace:
    """Persist projects to a JSON-based storage directory."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.home() / ".ai_song_workspace"
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, project: SongProject) -> Path:
        payload = {
            "metadata": {
                "title": project.title,
                "genre": project.genre,
                "mood": project.mood,
                "tempo": project.tempo,
                "sections": [section.to_dict() for section in project.sections],
            },
            "audio": [float(sample) for sample in project.audio],
        }
        path = self.root / f"{project.title.replace(' ', '_')}.json"
        path.write_text(json.dumps(payload))
        return path

    def list_projects(self) -> List[Path]:
        return sorted(self.root.glob("*.json"))

    def load(self, path: Path) -> SongProject:
        data = json.loads(Path(path).read_text())
        metadata = data["metadata"]
        sections = [SongSection.from_dict(section) for section in metadata["sections"]]
        audio = [float(sample) for sample in data.get("audio", [])]
        return SongProject(
            title=metadata["title"],
            genre=metadata["genre"],
            mood=metadata["mood"],
            tempo=metadata["tempo"],
            sections=sections,
            audio=audio,
        )
