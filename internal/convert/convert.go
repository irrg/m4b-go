package convert

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"m4b/internal/ffmpeg"
)

type Options struct {
	InputDir   string
	InputFiles []string
	OutputDir  string
	Format     string
	Bitrate    string
}

var audioExts = map[string]bool{
	".mp3": true, ".m4a": true, ".m4b": true, ".aac": true,
	".flac": true, ".ogg": true, ".wav": true, ".wma": true,
}

func Run(opts Options) error {
	if err := os.MkdirAll(opts.OutputDir, 0755); err != nil {
		return err
	}
	inputs, err := collectInputs(opts)
	if err != nil {
		return err
	}
	if len(inputs) == 0 {
		return fmt.Errorf("no audio files found in %q", opts.InputDir)
	}

	ext := "." + strings.ToLower(coalesce(opts.Format, "mp3"))

	for i, input := range inputs {
		base := strings.TrimSuffix(filepath.Base(input), filepath.Ext(input))
		output := filepath.Join(opts.OutputDir, base+ext)

		probe, err := ffmpeg.Probe(input)
		if err != nil {
			return fmt.Errorf("probe %q: %w", input, err)
		}

		if isCompatible(probe, opts.Format) {
			fmt.Printf("[%d/%d] copy   %s\n", i+1, len(inputs), filepath.Base(input))
			if err := ffmpeg.CopyAudio(input, output); err != nil {
				return fmt.Errorf("copy %q: %w", input, err)
			}
		} else {
			fmt.Printf("[%d/%d] encode %s\n", i+1, len(inputs), filepath.Base(input))
			if err := ffmpeg.ConvertAudio(input, output, ffmpeg.ConvertOpts{Bitrate: coalesce(opts.Bitrate, defaultBitrate(opts.Format))}); err != nil {
				return fmt.Errorf("convert %q: %w", input, err)
			}
		}
	}
	return nil
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
	return files, nil
}

func isCompatible(probe *ffmpeg.ProbeResult, format string) bool {
	for _, s := range probe.Streams {
		if s.CodecType == "audio" {
			switch strings.ToLower(format) {
			case "mp3":
				return s.CodecName == "mp3"
			default:
				return s.CodecName == "aac"
			}
		}
	}
	return false
}

func defaultBitrate(format string) string {
	if strings.ToLower(format) == "mp3" {
		return "128k"
	}
	return "64k"
}

func coalesce(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
