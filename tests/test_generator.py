from ai_song_generator import (
    AISongGenerator,
    CloudWorkspace,
    SectionLayer,
    SongEditor,
    VocalIntegration,
)


def test_generate_song_basic():
    generator = AISongGenerator()
    project = generator.generate(style="lofi", duration=5.0, seed=42)
    assert project.genre == "Lo-Fi"
    assert len(project.audio) > 0
    peak = max(abs(sample) for sample in project.audio)
    assert 0.9 <= peak <= 1.0


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
    assert len(loaded.audio) == len(project.audio)
    for a, b in zip(loaded.audio, project.audio):
        assert abs(a - b) < 1e-6


def test_sections_include_layers():
    generator = AISongGenerator()
    project = generator.generate(style="lofi", duration=4.0, seed=5)
    assert project.sections
    for section in project.sections:
        assert section.layers, "expected layered instrumentation"
        for layer in section.layers:
            assert isinstance(layer, SectionLayer)
            assert layer.notes, "layer should contain note data"
