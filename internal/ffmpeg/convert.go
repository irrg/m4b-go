package ffmpeg

import (
	"fmt"
	"os/exec"
	"strconv"
	"time"
)

type ConvertOpts struct {
	Bitrate    string
	SampleRate int
	Channels   int
}

func ConvertToAAC(input, output string, opts ConvertOpts) error {
	args := []string{"-y", "-i", input, "-c:a", "aac"}
	if opts.Bitrate != "" {
		args = append(args, "-b:a", opts.Bitrate)
	}
	if opts.SampleRate > 0 {
		args = append(args, "-ar", strconv.Itoa(opts.SampleRate))
	}
	if opts.Channels > 0 {
		args = append(args, "-ac", strconv.Itoa(opts.Channels))
	}
	args = append(args, "-vn", output)
	return run(args...)
}

// Concat assembles a concat list + optional ffmetadata file into an m4b.
func Concat(listFile, output, metaFile string) error {
	args := []string{"-y", "-f", "concat", "-safe", "0", "-i", listFile}
	if metaFile != "" {
		args = append(args, "-i", metaFile, "-map_metadata", "1")
	}
	args = append(args, "-c", "copy", "-f", "mp4", output)
	return run(args...)
}

// ExtractSegment cuts [start, end) from input into output with optional metadata flags.
// metaFlags is a list of "key=value" strings passed as -metadata arguments.
func ExtractSegment(input, output string, start, end time.Duration, metaFlags []string) error {
	args := []string{"-y", "-i", input,
		"-ss", formatDuration(start),
		"-to", formatDuration(end),
		"-c", "copy",
	}
	for _, f := range metaFlags {
		args = append(args, "-metadata", f)
	}
	args = append(args, output)
	return run(args...)
}

// ApplyMeta copies input to output while applying a prewritten ffmetadata file.
func ApplyMeta(input, output, metaFile string) error {
	return run("-y", "-i", input, "-i", metaFile,
		"-map_metadata", "1", "-c", "copy", output)
}

// ExtractCover pulls attached cover art to a JPEG file.
func ExtractCover(input, output string) error {
	return run("-y", "-i", input, "-an", "-vcodec", "copy", output)
}

func run(args ...string) error {
	cmd := exec.Command("ffmpeg", args...)
	if out, err := cmd.CombinedOutput(); err != nil {
		cap := min(3, len(args))
		return fmt.Errorf("ffmpeg %v failed: %w\n%s", args[:cap], err, string(out))
	}
	return nil
}

func formatDuration(d time.Duration) string {
	total := d.Milliseconds()
	ms := total % 1000
	total /= 1000
	s := total % 60
	total /= 60
	m := total % 60
	h := total / 60
	return fmt.Sprintf("%02d:%02d:%02d.%03d", h, m, s, ms)
}
