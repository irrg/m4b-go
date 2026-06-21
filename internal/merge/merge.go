package merge

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"m4b/internal/chapter"
	"m4b/internal/ffmpeg"
	"m4b/internal/tag"
)

type TagOptions struct {
	Title       string
	Artist      string
	Album       string
	AlbumArtist string
	Genre       string
	Year        string
	Series      string
	SeriesPart  string
	Bitrate     string
}

type Options struct {
	InputDir   string
	InputFiles []string
	OutputFile string
	Tag        TagOptions
}

var audioExts = map[string]bool{
	".mp3": true, ".m4a": true, ".m4b": true, ".aac": true,
	".flac": true, ".ogg": true, ".wav": true, ".wma": true,
}

func Run(opts Options) error {
	inputs, err := collectInputs(opts)
	if err != nil {
		return err
	}
	if len(inputs) == 0 {
		return fmt.Errorf("no audio files found in %q", opts.InputDir)
	}

	tmpDir, err := os.MkdirTemp("", "m4b-merge-*")
	if err != nil {
		return err
	}
	defer os.RemoveAll(tmpDir)

	var chapters chapter.List
	var concatLines []string
	var offset time.Duration

	for i, input := range inputs {
		probe, err := ffmpeg.Probe(input)
		if err != nil {
			return fmt.Errorf("probe %q: %w", input, err)
		}
		dur, err := ffmpeg.ParseSeconds(probe.Format.Duration)
		if err != nil {
			return fmt.Errorf("duration for %q: %w", input, err)
		}

		tmp := filepath.Join(tmpDir, fmt.Sprintf("%04d.m4a", i))
		if err := ffmpeg.ConvertToAAC(input, tmp, ffmpeg.ConvertOpts{Bitrate: coalesce(opts.Tag.Bitrate, "64k")}); err != nil {
			return fmt.Errorf("convert %q: %w", input, err)
		}

		title := probe.Format.Tags["title"]
		if title == "" {
			title = strings.TrimSuffix(filepath.Base(input), filepath.Ext(input))
		}
		chapters = append(chapters, chapter.Chapter{
			Title: title,
			Start: offset,
			End:   offset + dur,
		})
		offset += dur
		concatLines = append(concatLines, fmt.Sprintf("file '%s'", tmp))
	}

	concatFile := filepath.Join(tmpDir, "concat.txt")
	if err := os.WriteFile(concatFile, []byte(strings.Join(concatLines, "\n")), 0644); err != nil {
		return err
	}

	at := tag.AudioTag{
		Title:       opts.Tag.Title,
		Artist:      opts.Tag.Artist,
		Album:       coalesce(opts.Tag.Album, opts.Tag.Title),
		AlbumArtist: opts.Tag.AlbumArtist,
		Genre:       coalesce(opts.Tag.Genre, "Audiobook"),
		Year:        opts.Tag.Year,
		Series:      opts.Tag.Series,
		SeriesPart:  opts.Tag.SeriesPart,
	}
	at.ComputeSortTags()

	metaFile := filepath.Join(tmpDir, "meta.txt")
	if err := ffmpeg.WriteMeta(metaFile, tagsMap(at), chapters, offset); err != nil {
		return err
	}

	return ffmpeg.Concat(concatFile, opts.OutputFile, metaFile)
}

func collectInputs(opts Options) ([]string, error) {
	if len(opts.InputFiles) > 0 {
		return opts.InputFiles, nil
	}
	entries, err := os.ReadDir(opts.InputDir)
	if err != nil {
		return nil, err
	}
	var files []string
	for _, e := range entries {
		if !e.IsDir() && audioExts[strings.ToLower(filepath.Ext(e.Name()))] {
			files = append(files, filepath.Join(opts.InputDir, e.Name()))
		}
	}
	sort.Strings(files)
	return files, nil
}

func tagsMap(at tag.AudioTag) map[string]string {
	m := map[string]string{}
	for _, kv := range at.ToFFmpegFlags() {
		parts := strings.SplitN(kv, "=", 2)
		if len(parts) == 2 {
			m[parts[0]] = parts[1]
		}
	}
	return m
}

func coalesce(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
