import numpy as np

from ai_song_generator import AISongGenerator, CloudWorkspace, SongEditor, VocalIntegration


def test_generate_song_basic():
    generator = AISongGenerator()
    project = generator.generate(style="lofi", duration=5.0, seed=42)
    assert project.genre == "Lo-Fi"
    assert project.audio.size > 0
    assert 0.9 <= float(np.max(np.abs(project.audio))) <= 1.0


def test_editor_tempo_adjustment():
    generator = AISongGenerator()
    project = generator.generate(style="pop", duration=4.0, seed=1)
    original_length = len(project.audio)
    editor = SongEditor()
    editor.adjust_tempo(project, tempo=90)
    assert len(project.audio) != original_length
    assert project.tempo == 90


def test_vocal_blend():
    generator = AISongGenerator()
    vocals = VocalIntegration()
    project = generator.generate(style="ambient", duration=4.0, seed=2)
    vocal_track = vocals.generate_vocals("hello world")
    original_len = len(project.audio)
    vocals_len = len(vocal_track)
    vocals.blend(project, vocal_track)
    assert len(project.audio) == max(original_len, vocals_len)


def test_workspace_roundtrip(tmp_path):
    generator = AISongGenerator()
    workspace = CloudWorkspace(root=tmp_path)
    project = generator.generate(style="jazz", duration=3.0, seed=7)
    saved_path = workspace.save(project)
    assert saved_path.exists()
    loaded = workspace.load(saved_path)
    assert loaded.title == project.title
    assert np.allclose(loaded.audio, project.audio)
