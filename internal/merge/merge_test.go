package merge_test

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"m4b/internal/merge"
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

func TestMerge_TwoFiles(t *testing.T) {
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		t.Skip("ffmpeg not available")
	}
	dir := t.TempDir()
	makeSineAudio(t, filepath.Join(dir, "01-intro.m4a"), 2)
	makeSineAudio(t, filepath.Join(dir, "02-chapter1.m4a"), 3)
	output := filepath.Join(dir, "output.m4b")

	err := merge.Run(merge.Options{
		InputDir:   dir,
		OutputFile: output,
		Tag:        merge.TagOptions{Title: "Test Book", Artist: "Test Author"},
	})
	require.NoError(t, err)
	_, err = os.Stat(output)
	require.NoError(t, err)
}

func TestMerge_NoInputFiles(t *testing.T) {
	err := merge.Run(merge.Options{
		InputDir:   t.TempDir(),
		OutputFile: "/tmp/nope.m4b",
	})
	require.Error(t, err)
}
