package ffmpeg_test

import (
	"testing"

	"m4b/internal/ffmpeg"
	"github.com/stretchr/testify/require"
)

func TestProbe_MissingFile(t *testing.T) {
	_, err := ffmpeg.Probe("/nonexistent/file.m4b")
	require.Error(t, err)
}
