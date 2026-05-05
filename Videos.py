import shutil
import subprocess
from pathlib import Path


SUPPORTED_VIDEO_INPUTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg", ".gif"}
SUPPORTED_VIDEO_OUTPUTS = {"mp4", "mov", "mkv", "avi", "webm", "gif"}
SUPPORTED_AUDIO_OUTPUTS = {"mp3", "m4a", "ogg", "opus", "wav"}


def convert_video(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    output_format: str = "mp4",
    quality: int = 85,
) -> Path:
    """Convert one video to the requested output format using FFmpeg."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH.")

    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input video does not exist: {source}")

    if source.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
        raise ValueError("Video conversion supports MP4, MOV, MKV, AVI, WebM, MPEG, and GIF files.")

    normalized_format = output_format.lower().lstrip(".")
    if normalized_format not in SUPPORTED_VIDEO_OUTPUTS:
        raise ValueError(f"Unsupported video output format: {output_format}")

    destination_dir = Path(output_dir) if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _available_destination(source, destination_dir, normalized_format)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        *_codec_options(normalized_format, quality),
        str(destination),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "FFmpeg conversion failed."
        raise RuntimeError(error.splitlines()[-1])

    return destination


def compress_video(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    output_format: str | None = None,
    quality: int = 70,
) -> Path:
    """Compress one video using FFmpeg."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH.")

    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input video does not exist: {source}")

    if source.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
        raise ValueError("Video compression supports MP4, MOV, MKV, AVI, WebM, MPEG, and GIF files.")

    normalized_format = (output_format or source.suffix).lower().lstrip(".")
    if normalized_format == "mpg":
        normalized_format = "mpeg"
    if normalized_format not in SUPPORTED_VIDEO_OUTPUTS:
        raise ValueError(f"Unsupported video output format: {output_format}")

    destination_dir = Path(output_dir) if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _available_destination(source, destination_dir, normalized_format, stem_suffix="_compressed")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        *_compression_codec_options(normalized_format, quality),
        str(destination),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "FFmpeg video compression failed."
        raise RuntimeError(error.splitlines()[-1])

    return destination


def extract_audio(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    output_format: str = "mp3",
    quality: int = 85,
) -> Path:
    """Extract audio from one video file using FFmpeg."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg was not found. Install FFmpeg and add it to PATH.")

    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input video does not exist: {source}")

    if source.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
        raise ValueError("Audio extraction supports MP4, MOV, MKV, AVI, WebM, MPEG, and GIF files.")

    normalized_format = output_format.lower().lstrip(".")
    if normalized_format not in SUPPORTED_AUDIO_OUTPUTS:
        raise ValueError(f"Unsupported audio output format: {output_format}")

    destination_dir = Path(output_dir) if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _available_destination(source, destination_dir, normalized_format)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        *_audio_codec_options(normalized_format, quality),
        str(destination),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "FFmpeg audio extraction failed."
        raise RuntimeError(error.splitlines()[-1])

    return destination


def trim_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def _video_tools_not_ready() -> None:
    raise NotImplementedError("This video tool is planned for a later phase.")


def _available_destination(
    source: Path,
    destination_dir: Path,
    output_format: str,
    stem_suffix: str = "",
) -> Path:
    destination = destination_dir / f"{source.stem}{stem_suffix}.{output_format}"
    if destination.resolve() == source.resolve():
        destination = destination_dir / f"{source.stem}_converted.{output_format}"

    if not destination.exists():
        return destination

    base_stem = destination.stem
    suffix = destination.suffix
    counter = 1
    while True:
        candidate = destination_dir / f"{base_stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _codec_options(output_format: str, quality: int) -> list[str]:
    bounded_quality = max(1, min(int(quality), 100))
    crf = round(35 - (bounded_quality / 100 * 17))

    if output_format in {"mp4", "mov", "mkv"}:
        return ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-c:a", "aac", "-b:a", "160k"]

    if output_format == "webm":
        return ["-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0", "-c:a", "libopus", "-b:a", "128k"]

    if output_format == "avi":
        return ["-c:v", "mpeg4", "-q:v", str(max(2, round(31 - (bounded_quality / 100 * 26)))), "-c:a", "libmp3lame"]

    if output_format == "gif":
        return ["-vf", "fps=12,scale=640:-1:flags=lanczos", "-loop", "0"]

    return []


def _compression_codec_options(output_format: str, quality: int) -> list[str]:
    bounded_quality = max(1, min(int(quality), 100))
    crf = round(38 - (bounded_quality / 100 * 16))
    audio_bitrate = _audio_bitrate(max(30, bounded_quality - 15))

    if output_format in {"mp4", "mov", "mkv"}:
        return [
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-preset",
            "slow",
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            "-movflags",
            "+faststart",
        ]

    if output_format == "webm":
        return [
            "-c:v",
            "libvpx-vp9",
            "-crf",
            str(crf),
            "-b:v",
            "0",
            "-c:a",
            "libopus",
            "-b:a",
            audio_bitrate,
        ]

    if output_format == "avi":
        return [
            "-c:v",
            "mpeg4",
            "-q:v",
            str(max(4, round(35 - (bounded_quality / 100 * 25)))),
            "-c:a",
            "libmp3lame",
            "-b:a",
            audio_bitrate,
        ]

    if output_format == "gif":
        return ["-vf", "fps=10,scale=480:-1:flags=lanczos", "-loop", "0"]

    return []


def _audio_codec_options(output_format: str, quality: int) -> list[str]:
    bounded_quality = max(1, min(int(quality), 100))
    bitrate = _audio_bitrate(bounded_quality)

    if output_format == "mp3":
        return ["-c:a", "libmp3lame", "-b:a", bitrate]

    if output_format == "m4a":
        return ["-c:a", "aac", "-b:a", bitrate]

    if output_format == "ogg":
        return ["-c:a", "libvorbis", "-b:a", bitrate]

    if output_format == "opus":
        return ["-c:a", "libopus", "-b:a", bitrate]

    if output_format == "wav":
        return ["-c:a", "pcm_s16le"]

    return []


def _audio_bitrate(quality: int) -> str:
    if quality >= 90:
        return "192k"
    if quality >= 75:
        return "160k"
    if quality >= 60:
        return "128k"
    if quality >= 40:
        return "96k"
    return "64k"
