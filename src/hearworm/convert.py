from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import ffmpeg

AUDIO_EXTS = {".mp3", ".m4a", ".m4b", ".aac", ".flac", ".ogg", ".wav", ".wma"}


@dataclass
class Options:
    input_dir: str = ""
    input_files: list[str] = field(default_factory=list)
    output_dir: str = ""
    format: str = "mp3"
    bitrate: str = ""


def run(opts: Options) -> None:
    os.makedirs(opts.output_dir, exist_ok=True)
    inputs = _collect_inputs(opts)
    if not inputs:
        raise ValueError(f"no audio files found in {opts.input_dir!r}")

    ext = "." + (opts.format or "mp3").lower()
    total = len(inputs)

    for i, src in enumerate(inputs, 1):
        stem = Path(src).stem
        dst = str(Path(opts.output_dir) / (stem + ext))

        result = ffmpeg.probe(src)
        if _is_compatible(result, opts.format):
            print(f"[{i}/{total}] copy   {Path(src).name}")
            ffmpeg.copy_audio(src, dst)
        else:
            print(f"[{i}/{total}] encode {Path(src).name}")
            bitrate = opts.bitrate or _default_bitrate(opts.format)
            ffmpeg.convert_audio(src, dst, ffmpeg.ConvertOpts(bitrate=bitrate))


def _collect_inputs(opts: Options) -> list[str]:
    if opts.input_files:
        return opts.input_files
    entries = sorted(Path(opts.input_dir).iterdir())
    return [str(e) for e in entries if e.is_file() and e.suffix.lower() in AUDIO_EXTS]


def _is_compatible(result: ffmpeg.ProbeResult, fmt: str) -> bool:
    for s in result.streams:
        if s.codec_type == "audio":
            if fmt.lower() == "mp3":
                return s.codec_name == "mp3"
            return s.codec_name == "aac"
    return False


def _default_bitrate(fmt: str) -> str:
    return "128k" if fmt.lower() == "mp3" else "64k"
