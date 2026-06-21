package tag_test

import (
	"testing"

	"m4b/internal/tag"
	"github.com/stretchr/testify/assert"
)

func TestComputeSortTags_SeriesAndPart(t *testing.T) {
	at := tag.AudioTag{
		Title:      "Harry Potter and the Chamber of Secrets",
		Series:     "Harry Potter",
		SeriesPart: "2",
	}
	at.ComputeSortTags()
	assert.Equal(t, "Harry Potter 2 - Harry Potter and the Chamber of Secrets", at.SortName)
	assert.Equal(t, "Harry Potter 2", at.SortAlbum)
}

func TestComputeSortTags_NoOverwriteExisting(t *testing.T) {
	at := tag.AudioTag{
		Title:      "Some Book",
		Series:     "Some Series",
		SeriesPart: "1",
		SortName:   "manually set",
	}
	at.ComputeSortTags()
	assert.Equal(t, "manually set", at.SortName)
}

func TestComputeSortTags_NoSeries(t *testing.T) {
	at := tag.AudioTag{Title: "Standalone Book"}
	at.ComputeSortTags()
	assert.Empty(t, at.SortName)
	assert.Empty(t, at.SortAlbum)
}

func TestToFFmpegFlags_SkipsEmpty(t *testing.T) {
	at := tag.AudioTag{Title: "My Book", Artist: ""}
	flags := at.ToFFmpegFlags()
	found := false
	for _, f := range flags {
		if f == "artist=" {
			found = true
		}
	}
	assert.False(t, found, "empty artist should not appear in flags")
	assert.Contains(t, flags, "title=My Book")
}
