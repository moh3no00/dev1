"""Predefined genre and mood templates."""

GENRE_TEMPLATES = {
    "lofi": {
        "genre": "Lo-Fi",
        "mood": "chill",
        "tempo": 85,
        "scale": [220.0, 246.94, 277.18, 293.66, 329.63, 369.99, 415.3],
        "sections": ["intro", "verse", "chorus", "outro"],
        "keywords": ["study", "lofi", "relax", "coffee"],
    },
    "pop": {
        "genre": "Pop",
        "mood": "upbeat",
        "tempo": 120,
        "scale": [261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 493.88],
        "sections": ["intro", "verse", "chorus", "bridge", "chorus"],
        "keywords": ["pop", "catchy", "radio"],
    },
    "cinematic": {
        "genre": "Cinematic",
        "mood": "epic",
        "tempo": 100,
        "scale": [174.61, 196.0, 220.0, 246.94, 277.18, 311.13, 349.23],
        "sections": ["intro", "build", "climax", "resolution"],
        "keywords": ["film", "orchestra", "cinematic"],
    },
    "edm": {
        "genre": "EDM",
        "mood": "energetic",
        "tempo": 128,
        "scale": [261.63, 293.66, 329.63, 391.0, 440.0, 523.25, 587.33],
        "sections": ["intro", "build", "drop", "breakdown"],
        "keywords": ["club", "dance", "edm"],
    },
    "jazz": {
        "genre": "Jazz",
        "mood": "smooth",
        "tempo": 110,
        "scale": [261.63, 311.13, 349.23, 392.0, 466.16, 523.25, 587.33],
        "sections": ["intro", "theme", "solo", "theme"],
        "keywords": ["jazz", "sax", "swing"],
    },
    "ambient": {
        "genre": "Ambient",
        "mood": "dreamy",
        "tempo": 60,
        "scale": [110.0, 146.83, 196.0, 220.0, 261.63, 329.63, 392.0],
        "sections": ["drone", "texture", "swells", "release"],
        "keywords": ["ambient", "relax", "space"],
    },
}
