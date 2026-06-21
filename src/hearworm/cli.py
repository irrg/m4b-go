from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(name="hearworm", help="Audiobook conversion and manipulation tool.")


def _check_deps() -> None:
    for bin_ in ("ffmpeg", "ffprobe"):
        if not shutil.which(bin_):
            typer.echo(f"error: {bin_} not found in PATH — install ffmpeg >= 4.1", err=True)
            raise typer.Exit(1)


@app.callback()
def main_callback() -> None:
    _check_deps()


@app.command()
def convert(
    input_dir: str = typer.Argument(..., help="Directory of audio files to convert"),
    output_dir: str = typer.Option(..., "--output-dir", "-o", help="Output directory"),
    audio_format: str = typer.Option("mp3", "--audio-format", help="Output format (mp3, m4b, m4a)"),
    audio_bitrate: str = typer.Option("", "--audio-bitrate", help="Output bitrate (e.g. 128k)"),
) -> None:
    """Batch-convert a directory of audio files to another format."""
    from . import convert as conv
    conv.run(conv.Options(
        input_dir=input_dir,
        output_dir=output_dir,
        format=audio_format,
        bitrate=audio_bitrate,
    ))


@app.command()
def split(
    input_file: str = typer.Argument(..., help="Input m4b file"),
    output_dir: str = typer.Option(..., "--output-dir", "-o", help="Output directory"),
    audio_format: str = typer.Option("mp3", "--audio-format", help="Output format (mp3, m4b, m4a)"),
    audio_bitrate: str = typer.Option("", "--audio-bitrate", help="Output bitrate"),
) -> None:
    """Split an m4b with embedded chapters into one file per chapter."""
    from . import split as sp
    sp.run(sp.Options(
        input_file=input_file,
        output_dir=output_dir,
        format=audio_format,
        bitrate=audio_bitrate,
    ))


@app.command()
def merge(
    input_dir: str = typer.Argument(..., help="Directory of audio files to merge"),
    output_file: str = typer.Option(..., "--output-file", "-o", help="Output file path"),
    audio_format: str = typer.Option("m4b", "--audio-format", help="Output format (mp3, m4b, m4a)"),
    audio_bitrate: str = typer.Option("", "--audio-bitrate", help="Output bitrate"),
    name: str = typer.Option("", "--name", help="Audiobook title"),
    artist: str = typer.Option("", "--artist", help="Author / artist"),
    album: str = typer.Option("", "--album", help="Album tag"),
    album_artist: str = typer.Option("", "--album-artist", help="Album artist"),
    genre: str = typer.Option("Audiobook", "--genre", help="Genre"),
    year: str = typer.Option("", "--year", help="Publication year"),
    series: str = typer.Option("", "--series", help="Series name"),
    series_part: str = typer.Option("", "--series-part", help="Series part number"),
) -> None:
    """Combine a directory of audio files into a single file with chapters."""
    from . import merge as mg
    mg.run(mg.Options(
        input_dir=input_dir,
        output_file=output_file,
        format=audio_format,
        bitrate=audio_bitrate,
        tag=mg.TagOptions(
            title=name,
            artist=artist,
            album=album,
            album_artist=album_artist,
            genre=genre,
            year=year,
            series=series,
            series_part=series_part,
        ),
    ))


@app.command()
def chapters(
    input_file: str = typer.Argument(..., help="Input audio file"),
    output_file: str = typer.Option("", "--output-file", "-o", help="Output file (default: overwrite input)"),
    silence_min_noise: float = typer.Option(-30.0, "--silence-min-noise", help="Noise threshold in dB"),
    silence_min_length: float = typer.Option(0.5, "--silence-min-length", help="Minimum silence duration in seconds"),
) -> None:
    """Detect silence and embed chapter markers at silence midpoints."""
    from . import chapters as ch
    ch.run(ch.Options(
        input_file=input_file,
        output_file=output_file,
        silence_min_noise=silence_min_noise,
        silence_min_length=silence_min_length,
    ))


@app.command()
def aax_checksum(
    input_file: str = typer.Argument(..., help="Input .aax file"),
) -> None:
    """Extract the SHA1 checksum from an Audible AAX file."""
    import subprocess, re
    result = subprocess.run(
        ["ffprobe", input_file],
        capture_output=True, text=True,
    )
    m = re.search(r"file checksum == ([0-9a-f]+)", result.stderr)
    if m:
        typer.echo(m.group(1))
    else:
        typer.echo("error: could not extract checksum — is this a valid .aax file?", err=True)
        raise typer.Exit(1)


auth_app = typer.Typer(help="Audible authentication.")
app.add_typer(auth_app, name="auth")


@auth_app.command("login")
def auth_login(
    country: str = typer.Option("us", "--country", "-c", help="Audible marketplace country code"),
) -> None:
    """Log in to Audible and store activation bytes."""
    from . import auth
    ab = auth.login(country=country)
    typer.echo(f"activation_bytes: {ab}")
    typer.echo("Saved to ~/.config/hearworm/auth.json")


@auth_app.command("set-bytes")
def auth_set_bytes(
    activation_bytes: str = typer.Argument(..., help="Activation bytes hex string"),
) -> None:
    """Manually store activation bytes (from rcrack or other source)."""
    from . import auth
    auth.set_activation_bytes(activation_bytes)
    typer.echo("Saved.")


@auth_app.command("show")
def auth_show() -> None:
    """Show stored activation bytes."""
    from . import auth
    ab = auth.get_activation_bytes()
    if ab:
        typer.echo(ab)
    else:
        typer.echo("No activation bytes stored. Run 'hearworm auth login'.", err=True)
        raise typer.Exit(1)
