from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import ffmpeg
from .convert import AUDIO_EXTS, _is_compatible
from .chapter import Chapter, total_duration
from .tag import AudioTag


@dataclass
class TagOptions:
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    comment: str = ""
    year: str = ""
    genre: str = "Audiobook"
    series: str = ""
    series_part: str = ""
    cover_path: str = ""


@dataclass
class Options:
    input_dir: str = ""
    input_files: list[str] = field(default_factory=list)
    output_file: str = ""
    format: str = "m4b"
    bitrate: str = ""
    tag: TagOptions = field(default_factory=TagOptions)


def run(opts: Options) -> None:
    inputs = _collect_inputs(opts)
    if not inputs:
        raise ValueError(f"no audio files found in {opts.input_dir!r}")

    fmt = opts.format or "m4b"
    target_ext = "." + fmt.lower()
    bitrate = opts.bitrate or ("128k" if fmt == "mp3" else "64k")

    with tempfile.TemporaryDirectory() as tmp:
        encoded: list[str] = []
        chapters: list[Chapter] = []
        cursor = __import__("datetime").timedelta()

        for i, src in enumerate(inputs, 1):
            result = ffmpeg.probe(src)
            dur = __import__("datetime").timedelta(seconds=result.format.duration)

            src_tags = result.format.tags
            title = src_tags.get("title") or Path(src).stem

            chapter_start = cursor
            cursor += dur
            chapters.append(Chapter(title=title, start=chapter_start, end=cursor))

            enc_path = str(Path(tmp) / f"{i:03d}{target_ext}")
            if _is_compatible(result, fmt):
                print(f"[{i}/{len(inputs)}] copy   {Path(src).name}")
                ffmpeg.copy_audio(src, enc_path)
            else:
                print(f"[{i}/{len(inputs)}] encode {Path(src).name}")
                ffmpeg.convert_audio(src, enc_path, ffmpeg.ConvertOpts(bitrate=bitrate))
            encoded.append(enc_path)

        merged = str(Path(tmp) / ("merged" + target_ext))
        ffmpeg.concat(encoded, merged)

        tag = AudioTag(
            title=opts.tag.title,
            artist=opts.tag.artist,
            album=opts.tag.album or opts.tag.title,
            album_artist=opts.tag.album_artist,
            comment=opts.tag.comment,
            year=opts.tag.year,
            genre=opts.tag.genre,
            series=opts.tag.series,
            series_part=opts.tag.series_part,
            cover_path=opts.tag.cover_path,
        )
        tag.compute_sort_tags()

        meta_path = str(Path(tmp) / "meta.txt")
        tag_dict = {f.split("=", 1)[0]: f.split("=", 1)[1] for f in tag.to_ffmpeg_flags()}
        ffmpeg.write_meta(meta_path, tag_dict, chapters, cursor.total_seconds())

        os.makedirs(Path(opts.output_file).parent, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", merged,
            "-i", meta_path,
            "-map_metadata", "1",
            "-c:a", "copy",
            opts.output_file,
        ]
        import subprocess
        subprocess.run(cmd, check=True)


def _collect_inputs(opts: Options) -> list[str]:
    if opts.input_files:
        return opts.input_files
    entries = sorted(Path(opts.input_dir).iterdir())
    return [str(e) for e in entries if e.is_file() and e.suffix.lower() in AUDIO_EXTS]
