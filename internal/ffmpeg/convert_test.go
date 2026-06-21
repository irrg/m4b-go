package ffmpeg_test

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"m4b/internal/ffmpeg"
	"github.com/stretchr/testify/require"
)

func makeSineAudio(t *testing.T, path string, durationSecs int) {
	t.Helper()
	cmd := exec.Command("ffmpeg", "-y", "-f", "lavfi",
		"-i", fmt.Sprintf("sine=frequency=440:duration=%d", durationSecs),
		"-c:a", "aac", "-b:a", "64k", path)
	out, err := cmd.CombinedOutput()
	require.NoError(t, err, string(out))
}

func TestConvertToAAC(t *testing.T) {
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		t.Skip("ffmpeg not available")
	}
	dir := t.TempDir()
	input := filepath.Join(dir, "input.m4a")
	output := filepath.Join(dir, "output.m4a")
	makeSineAudio(t, input, 3)

	err := ffmpeg.ConvertToAAC(input, output, ffmpeg.ConvertOpts{Bitrate: "64k"})
	require.NoError(t, err)
	_, err = os.Stat(output)
	require.NoError(t, err)
}

func TestExtractSegment(t *testing.T) {
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		t.Skip("ffmpeg not available")
	}
	dir := t.TempDir()
	input := filepath.Join(dir, "input.m4a")
	output := filepath.Join(dir, "segment.m4a")
	makeSineAudio(t, input, 10)

	err := ffmpeg.ExtractSegment(input, output, 2*time.Second, 5*time.Second, []string{"title=Seg One"})
	require.NoError(t, err)
	_, err = os.Stat(output)
	require.NoError(t, err)
}
