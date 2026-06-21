package chapter

import (
	"bufio"
	"fmt"
	"io"
	"strings"
	"time"
)

func ParseTxt(r io.Reader) (List, error) {
	var list List
	scanner := bufio.NewScanner(r)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		idx := strings.Index(line, " ")
		if idx < 0 {
			return nil, fmt.Errorf("invalid chapters.txt line (no space after timestamp): %q", line)
		}
		d, err := parseDuration(line[:idx])
		if err != nil {
			return nil, err
		}
		list = append(list, Chapter{Title: strings.TrimSpace(line[idx+1:]), Start: d})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	for i := range list {
		if i+1 < len(list) {
			list[i].End = list[i+1].Start
		}
	}
	return list, nil
}

// parseDuration parses HH:MM:SS.mmm or HH:MM:SS
func parseDuration(s string) (time.Duration, error) {
	var h, m, sec, ms int
	if n, _ := fmt.Sscanf(s, "%d:%d:%d.%d", &h, &m, &sec, &ms); n == 4 {
		return time.Duration(h)*time.Hour + time.Duration(m)*time.Minute +
			time.Duration(sec)*time.Second + time.Duration(ms)*time.Millisecond, nil
	}
	if n, _ := fmt.Sscanf(s, "%d:%d:%d", &h, &m, &sec); n == 3 {
		return time.Duration(h)*time.Hour + time.Duration(m)*time.Minute +
			time.Duration(sec)*time.Second, nil
	}
	return 0, fmt.Errorf("cannot parse %q as HH:MM:SS[.mmm]", s)
}
