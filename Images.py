from pathlib import Path
from typing import Iterable

from PIL import Image


SUPPORTED_IMAGE_OUTPUTS = {"jpg", "jpeg", "png", "webp", "heic", "heif", "ico"}
CONVERTIBLE_IMAGE_INPUTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".ico"}
COMPRESSIBLE_IMAGE_INPUTS = {".jpg", ".jpeg", ".png", ".webp"}
HEIC_FORMATS = {"heic", "heif"}


def _register_heif_support() -> None:
    try:
        from pillow_heif import register_heif_opener
    except ImportError as exc:
        raise ImportError(
            "HEIC/HEIF support requires pillow-heif. Install dependencies with: "
            "pip install -r requirements.txt"
        ) from exc

    register_heif_opener()


def ensure_image_support_for_path(path: str | Path) -> None:
    """Register optional image plugins needed for this file."""
    if Path(path).suffix.lower() in {".heic", ".heif"}:
        _register_heif_support()


def convert_image(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    output_format: str = "jpg",
    quality: int = 90,
) -> Path:
    """Convert one image to the requested output format."""
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input image does not exist: {source}")

    normalized_format = output_format.lower().lstrip(".")
    if normalized_format == "jpeg":
        normalized_format = "jpg"
    if normalized_format == "heif":
        normalized_format = "heic"

    if normalized_format not in SUPPORTED_IMAGE_OUTPUTS:
        raise ValueError(f"Unsupported output format: {output_format}")

    ensure_image_support_for_path(source)
    if normalized_format in HEIC_FORMATS:
        _register_heif_support()

    destination_dir = Path(output_dir) if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _available_destination(source, destination_dir, normalized_format)

    with Image.open(source) as image:
        image_to_save = _prepare_for_format(image, normalized_format)
        save_kwargs = _save_options(normalized_format, quality)
        image_to_save.save(destination, **save_kwargs)

    return destination


def compress_image(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    quality: int = 80,
) -> Path:
    """Compress an image while keeping its current format when possible."""
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input image does not exist: {source}")

    if source.suffix.lower() not in COMPRESSIBLE_IMAGE_INPUTS:
        raise ValueError("Compression supports JPG, PNG, and WebP images.")

    output_format = source.suffix.lower().lstrip(".")
    if output_format == "jpeg":
        output_format = "jpg"

    destination_dir = Path(output_dir) if output_dir else source.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{source.stem}_compressed.{output_format}"

    with Image.open(source) as image:
        prepared = _prepare_for_format(image, output_format)
        prepared.save(destination, **_save_options(output_format, quality))

    return destination


def file_size_text(path: str | Path) -> str:
    """Return a compact display string for a file size."""
    size = Path(path).stat().st_size
    units = ["B", "KB", "MB", "GB"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024


def resize_image(
    input_path: str | Path,
    output_path: str | Path,
    width: int,
    height: int,
    keep_aspect: bool = True,
) -> Path:
    """Resize an image and save it to output_path."""
    source = Path(input_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ensure_image_support_for_path(source)

    with Image.open(source) as image:
        if keep_aspect:
            resized = image.copy()
            resized.thumbnail((width, height))
        else:
            resized = image.resize((width, height))

        output_format = destination.suffix.lower().lstrip(".") or image.format.lower()
        prepared = _prepare_for_format(resized, output_format)
        prepared.save(destination, **_save_options(output_format, 90))

    return destination


def batch_process(
    input_paths: Iterable[str | Path],
    output_dir: str | Path,
    output_format: str = "jpg",
    quality: int = 90,
) -> list[Path]:
    """Convert a group of images to one output folder."""
    return [
        convert_image(path, output_dir=output_dir, output_format=output_format, quality=quality)
        for path in input_paths
    ]


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


def _prepare_for_format(image: Image.Image, output_format: str) -> Image.Image:
    if output_format in {"jpg", "jpeg"} and image.mode in {"RGBA", "LA", "P"}:
        background = Image.new("RGB", image.size, "white")
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.getchannel("A") if image.mode in {"RGBA", "LA"} else None)
        return background

    if output_format in {"jpg", "jpeg"}:
        return image.convert("RGB")

    if output_format in HEIC_FORMATS and image.mode == "P":
        return image.convert("RGBA")

    if output_format == "ico" and image.mode not in {"RGB", "RGBA"}:
        return image.convert("RGBA")

    return image.copy()


def _save_options(output_format: str, quality: int) -> dict[str, object]:
    bounded_quality = max(1, min(int(quality), 100))

    if output_format in {"jpg", "jpeg"}:
        return {"format": "JPEG", "quality": bounded_quality, "optimize": True}

    if output_format == "webp":
        return {"format": "WEBP", "quality": bounded_quality, "method": 6}

    if output_format == "png":
        return {"format": "PNG", "optimize": True}

    if output_format in HEIC_FORMATS:
        return {"format": "HEIF", "quality": bounded_quality}

    if output_format == "ico":
        return {"format": "ICO"}

    return {}
