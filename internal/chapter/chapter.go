package chapter

import (
	"fmt"
	"time"

	"m4b/internal/ffmpeg"
)

type Chapter struct {
	Title string
	Start time.Duration
	End   time.Duration
}

type List []Chapter

func (l List) TotalDuration() time.Duration {
	if len(l) == 0 {
		return 0
	}
	return l[len(l)-1].End
}

// FromFFChapters converts ffprobe chapter data to a List.
// Uses StartTime/EndTime (seconds as float strings) for accuracy across all timebases.
func FromFFChapters(chs []ffmpeg.FFChapter) List {
	list := make(List, len(chs))
	for i, c := range chs {
		var startSecs, endSecs float64
		fmt.Sscanf(c.StartTime, "%f", &startSecs)
		fmt.Sscanf(c.EndTime, "%f", &endSecs)
		list[i] = Chapter{
			Title: c.Tags["title"],
			Start: time.Duration(startSecs * float64(time.Second)),
			End:   time.Duration(endSecs * float64(time.Second)),
		}
	}
	return list
}
