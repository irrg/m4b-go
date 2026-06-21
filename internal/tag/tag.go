package tag

import (
	"fmt"
	"strings"

	"m4b/internal/ffmpeg"
)

type AudioTag struct {
	Title           string
	Artist          string
	Album           string
	AlbumArtist     string
	Comment         string
	Year            string
	Genre           string
	Composer        string
	Copyright       string
	Description     string
	LongDescription string
	SortName        string
	SortAlbum       string
	SortArtist      string
	Series          string
	SeriesPart      string
	CoverPath       string
}

func (t *AudioTag) ComputeSortTags() {
	if t.Series == "" || t.SeriesPart == "" {
		return
	}
	if t.SortName == "" {
		t.SortName = fmt.Sprintf("%s %s - %s", t.Series, t.SeriesPart, t.Title)
	}
	if t.SortAlbum == "" {
		t.SortAlbum = fmt.Sprintf("%s %s", t.Series, t.SeriesPart)
	}
}

// ToFFmpegFlags returns "key=value" strings for use with ffmpeg -metadata flags.
func (t AudioTag) ToFFmpegFlags() []string {
	pairs := map[string]string{
		"title":        t.Title,
		"artist":       t.Artist,
		"album":        t.Album,
		"album_artist": t.AlbumArtist,
		"comment":      t.Comment,
		"date":         t.Year,
		"genre":        t.Genre,
		"composer":     t.Composer,
		"copyright":    t.Copyright,
		"description":  t.Description,
		"synopsis":     t.LongDescription,
		"sort_name":    t.SortName,
		"sort_album":   t.SortAlbum,
		"sort_artist":  t.SortArtist,
	}
	var flags []string
	for k, v := range pairs {
		if v != "" {
			flags = append(flags, fmt.Sprintf("%s=%s", k, v))
		}
	}
	return flags
}

func FromProbeResult(r *ffmpeg.ProbeResult) AudioTag {
	tags := r.Format.Tags
	return AudioTag{
		Title:           tagVal(tags, "title"),
		Artist:          tagVal(tags, "artist"),
		Album:           tagVal(tags, "album"),
		AlbumArtist:     tagVal(tags, "album_artist"),
		Comment:         tagVal(tags, "comment"),
		Year:            tagVal(tags, "date"),
		Genre:           tagVal(tags, "genre"),
		Composer:        tagVal(tags, "composer"),
		Copyright:       tagVal(tags, "copyright"),
		Description:     tagVal(tags, "description"),
		LongDescription: tagVal(tags, "synopsis"),
		SortName:        tagVal(tags, "sort_name"),
		SortAlbum:       tagVal(tags, "sort_album"),
		SortArtist:      tagVal(tags, "sort_artist"),
	}
}

func tagVal(tags map[string]string, key string) string {
	if tags == nil {
		return ""
	}
	if v, ok := tags[key]; ok {
		return v
	}
	return tags[strings.ToUpper(key)]
}
