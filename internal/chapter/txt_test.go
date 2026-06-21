package chapter_test

import (
	"strings"
	"testing"
	"time"

	"m4b/internal/chapter"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestParseTxt_Basic(t *testing.T) {
	input := "00:00:00.000 Intro\n00:05:30.000 Chapter 1\n01:22:15.500 Chapter 2\n"
	list, err := chapter.ParseTxt(strings.NewReader(input))
	require.NoError(t, err)
	require.Len(t, list, 3)
	assert.Equal(t, "Intro", list[0].Title)
	assert.Equal(t, time.Duration(0), list[0].Start)
	assert.Equal(t, 5*time.Minute+30*time.Second, list[1].Start)
	assert.Equal(t, 82*time.Minute+15*time.Second+500*time.Millisecond, list[2].Start)
	assert.Equal(t, 82*time.Minute+15*time.Second+500*time.Millisecond, list[1].End)
}

func TestParseTxt_Empty(t *testing.T) {
	list, err := chapter.ParseTxt(strings.NewReader(""))
	require.NoError(t, err)
	assert.Empty(t, list)
}

func TestParseTxt_InvalidLine(t *testing.T) {
	_, err := chapter.ParseTxt(strings.NewReader("not a timestamp\n"))
	require.Error(t, err)
}
