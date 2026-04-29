from pathlib import Path


def _video_tools_not_ready() -> None:
    raise NotImplementedError("Video tools are planned for a later phase and require FFmpeg.")


def convert_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def compress_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def extract_audio(*args, **kwargs) -> Path:
    _video_tools_not_ready()


def trim_video(*args, **kwargs) -> Path:
    _video_tools_not_ready()
