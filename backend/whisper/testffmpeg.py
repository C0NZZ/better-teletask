import ffmpeg

(
            ffmpeg.input("https://www10-fms.hpi.uni-potsdam.de/vod/media/SS_2025/KISZ_2025/KISZ_2025_09_25/sd/video.mp4")
            .output(
                "test.mp3",
                format='mp3',
                acodec='libmp3lame',
                **{"q:a": 2},
                vn=None
            )
            .overwrite_output()
            .global_args('-hide_banner', '-loglevel', 'error')
            .run(capture_stdout=True, capture_stderr=True)
        )