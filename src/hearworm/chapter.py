from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import IO


@dataclass
class Chapter:
    title: str
    start: timedelta
    end: timedelta

    def duration(self) -> timedelta:
        return self.end - self.start


def total_duration(chapters: list[Chapter]) -> timedelta:
    if not chapters:
        return timedelta()
    return chapters[-1].end


def parse_txt(reader: IO[str]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for line in reader:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\s+(.+)$", line)
        if not m:
            continue
        start = _parse_duration(m.group(1))
        title = m.group(2).strip()
        if chapters:
            chapters[-1].end = start
        chapters.append(Chapter(title=title, start=start, end=start))
    return chapters


def _parse_duration(s: str) -> timedelta:
    parts = s.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    sec_parts = parts[2].split(".")
    seconds = int(sec_parts[0])
    ms = int(sec_parts[1].ljust(3, "0")[:3]) if len(sec_parts) > 1 else 0
    return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=ms)
