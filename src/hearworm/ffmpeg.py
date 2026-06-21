from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from .chapter import Chapter


@dataclass
class StreamInfo:
    codec_type: str
    codec_name: str


@dataclass
class FormatInfo:
    duration: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class FFChapter:
    title: str
    start_time: float
    end_time: float


@dataclass
class ProbeResult:
    streams: list[StreamInfo]
    format: FormatInfo
    chapters: list[FFChapter] = field(default_factory=list)


@dataclass
class ConvertOpts:
    bitrate: str = ""


@dataclass
class SilenceRange:
    start: timedelta
    end: timedelta


def probe(path: str | Path) -> ProbeResult:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", "-show_chapters", str(path),
    ]
    result = _run(cmd, capture=True)
    data: dict[str, Any] = json.loads(result.stdout)

    streams = [
        StreamInfo(
            codec_type=s.get("codec_type", ""),
            codec_name=s.get("codec_name", ""),
        )
        for s in data.get("streams", [])
    ]

    fmt = data.get("format", {})
    format_info = FormatInfo(
        duration=float(fmt.get("duration", 0)),
        tags={k.lower(): v for k, v in fmt.get("tags", {}).items()},
    )

    chapters = [
        FFChapter(
            title=ch.get("tags", {}).get("title", f"Chapter {i+1}"),
            start_time=float(ch.get("start_time", 0)),
            end_time=float(ch.get("end_time", 0)),
        )
        for i, ch in enumerate(data.get("chapters", []))
    ]

    return ProbeResult(streams=streams, format=format_info, chapters=chapters)


def chapters_from_probe(result: ProbeResult) -> list[Chapter]:
    out: list[Chapter] = []
    for ch in result.chapters:
        out.append(Chapter(
            title=ch.title,
            start=timedelta(seconds=ch.start_time),
            end=timedelta(seconds=ch.end_time),
        ))
    return out


def convert_audio(src: str | Path, dst: str | Path, opts: ConvertOpts | None = None) -> None:
    bitrate = (opts.bitrate if opts else "") or _default_bitrate(str(dst))
    codec = _codec_for_ext(Path(dst).suffix.lower())
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vn", "-c:a", codec, "-b:a", bitrate, str(dst)]
    _run(cmd)


def copy_audio(src: str | Path, dst: str | Path) -> None:
    _run(["ffmpeg", "-y", "-i", str(src), "-vn", "-c:a", "copy", str(dst)])


def concat(inputs: list[str | Path], output: str | Path) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for p in inputs:
            f.write(f"file '{p}'\n")
        list_file = f.name
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
              "-c", "copy", str(output)])
    finally:
        os.unlink(list_file)


def extract_segment(src: str | Path, dst: str | Path,
                    start: timedelta, end: timedelta,
                    opts: ConvertOpts | None = None) -> None:
    ext = Path(str(dst)).suffix.lower()
    if ext == ".mp3":
        bitrate = (opts.bitrate if opts else "") or _default_bitrate(str(dst))
        audio_args = ["-c:a", "libmp3lame", "-b:a", bitrate, "-vn"]
    else:
        audio_args = ["-c", "copy", "-vn"]
    _run([
        "ffmpeg", "-y",
        "-ss", _fmt_duration(start),
        "-to", _fmt_duration(end),
        "-i", str(src),
        *audio_args,
        str(dst),
    ])


def apply_meta(src: str | Path, dst: str | Path,
               metadata_flags: list[str],
               cover_path: str | Path | None = None) -> None:
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if cover_path:
        cmd += ["-i", str(cover_path), "-map", "0:a", "-map", "1:v",
                "-c:v", "mjpeg", "-disposition:v", "attached_pic"]
    else:
        cmd += ["-vn"]
    for flag in metadata_flags:
        cmd += ["-metadata", flag]
    cmd += ["-c:a", "copy", str(dst)]
    _run(cmd)


def extract_cover(src: str | Path, dst: str | Path) -> bool:
    try:
        _run(["ffmpeg", "-y", "-i", str(src), "-an", "-vcodec", "copy", str(dst)])
        return Path(dst).stat().st_size > 0
    except subprocess.CalledProcessError:
        return False


def write_meta(path: str | Path, tags: dict[str, str],
               chapters: list[Chapter], total_secs: float) -> None:
    lines = [";FFMETADATA1"]
    for k, v in tags.items():
        lines.append(f"{k}={_escape_meta(v)}")
    for ch in chapters:
        start_ms = int(ch.start.total_seconds() * 1000)
        end_ms = int(ch.end.total_seconds() * 1000)
        lines.append("[CHAPTER]")
        lines.append("TIMEBASE=1/1000")
        lines.append(f"START={start_ms}")
        lines.append(f"END={end_ms}")
        lines.append(f"title={_escape_meta(ch.title)}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def detect_silence(path: str | Path,
                   min_noise: float = -30.0,
                   min_duration: float = 0.5) -> list[SilenceRange]:
    cmd = [
        "ffmpeg", "-i", str(path),
        "-af", f"silencedetect=noise={min_noise}dB:d={min_duration}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return _parse_silence(result.stderr)


def _parse_silence(output: str) -> list[SilenceRange]:
    ranges: list[SilenceRange] = []
    current_start: float | None = None
    for line in output.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            current_start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and current_start is not None:
            ranges.append(SilenceRange(
                start=timedelta(seconds=current_start),
                end=timedelta(seconds=float(m.group(1))),
            ))
            current_start = None
    return ranges


def _codec_for_ext(ext: str) -> str:
    if ext == ".mp3":
        return "libmp3lame"
    return "aac"


def _default_bitrate(path: str) -> str:
    if path.endswith(".mp3"):
        return "128k"
    return "64k"


def _fmt_duration(d: timedelta) -> str:
    total = d.total_seconds()
    h = int(total // 3600)
    m = int((total % 3600) // 60)
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _escape_meta(s: str) -> str:
    return s.replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", "\\\n")


def _run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=capture, text=capture, check=True)
    return result
