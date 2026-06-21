from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from . import ffmpeg
from .chapter import Chapter


@dataclass
class Options:
    input_file: str = ""
    output_file: str = ""
    silence_min_noise: float = -30.0
    silence_min_length: float = 0.5


def run(opts: Options) -> None:
    result = ffmpeg.probe(opts.input_file)
    total_secs = result.format.duration

    silences = ffmpeg.detect_silence(
        opts.input_file,
        min_noise=opts.silence_min_noise,
        min_duration=opts.silence_min_length,
    )

    chapters = _silences_to_chapters(silences, total_secs)
    if not chapters:
        raise ValueError("no silence detected — try lowering --silence-min-noise")

    tags = {f.split("=", 1)[0]: f.split("=", 1)[1]
            for f in result.format.tags.items()
            if isinstance(f, tuple)}
    tags = dict(result.format.tags)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tf:
        meta_path = tf.name
    try:
        ffmpeg.write_meta(meta_path, tags, chapters, total_secs)

        output = opts.output_file or opts.input_file
        ext = Path(opts.input_file).suffix

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf2:
            tmp_out = tf2.name
        try:
            import subprocess
            subprocess.run([
                "ffmpeg", "-y",
                "-i", opts.input_file,
                "-i", meta_path,
                "-map_metadata", "1",
                "-c:a", "copy",
                tmp_out,
            ], check=True)
            os.replace(tmp_out, output)
        except Exception:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)
            raise
    finally:
        os.unlink(meta_path)


def _silences_to_chapters(silences: list[ffmpeg.SilenceRange],
                           total_secs: float) -> list[Chapter]:
    boundaries = [timedelta()]
    for s in silences:
        mid = s.start + (s.end - s.start) / 2
        boundaries.append(mid)
    boundaries.append(timedelta(seconds=total_secs))

    chapters: list[Chapter] = []
    for i in range(len(boundaries) - 1):
        chapters.append(Chapter(
            title=f"Chapter {i + 1}",
            start=boundaries[i],
            end=boundaries[i + 1],
        ))
    return chapters
