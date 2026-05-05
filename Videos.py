import shutil
import subprocess
from pathlib import Path


SUPPORTED_VIDEO_INPUTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg", ".gif"}
SUPPORTED_VIDEO_OUTPUTS = {"mp4", "mov", "mkv", "avi", "webm", "gif"}


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


def compress_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def extract_audio(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def trim_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def _video_tools_not_ready() -> None:
    raise NotImplementedError("This video tool is planned for a later phase.")


def _available_destination(source: Path, destination_dir: Path, output_format: str) -> Path:
    destination = destination_dir / f"{source.stem}.{output_format}"
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
