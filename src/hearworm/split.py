from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import ffmpeg
from .tag import from_probe_result


@dataclass
class Options:
    input_file: str = ""
    output_dir: str = ""
    format: str = "mp3"
    bitrate: str = ""


def run(opts: Options) -> None:
    os.makedirs(opts.output_dir, exist_ok=True)
    result = ffmpeg.probe(opts.input_file)
    chapters = ffmpeg.chapters_from_probe(result)
    if not chapters:
        raise ValueError(f"no chapters found in {opts.input_file!r}")

    fmt = opts.format or "mp3"
    ext = "." + fmt.lower()
    tag = from_probe_result(result)
    total = len(chapters)

    for i, ch in enumerate(chapters, 1):
        safe_title = _sanitize(ch.title)
        dst = str(Path(opts.output_dir) / f"{i:03d}-{safe_title}{ext}")
        print(f"[{i}/{total}] {ch.title}")
        ffmpeg.extract_segment(opts.input_file, dst, ch.start, ch.end)

        flags = from_probe_result(result).to_ffmpeg_flags()
        title_flag = f"title={ch.title}"
        flags = [f for f in flags if not f.startswith("title=")] + [title_flag]

        import tempfile, subprocess
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
            tmp = tf.name
        try:
            cmd = ["ffmpeg", "-y", "-i", dst]
            for flag in flags:
                cmd += ["-metadata", flag]
            cmd += ["-c:a", "copy", tmp]
            subprocess.run(cmd, check=True, capture_output=True)
            os.replace(tmp, dst)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


def _sanitize(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name.strip()[:200]
