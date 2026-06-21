# hearworm

Download, convert, split, merge, and chapter-mark audiobook files. **ffmpeg is the only runtime dependency.**

Supports mp3, m4b, m4a, aac, flac, ogg, wav, and wma as input or output. Primary use case: downloading Audible books and splitting m4b audiobooks into per-chapter mp3 files.

## License

MIT License — see [LICENSE](LICENSE) for full text.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- ffmpeg ≥ 4.1 (must be in PATH)

## Install

```bash
git clone https://github.com/irrg/hearworm
cd hearworm
uv run hearworm --help
```

## Audible

### auth login

Authenticate with Audible and store credentials locally.

```bash
uv run hearworm auth login
uv run hearworm auth login --country uk
```

Credentials are saved to `~/.config/hearworm/auth.json`. Activation bytes are fetched automatically and stored alongside them.

```bash
uv run hearworm auth show          # print stored activation bytes
uv run hearworm auth set-bytes DEADBEEF  # set activation bytes manually
```

### library

List your Audible library.

```bash
uv run hearworm library
uv run hearworm library "wind"     # filter by title substring
```

### download

Download an Audible book and decrypt it to m4b. Accepts a partial title or ASIN.

```bash
uv run hearworm download "Name of the Wind" --output-dir ~/audiobooks/
uv run hearworm download B002V5HSCM --output-dir ~/audiobooks/
```

Supports both AAXC (current Audible format) and AAX. The raw encrypted file is cached in the output directory and reused on retry; it is deleted after successful decryption. ffmpeg output is written to `errors.txt` in the current directory on failure.

To download and immediately split to mp3:

```bash
uv run hearworm download "Name of the Wind" -o ~/audiobooks/ \
  --then-convert mp3 --audio-bitrate 128k
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | `.` | Directory to save the m4b |
| `--then-convert` | | Also convert to this format after download (e.g. `mp3`) |
| `--audio-bitrate` | | Bitrate for `--then-convert` |

## Conversion

### convert

Batch-convert a directory of audio files to another format.

```bash
uv run hearworm convert /path/to/audiobooks/ --output-dir ./mp3s/ --audio-format mp3
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | *(required)* | Directory for output files |
| `--audio-format` | `mp3` | Output format: `mp3`, `m4b`, `m4a` |
| `--audio-bitrate` | `128k` mp3 / `64k` aac | Output bitrate |

### split

Split an m4b (or any file with embedded chapters) into one file per chapter.

```bash
uv run hearworm split input.m4b --output-dir ./chapters/ --audio-format mp3
```

Output files are named `001-Chapter Title.mp3`. Tags from the source file are preserved on each output file.

For files without embedded chapters, use `hearworm chapters` first to detect silence and embed markers, then split.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | *(required)* | Directory for output files |
| `--audio-format` | `mp3` | Output format: `mp3`, `m4b`, `m4a` |
| `--audio-bitrate` | | Output bitrate |

### merge

Combine a directory of audio files into a single file with embedded chapters.

```bash
uv run hearworm merge /path/to/audio-files/ \
  --output-file output.m4b \
  --name "The Name of the Wind" \
  --artist "Patrick Rothfuss" \
  --series "Kingkiller Chronicle" \
  --series-part "1"
```

One chapter is created per input file, named from the file's `title` tag (or filename). Files are sorted alphabetically — prefix with track numbers (`01-`, `02-`) for correct order.

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-file` | *(required)* | Output file path |
| `--audio-format` | `m4b` | Output format: `mp3`, `m4b`, `m4a` |
| `--audio-bitrate` | | Output bitrate |
| `--name` | | Audiobook title |
| `--artist` | | Author / artist |
| `--album` | same as `--name` | Album tag |
| `--album-artist` | | Album artist tag |
| `--genre` | `Audiobook` | Genre tag |
| `--year` | | Publication year |
| `--series` | | Series name |
| `--series-part` | | Series part number |

When `--series` and `--series-part` are set, `sort_name` is computed as `"{series} {part} - {title}"` so players order the series correctly.

### chapters

Detect silence and embed chapter markers at silence midpoints. Use this before `split` on files that have no existing chapters.

```bash
uv run hearworm chapters input.mp3                        # overwrite in-place
uv run hearworm chapters input.mp3 --output-file out.mp3  # write to new file
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-file` | *(overwrites input)* | Output file path |
| `--silence-min-noise` | `-30` | Noise threshold in dB |
| `--silence-min-length` | `0.5` | Minimum silence duration in seconds |

### aax-checksum

Extract the SHA1 checksum from an AAX file (useful for looking up activation bytes).

```bash
uv run hearworm aax-checksum input.aax
```
