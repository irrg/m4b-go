# m4b-go

A Go port of [m4b-tool](https://github.com/sandreas/m4b-tool) — merge, split, and chapter-mark audiobook m4b files. Single static binary. **ffmpeg is the only runtime dependency.**

Drops the original's PHP runtime, custom mp4v2 fork, fdkaac, and tone binary. Sort order tags (series/part) are written directly via ffmpeg metadata flags.

## License

MIT License — see [LICENSE](LICENSE) for full text.

## Requirements

- Go 1.22+ (to build)
- ffmpeg ≥ 4.1 (runtime, must be in PATH)

## Install

```bash
go install m4b/...@latest
```

Or build from source:

```bash
git clone https://github.com/irrg/m4b-go
cd m4b-go
go build -o m4b-tool .
```

## Usage

### merge

Combine a directory of audio files into a single `.m4b` with chapters.

```bash
m4b-tool merge /path/to/audio-files/ \
  --output-file output.m4b \
  --name "Harry Potter and the Chamber of Secrets" \
  --artist "J.K. Rowling" \
  --series "Harry Potter" \
  --series-part "2"
```

One chapter is created per input file, named from the file's `title` tag (or the filename if no tag exists). Files are sorted alphabetically, so prefix them with track numbers (`01-`, `02-`, etc.) for correct order.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-file` | *(required)* | Output `.m4b` path |
| `--name` | | Audiobook title |
| `--artist` | | Author / artist |
| `--album` | same as `--name` | Album tag |
| `--album-artist` | | Album artist tag |
| `--genre` | `Audiobook` | Genre tag |
| `--year` | | Publication year |
| `--series` | | Series name (used to compute sort order) |
| `--series-part` | | Series part number |
| `--audio-bitrate` | `64k` | Output AAC bitrate |

**Series sort order:** When `--series` and `--series-part` are set, `sort_name` is automatically computed as `"{series} {part} - {title}"` (e.g. `Harry Potter 2 - Harry Potter and the Chamber of Secrets`). Players that respect sort tags will order the series correctly regardless of alphabetical title order.

### split

Split an `.m4b` into one file per chapter.

```bash
m4b-tool split input.m4b --output-dir ./chapters/
```

Output files are named `001-Chapter Title.m4b`. Tags from the source file are preserved on each output file.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | *(required)* | Directory for output files |
| `--audio-format` | `m4b` | Output format: `m4b`, `mp3`, `m4a` |

### chapters

Detect silence in an audio file and embed chapter markers at silence midpoints.

```bash
m4b-tool chapters input.m4b --output-file output.m4b
```

Omit `--output-file` to overwrite the input in-place.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-file` | *(overwrites input)* | Output file path |
| `--silence-min-noise` | `-30` | Noise threshold in dB |
| `--silence-min-length` | `0.5` | Minimum silence duration in seconds |

## What's not included (v1)

- MusicBrainz chapter name lookup
- EPUB / Audible JSON / Overdrive metadata sources
- Parallel batch processing
- fdkaac / tone support

## Differences from sandreas/m4b-tool

| Feature | m4b-tool (PHP) | m4b-go |
|---------|---------------|--------|
| Runtime | PHP 8.2 + Composer | None (static binary) |
| MP4 tagging | Custom mp4v2 fork | ffmpeg `-metadata` flags |
| Sort tags | Custom `mp4tags` CLI | ffmpeg `sort_name`, `sort_album` |
| High-efficiency AAC | fdkaac (optional) | ffmpeg built-in AAC |
| Tone integration | tone binary (optional) | Not included |
| MusicBrainz | Supported | Not included (v1) |
