package cmd

import (
	"github.com/spf13/cobra"
	"m4b/internal/convert"
)

var convertCmd = &cobra.Command{
	Use:   "convert <input-dir>",
	Short: "Convert a directory of audio files to another format",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		f := cmd.Flags()
		outDir, _ := f.GetString("output-dir")
		format, _ := f.GetString("audio-format")
		bitrate, _ := f.GetString("audio-bitrate")
		return convert.Run(convert.Options{
			InputDir:  args[0],
			OutputDir: outDir,
			Format:    format,
			Bitrate:   bitrate,
		})
	},
}

func init() {
	f := convertCmd.Flags()
	f.StringP("output-dir", "o", "", "output directory (required)")
	f.String("audio-format", "mp3", "output format: mp3, m4b, m4a")
	f.String("audio-bitrate", "", "output bitrate (defaults to 128k for mp3, 64k for aac)")
	convertCmd.MarkFlagRequired("output-dir")
	rootCmd.AddCommand(convertCmd)
}
