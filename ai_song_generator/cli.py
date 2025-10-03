"""Command line interface for the AI song generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import AISongGenerator, CloudWorkspace, VocalIntegration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Song Generator")
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="Generate a new song")
    create.add_argument("style", help="Genre template key")
    create.add_argument("--duration", type=float, default=30.0)
    create.add_argument("--tempo", type=int)
    create.add_argument("--mood")
    create.add_argument("--output", type=Path, default=Path("output"))

    vocals = subparsers.add_parser("vocals", help="Generate vocals for lyrics")
    vocals.add_argument("lyrics")
    vocals.add_argument("--pitch", type=float, default=440.0)
    vocals.add_argument("--output", type=Path, default=Path("vocals.wav"))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    generator = AISongGenerator()
    vocals = VocalIntegration()
    workspace = CloudWorkspace()

    if args.command == "create":
        project = generator.generate(style=args.style, duration=args.duration, tempo=args.tempo, mood=args.mood)
        workspace.save(project)
        export_path = project.export(args.output, format="wav")
        print(f"Generated {project.title} -> {export_path}")
        return 0
    if args.command == "vocals":
        audio = vocals.generate_vocals(args.lyrics, pitch=args.pitch)
        project = generator.generate(style="ambient", duration=len(audio) / 44100)
        vocals.blend(project, audio)
        export_path = project.export(args.output, format="wav")
        print(f"Generated backing track with vocals -> {export_path}")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
