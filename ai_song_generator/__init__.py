"""AI Song Generator package providing end-to-end music creation tools."""

from .generator import AISongGenerator, SongProject
from .structures import SectionLayer, SongSection
from .editor import SongEditor
from .templates import GENRE_TEMPLATES
from .vocals import VocalIntegration
from .workspace import CloudWorkspace

__all__ = [
    "AISongGenerator",
    "SongProject",
    "SongSection",
    "SectionLayer",
    "SongEditor",
    "GENRE_TEMPLATES",
    "VocalIntegration",
    "CloudWorkspace",
]
