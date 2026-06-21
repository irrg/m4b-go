from __future__ import annotations

from dataclasses import dataclass, field

from .ffmpeg import ProbeResult


@dataclass
class AudioTag:
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    comment: str = ""
    year: str = ""
    genre: str = ""
    composer: str = ""
    copyright: str = ""
    description: str = ""
    long_description: str = ""
    sort_name: str = ""
    sort_album: str = ""
    sort_artist: str = ""
    series: str = ""
    series_part: str = ""
    cover_path: str = ""

    def compute_sort_tags(self) -> None:
        if not self.series or not self.series_part:
            return
        if not self.sort_name:
            self.sort_name = f"{self.series} {self.series_part} - {self.title}"
        if not self.sort_album:
            self.sort_album = f"{self.series} {self.series_part}"

    def to_ffmpeg_flags(self) -> list[str]:
        mapping = {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "comment": self.comment,
            "date": self.year,
            "genre": self.genre,
            "composer": self.composer,
            "copyright": self.copyright,
            "description": self.description,
            "synopsis": self.long_description,
            "sort_name": self.sort_name,
            "sort_album": self.sort_album,
            "sort_artist": self.sort_artist,
        }
        return [f"{k}={v}" for k, v in mapping.items() if v]


def from_probe_result(r: ProbeResult) -> AudioTag:
    tags = r.format.tags
    return AudioTag(
        title=tags.get("title", ""),
        artist=tags.get("artist", ""),
        album=tags.get("album", ""),
        album_artist=tags.get("album_artist", ""),
        comment=tags.get("comment", ""),
        year=tags.get("date", ""),
        genre=tags.get("genre", ""),
        composer=tags.get("composer", ""),
        copyright=tags.get("copyright", ""),
        description=tags.get("description", ""),
        long_description=tags.get("synopsis", ""),
        sort_name=tags.get("sort_name", ""),
        sort_album=tags.get("sort_album", ""),
        sort_artist=tags.get("sort_artist", ""),
    )
