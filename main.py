import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from Images import (
    COMPRESSIBLE_IMAGE_INPUTS,
    CONVERTIBLE_IMAGE_INPUTS,
    SUPPORTED_IMAGE_OUTPUTS,
    compress_image,
    convert_image,
    ensure_image_support_for_path,
    file_size_text,
)
from Videos import SUPPORTED_VIDEO_INPUTS, SUPPORTED_VIDEO_OUTPUTS, compress_video, convert_video
from Videos import SUPPORTED_AUDIO_OUTPUTS, extract_audio


APP_TITLE = "Media Utility Desktop App"
IMAGE_MODE = "Image Work"
VIDEO_MODE = "Video Work"
IMAGE_INPUT = [
    ("Image files", "*.png *.jpg *.jpeg *.webp *.heic *.heif *.ico"),
    ("PNG images", "*.png"),
    ("JPEG images", "*.jpg *.jpeg"),
    ("WebP images", "*.webp"),
    ("HEIC images", "*.heic *.heif"),
    ("ICO images", "*.ico"),
    ("All files", "*.*"),
]
VIDEO_INPUT = [
    ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.mpeg *.mpg *.gif"),
    ("MP4 videos", "*.mp4"),
    ("MOV videos", "*.mov"),
    ("MKV videos", "*.mkv"),
    ("AVI videos", "*.avi"),
    ("WebM videos", "*.webm"),
    ("GIF files", "*.gif"),
    ("All files", "*.*"),
]
OUTPUT_FORMATS = ["JPG", "PNG", "WebP", "HEIC", "ICO"]
VIDEO_OUTPUT_FORMATS = ["MP4", "MOV", "MKV", "AVI", "WebM", "GIF"]
AUDIO_OUTPUT_FORMATS = ["MP3", "M4A", "OGG", "Opus", "WAV"]
CONVERSION_FORMAT_TEXT = "JPG, PNG, WebP, HEIC, or ICO"
COMPRESSION_FORMAT_TEXT = "JPG, PNG, or WebP"
VIDEO_FORMAT_TEXT = "MP4, MOV, MKV, AVI, WebM, MPEG, or GIF"
AUDIO_OUTPUT_FORMAT_TEXT = "MP3, M4A, OGG, Opus, or WAV"

# ------------------------- APP Window Start --------------------------------- #
class MediaUtilityApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("760x760")    # w,h ---------- general window size
        self.minsize(650,650)   # w,h ---------- minimum window size

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.input_path = ctk.StringVar()
        self.input_paths: list[Path] = []
        self.output_dir = ctk.StringVar(value=str(Path.cwd() / "output"))
        self.output_format = ctk.StringVar(value="JPG")
        self.media_mode = ctk.StringVar(value=IMAGE_MODE)
        self.image_tool = ctk.StringVar(value="Convert")
        self.conversion_mode = ctk.StringVar(value="Single File")
        self.quality = ctk.IntVar(value=90)
        self.status = ctk.StringVar(value=f"Choose a {CONVERSION_FORMAT_TEXT} image to begin.")

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="MediaPrime",
            font=ctk.CTkFont(size=30, weight="bold", family="Calibri"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Choose your type of media",
            text_color=("gray35", "gray72"),
            font=ctk.CTkFont(size=15),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.mode_tabs = ctk.CTkSegmentedButton(
            header,
            values=[IMAGE_MODE, VIDEO_MODE],
            command=self._mode_changed,
        )
        self.mode_tabs.set(IMAGE_MODE)
        self.mode_tabs.grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0))

        body = ctk.CTkFrame(self, corner_radius=8)
        body.grid(row=1, column=0, sticky="nsew", padx=28, pady=12)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        controls = ctk.CTkFrame(body, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        controls.grid_columnconfigure(0, weight=1)

        self._add_tool_picker(controls)
        self._add_conversion_mode_picker(controls)
        self._add_file_picker(controls)
        self._add_output_picker(controls)
        self._add_conversion_controls(controls)

        preview = ctk.CTkFrame(body, corner_radius=8)
        preview.grid(row=0, column=1, sticky="nsew", padx=(0, 22), pady=22)
        preview.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview,
            text="Preview Info",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 10))

        self.preview_text = ctk.CTkTextbox(preview, height=190, corner_radius=8)
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 16))
        preview.grid_rowconfigure(1, weight=1)
        self._set_preview("No file selected yet.")

        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 24))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(progress_frame)
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            progress_frame,
            textvariable=self.status,
            text_color=("gray35", "gray72"),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _add_tool_picker(self, parent: ctk.CTkFrame) -> None:
        self.tool_label = ctk.CTkLabel(parent, text="Image Tool", font=ctk.CTkFont(weight="bold"))
        self.tool_label.grid(
            row=0, column=0, sticky="w"
        )
        self.tool_tabs = ctk.CTkSegmentedButton(
            parent,
            values=["Convert", "Compress"],
            variable=self.image_tool,
            command=self._tool_changed,
        )
        self.tool_tabs.grid(row=1, column=0, sticky="ew", pady=(8, 18))

    def _add_conversion_mode_picker(self, parent: ctk.CTkFrame) -> None:
        self.mode_label = ctk.CTkLabel(
            parent,
            text="Conversion Mode",
            font=ctk.CTkFont(weight="bold"),
        )
        self.mode_label.grid(row=2, column=0, sticky="w")

        self.conversion_mode_tabs = ctk.CTkSegmentedButton(
            parent,
            values=["Single File", "Batch Files"],
            variable=self.conversion_mode,
            command=self._conversion_mode_changed,
        )
        self.conversion_mode_tabs.grid(row=3, column=0, sticky="ew", pady=(8, 18))

    def _add_file_picker(self, parent: ctk.CTkFrame) -> None:
        self.input_label = ctk.CTkLabel(
            parent,
            text="Input Image",
            font=ctk.CTkFont(weight="bold"),
        )
        self.input_label.grid(row=4, column=0, sticky="w")

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=5, column=0, sticky="ew", pady=(8, 18))
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(row, textvariable=self.input_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(row, text="Browse", width=108, command=self.pick_file).grid(
            row=0, column=1
        )

    def _add_output_picker(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Output Folder", font=ctk.CTkFont(weight="bold")).grid(
            row=6, column=0, sticky="w"
        )

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=7, column=0, sticky="ew", pady=(8, 18))
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(row, textvariable=self.output_dir).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(row, text="Choose", width=108, command=self.pick_output_dir).grid(
            row=0, column=1
        )

    def _add_conversion_controls(self, parent: ctk.CTkFrame) -> None:
        options = ctk.CTkFrame(parent, fg_color="transparent")
        options.grid(row=8, column=0, sticky="ew")
        options.grid_columnconfigure(0, weight=1)
        options.grid_columnconfigure(1, weight=1)

        self.format_label = ctk.CTkLabel(
            options,
            text="Output Format",
            font=ctk.CTkFont(weight="bold"),
        )
        self.format_label.grid(
            row=0, column=0, sticky="w"
        )
        self.format_menu = ctk.CTkOptionMenu(
            options,
            values=OUTPUT_FORMATS,
            variable=self.output_format,
            command=self._format_changed,
        )
        self.format_menu.grid(row=1, column=0, sticky="ew", pady=(8, 18), padx=(0, 10))

        ctk.CTkLabel(options, text="Quality", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, sticky="w"
        )
        self.quality_label = ctk.CTkLabel(options, text=f"{self.quality.get()}%")
        self.quality_label.grid(row=1, column=1, sticky="e", pady=(8, 0))

        slider = ctk.CTkSlider(
            options,
            from_=50,
            to=100,
            number_of_steps=50,
            command=self._quality_changed,
        )
        slider.set(self.quality.get())
        slider.grid(row=2, column=1, sticky="ew", pady=(0, 18))

        self.convert_button = ctk.CTkButton(
            parent,
            text=self._convert_button_text(),
            height=44,
            command=self.process_selected_image,
        )
        self.convert_button.grid(row=9, column=0, sticky="ew", pady=(10, 0))

    def _mode_changed(self, value: str) -> None:
        self.media_mode.set(value)
        self.progress.set(0)
        self._clear_selection()

        if value == VIDEO_MODE:
            self.output_format.set("MP4")
            self.tool_label.configure(text="Video Tool")
            self.tool_tabs.configure(values=["Convert", "Compress Video", "Extract Audio"])
            self.tool_tabs.set("Convert")
            self.image_tool.set("Convert")
            self.mode_label.configure(state="disabled")
            self.conversion_mode_tabs.configure(state="disabled")
            self.format_menu.configure(values=VIDEO_OUTPUT_FORMATS, state="normal")
            self.input_label.configure(text="Input Video")
            self.format_label.configure(text="Output Format")
            self.convert_button.configure(text=self._convert_button_text())
            self.status.set(f"Choose a {VIDEO_FORMAT_TEXT} file to convert.")
            return

        self.output_format.set("JPG")
        self.tool_label.configure(text="Image Tool")
        self.tool_tabs.configure(values=["Convert", "Compress"])
        self.tool_tabs.set("Convert")
        self.image_tool.set("Convert")
        self.mode_label.configure(state="normal")
        self.conversion_mode_tabs.configure(state="normal")
        self.format_menu.configure(values=OUTPUT_FORMATS, state="normal")
        self.input_label.configure(text="Input Image")
        self.format_label.configure(text="Output Format")
        self.convert_button.configure(text=self._convert_button_text())
        self.status.set(f"Choose a {CONVERSION_FORMAT_TEXT} image to convert.")

    def _quality_changed(self, value: float) -> None:
        quality = int(value)
        self.quality.set(quality)
        self.quality_label.configure(text=f"{quality}%")

    def _tool_changed(self, value: str) -> None:
        self.progress.set(0)
        self._clear_selection()
        if self.media_mode.get() == VIDEO_MODE:
            self.mode_label.configure(state="disabled")
            self.conversion_mode_tabs.configure(state="disabled")
            if value == "Compress Video":
                self.output_format.set("MP4")
                self.format_menu.configure(values=VIDEO_OUTPUT_FORMATS, state="normal")
                self.input_label.configure(text="Input Video")
                self.convert_button.configure(text="Compress Video")
                self.status.set(f"Choose a {VIDEO_FORMAT_TEXT} file to compress.")
            elif value == "Extract Audio":
                self.output_format.set("MP3")
                self.format_menu.configure(values=AUDIO_OUTPUT_FORMATS, state="normal")
                self.input_label.configure(text="Input Video")
                self.convert_button.configure(text="Extract Audio")
                self.status.set(f"Choose a {VIDEO_FORMAT_TEXT} file to extract audio from.")
            else:
                self.output_format.set("MP4")
                self.format_menu.configure(values=VIDEO_OUTPUT_FORMATS, state="normal")
                self.input_label.configure(text="Input Video")
                self.convert_button.configure(text=self._convert_button_text())
                self.status.set(f"Choose a {VIDEO_FORMAT_TEXT} file to convert.")
            return

        if value == "Compress":
            self.conversion_mode.set("Single File")
            self.mode_label.configure(state="disabled")
            self.conversion_mode_tabs.configure(state="disabled")
            self.input_label.configure(text="Input Image")
            self.format_label.configure(text="Output Format")
            self.format_menu.configure(state="disabled")
            self.convert_button.configure(text="Compress Image")
            self.status.set(f"Choose a {COMPRESSION_FORMAT_TEXT} image to compress.")
        else:
            self.mode_label.configure(state="normal")
            self.conversion_mode_tabs.configure(state="normal")
            self.input_label.configure(text="Input Image")
            self.format_menu.configure(state="normal")
            self.convert_button.configure(text=self._convert_button_text())
            self.status.set(f"Choose a {CONVERSION_FORMAT_TEXT} image to convert.")

    def _conversion_mode_changed(self, value: str) -> None:
        if self.media_mode.get() == VIDEO_MODE:
            return

        self.progress.set(0)
        self._clear_selection()
        if value == "Batch Files":
            self.input_label.configure(text="Input Images")
            self.status.set(f"Choose multiple {CONVERSION_FORMAT_TEXT} images to convert.")
        else:
            self.input_label.configure(text="Input Image")
            self.status.set(f"Choose a {CONVERSION_FORMAT_TEXT} image to convert.")

    def _format_changed(self, _value: str) -> None:
        if self.media_mode.get() == VIDEO_MODE and self.image_tool.get() in {"Compress Video", "Extract Audio"}:
            return

        if self.image_tool.get() == "Convert":
            self.convert_button.configure(text=self._convert_button_text())

    def _convert_button_text(self) -> str:
        return f"Convert to {self.output_format.get()}"

    def pick_file(self) -> None:
        if self.media_mode.get() == VIDEO_MODE:
            tool = self.image_tool.get()
            is_extract_audio = tool == "Extract Audio"
            is_video_compression = tool == "Compress Video"
            if is_extract_audio:
                title = "Select video to extract audio"
            elif is_video_compression:
                title = "Select video to compress"
            else:
                title = "Select video to convert"
            filetypes = VIDEO_INPUT
            path = filedialog.askopenfilename(title=title, filetypes=filetypes)
            if not path:
                return

            self.input_paths = [Path(path)]
            self.input_path.set(str(self.input_paths[0]))
            if is_extract_audio:
                self.status.set(f"Video selected. Ready to extract {self.output_format.get()} audio.")
            elif is_video_compression:
                self.status.set(f"Video selected. Ready to compress to {self.output_format.get()}.")
            else:
                self.status.set(f"Video selected. Ready to convert to {self.output_format.get()}.")
            self.progress.set(0)
            self._update_audio_video_preview(self.input_paths[0], "Video")
            return

        if self.image_tool.get() == "Compress":
            title = "Select image to compress"
            paths = filedialog.askopenfilename(title=title, filetypes=IMAGE_INPUT)
        else:
            if self.conversion_mode.get() == "Batch Files":
                title = "Select images to convert"
                paths = filedialog.askopenfilenames(title=title, filetypes=IMAGE_INPUT)
            else:
                title = "Select image to convert"
                paths = filedialog.askopenfilename(title=title, filetypes=IMAGE_INPUT)

        if not paths:
            return

        if isinstance(paths, tuple):
            self.input_paths = [Path(path) for path in paths]
        else:
            self.input_paths = [Path(paths)]

        self.input_path.set(self._input_display_text())
        if self.image_tool.get() == "Compress":
            self.status.set("Image selected. Ready to compress.")
        elif self.conversion_mode.get() == "Batch Files":
            self.status.set(f"{len(self.input_paths)} images selected. Ready to convert to {self.output_format.get()}.")
        else:
            self.status.set(f"Image selected. Ready to convert to {self.output_format.get()}.")
        self.progress.set(0)
        if len(self.input_paths) == 1:
            self._update_preview(self.input_paths[0])
        else:
            self._update_batch_preview(self.input_paths)

    def pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir.set(path)

    def process_selected_image(self) -> None:
        if self.media_mode.get() == VIDEO_MODE:
            self.process_selected_video()
            return

        input_paths = self.input_paths or [Path(self.input_path.get().strip())]
        output_dir = Path(self.output_dir.get().strip())
        tool = self.image_tool.get()
        output_format = self.output_format.get().lower()
        is_batch = tool == "Convert" and self.conversion_mode.get() == "Batch Files"

        if not input_paths or not str(input_paths[0]).strip():
            messagebox.showerror("Missing file", "Please choose image files first.")
            return

        missing_paths = [path for path in input_paths if not path.exists()]
        if missing_paths:
            messagebox.showerror("Missing file", f"Could not find: {missing_paths[0]}")
            return

        unsupported_paths = [
            path for path in input_paths
            if path.suffix.lower() not in CONVERTIBLE_IMAGE_INPUTS
        ]
        if tool == "Convert" and unsupported_paths:
            messagebox.showerror(
                "Unsupported file",
                f"Conversion supports {CONVERSION_FORMAT_TEXT} images.\n\nFirst unsupported file:\n{unsupported_paths[0]}",
            )
            return

        if tool == "Convert" and output_format not in SUPPORTED_IMAGE_OUTPUTS:
            messagebox.showerror("Unsupported format", f"Choose {CONVERSION_FORMAT_TEXT} as the output format.")
            return

        if tool == "Compress" and input_paths[0].suffix.lower() not in COMPRESSIBLE_IMAGE_INPUTS:
            messagebox.showerror("Unsupported file", f"Compression supports {COMPRESSION_FORMAT_TEXT} images.")
            return

        busy_text = "Compressing..." if tool == "Compress" else "Converting..."
        self.convert_button.configure(state="disabled", text=busy_text)
        if is_batch:
            self.status.set(f"Converting 0 of {len(input_paths)} images...")
            self.progress.set(0)
        else:
            self.status.set("Compressing image..." if tool == "Compress" else "Converting image...")
            self.progress.set(0.35)

        thread = threading.Thread(
            target=self._image_worker,
            args=(tool, input_paths, output_dir, output_format, self.quality.get()),
            daemon=True,
        )
        thread.start()

    def _image_worker(
        self,
        tool: str,
        input_paths: list[Path],
        output_dir: Path,
        output_format: str,
        quality: int,
    ) -> None:
        if tool == "Compress":
            try:
                output_path = compress_image(input_paths[0], output_dir=output_dir, quality=quality)
            except Exception as exc:
                self.after(0, self._conversion_failed, str(exc))
                return

            self.after(0, self._conversion_finished, tool, input_paths[0], output_path)
            return

        results: list[Path] = []
        failures: list[tuple[Path, str]] = []
        total = len(input_paths)

        for index, input_path in enumerate(input_paths, start=1):
            try:
                output_path = convert_image(
                    input_path,
                    output_dir=output_dir,
                    output_format=output_format,
                    quality=quality,
                )
                results.append(output_path)
            except Exception as exc:
                failures.append((input_path, str(exc)))

            self.after(0, self._batch_progress, index, total)

        if total == 1:
            if failures:
                self.after(0, self._conversion_failed, failures[0][1])
            else:
                self.after(0, self._conversion_finished, tool, input_paths[0], results[0])
            return

        self.after(0, self._batch_finished, results, failures)

    def _batch_progress(self, completed: int, total: int) -> None:
        self.progress.set(completed / total)
        self.status.set(f"Converting {completed} of {total} images...")

    def _batch_finished(self, results: list[Path], failures: list[tuple[Path, str]]) -> None:
        self.progress.set(1 if results else 0)
        self.convert_button.configure(state="normal", text=self._convert_button_text())

        summary_lines = [
            "Batch conversion complete.",
            "",
            f"Converted: {len(results)}",
            f"Failed: {len(failures)}",
        ]

        if results:
            summary_lines.extend(["", "Outputs:"])
            summary_lines.extend(str(path) for path in results[:8])
            if len(results) > 8:
                summary_lines.append(f"...and {len(results) - 8} more")

        if failures:
            summary_lines.extend(["", "Failures:"])
            summary_lines.extend(f"{path.name}: {error}" for path, error in failures[:5])
            if len(failures) > 5:
                summary_lines.append(f"...and {len(failures) - 5} more")

        summary = "\n".join(summary_lines)
        self._set_preview(summary)
        self.status.set(f"Batch finished: {len(results)} converted, {len(failures)} failed.")

        if failures:
            messagebox.showwarning("Batch finished with errors", summary)
        else:
            messagebox.showinfo("Success", summary)

    def _conversion_finished(self, tool: str, input_path: Path, output_path: Path) -> None:
        self.progress.set(1)
        self.status.set(f"Saved: {output_path}")
        button_text = "Compress Image" if tool == "Compress" else self._convert_button_text()
        self.convert_button.configure(state="normal", text=button_text)

        if tool == "Compress":
            original_size = file_size_text(input_path)
            compressed_size = file_size_text(output_path)
            self._set_preview(
                "Compression complete.\n\n"
                f"Original: {original_size}\n"
                f"Compressed: {compressed_size}\n\n"
                f"Output:\n{output_path}"
            )
            message = f"Image compressed successfully:\n{output_path}"
        else:
            self._set_preview(f"Conversion complete.\n\nOutput:\n{output_path}")
            message = f"Image converted successfully:\n{output_path}"

        messagebox.showinfo("Success", message)

    def _conversion_failed(self, error: str) -> None:
        self.progress.set(0)
        self.status.set("Conversion failed.")
        if self.image_tool.get() == "Compress":
            button_text = "Compress Image"
        elif self.image_tool.get() == "Compress Video":
            button_text = "Compress Video"
        elif self.image_tool.get() == "Extract Audio":
            button_text = "Extract Audio"
        else:
            button_text = self._convert_button_text()
        self.convert_button.configure(state="normal", text=button_text)
        messagebox.showerror("Processing failed", error)

    def process_selected_video(self) -> None:
        if self.image_tool.get() == "Compress Video":
            self.compress_selected_video()
            return

        if self.image_tool.get() == "Extract Audio":
            self.extract_selected_audio()
            return

        input_path = self.input_paths[0] if self.input_paths else Path(self.input_path.get().strip())
        output_dir = Path(self.output_dir.get().strip())
        output_format = self.output_format.get().lower()

        if not str(input_path).strip() or not input_path.exists():
            messagebox.showerror("Missing file", "Please choose a video first.")
            return

        if input_path.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
            messagebox.showerror("Unsupported file", f"Video conversion supports {VIDEO_FORMAT_TEXT} files.")
            return

        if output_format not in SUPPORTED_VIDEO_OUTPUTS:
            messagebox.showerror("Unsupported format", "Choose MP4, MOV, MKV, AVI, WebM, or GIF as the output format.")
            return

        self.convert_button.configure(state="disabled", text="Converting...")
        self.status.set("Converting video with FFmpeg...")
        self.progress.set(0.35)

        thread = threading.Thread(
            target=self._video_worker,
            args=(input_path, output_dir, output_format, self.quality.get()),
            daemon=True,
        )
        thread.start()

    def _video_worker(self, input_path: Path, output_dir: Path, output_format: str, quality: int) -> None:
        try:
            output_path = convert_video(
                input_path,
                output_dir=output_dir,
                output_format=output_format,
                quality=quality,
            )
        except Exception as exc:
            self.after(0, self._conversion_failed, str(exc))
            return

        self.after(0, self._video_conversion_finished, input_path, output_path)

    def _video_conversion_finished(self, input_path: Path, output_path: Path) -> None:
        self.progress.set(1)
        self.status.set(f"Saved: {output_path}")
        self.convert_button.configure(state="normal", text=self._convert_button_text())
        self._set_preview(
            "Video conversion complete.\n\n"
            f"Original: {file_size_text(input_path)}\n"
            f"Converted: {file_size_text(output_path)}\n\n"
            f"Output:\n{output_path}"
        )
        messagebox.showinfo("Success", f"Video converted successfully:\n{output_path}")

    def compress_selected_video(self) -> None:
        input_path = self.input_paths[0] if self.input_paths else Path(self.input_path.get().strip())
        output_dir = Path(self.output_dir.get().strip())
        output_format = self.output_format.get().lower()

        if not str(input_path).strip() or not input_path.exists():
            messagebox.showerror("Missing file", "Please choose a video first.")
            return

        if input_path.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
            messagebox.showerror("Unsupported file", f"Video compression supports {VIDEO_FORMAT_TEXT} files.")
            return

        if output_format not in SUPPORTED_VIDEO_OUTPUTS:
            messagebox.showerror("Unsupported format", "Choose MP4, MOV, MKV, AVI, WebM, or GIF as the output format.")
            return

        self.convert_button.configure(state="disabled", text="Compressing...")
        self.status.set("Compressing video with FFmpeg...")
        self.progress.set(0.35)

        thread = threading.Thread(
            target=self._video_compression_worker,
            args=(input_path, output_dir, output_format, self.quality.get()),
            daemon=True,
        )
        thread.start()

    def _video_compression_worker(self, input_path: Path, output_dir: Path, output_format: str, quality: int) -> None:
        try:
            output_path = compress_video(
                input_path,
                output_dir=output_dir,
                output_format=output_format,
                quality=quality,
            )
        except Exception as exc:
            self.after(0, self._conversion_failed, str(exc))
            return

        self.after(0, self._video_compression_finished, input_path, output_path)

    def _video_compression_finished(self, input_path: Path, output_path: Path) -> None:
        self.progress.set(1)
        self.status.set(f"Saved: {output_path}")
        self.convert_button.configure(state="normal", text="Compress Video")
        self._set_preview(
            "Video compression complete.\n\n"
            f"Original: {file_size_text(input_path)}\n"
            f"Compressed: {file_size_text(output_path)}\n\n"
            f"Output:\n{output_path}"
        )
        messagebox.showinfo("Success", f"Video compressed successfully:\n{output_path}")

    def extract_selected_audio(self) -> None:
        input_path = self.input_paths[0] if self.input_paths else Path(self.input_path.get().strip())
        output_dir = Path(self.output_dir.get().strip())
        output_format = self.output_format.get().lower()

        if not str(input_path).strip() or not input_path.exists():
            messagebox.showerror("Missing file", "Please choose a video first.")
            return

        if input_path.suffix.lower() not in SUPPORTED_VIDEO_INPUTS:
            messagebox.showerror("Unsupported file", f"Audio extraction supports {VIDEO_FORMAT_TEXT} files.")
            return

        if output_format not in SUPPORTED_AUDIO_OUTPUTS:
            messagebox.showerror("Unsupported format", f"Choose {AUDIO_OUTPUT_FORMAT_TEXT} as the output format.")
            return

        self.convert_button.configure(state="disabled", text="Extracting...")
        self.status.set("Extracting audio with FFmpeg...")
        self.progress.set(0.35)

        thread = threading.Thread(
            target=self._audio_extraction_worker,
            args=(input_path, output_dir, output_format, self.quality.get()),
            daemon=True,
        )
        thread.start()

    def _audio_extraction_worker(self, input_path: Path, output_dir: Path, output_format: str, quality: int) -> None:
        try:
            output_path = extract_audio(
                input_path,
                output_dir=output_dir,
                output_format=output_format,
                quality=quality,
            )
        except Exception as exc:
            self.after(0, self._conversion_failed, str(exc))
            return

        self.after(0, self._audio_extraction_finished, input_path, output_path)

    def _audio_extraction_finished(self, input_path: Path, output_path: Path) -> None:
        self.progress.set(1)
        self.status.set(f"Saved: {output_path}")
        self.convert_button.configure(state="normal", text="Extract Audio")
        self._set_preview(
            "Audio extraction complete.\n\n"
            f"Video: {file_size_text(input_path)}\n"
            f"Audio: {file_size_text(output_path)}\n\n"
            f"Output:\n{output_path}"
        )
        messagebox.showinfo("Success", f"Audio extracted successfully:\n{output_path}")

    def _update_preview(self, path: Path) -> None:
        try:
            from PIL import Image

            ensure_image_support_for_path(path)
            with Image.open(path) as image:
                details = [
                    f"Name: {path.name}",
                    f"Format: {image.format}",
                    f"Size: {image.width} x {image.height}px",
                    f"Mode: {image.mode}",
                    f"File size: {file_size_text(path)}",
                    f"Input: {path}",
                ]
        except Exception as exc:
            details = [f"Could not read image details.", str(exc)]

        self._set_preview("\n".join(details))

    def _update_audio_video_preview(self, path: Path, media_type: str) -> None:
        details = [
            f"Name: {path.name}",
            f"Type: {path.suffix.upper().lstrip('.') or media_type}",
            f"File size: {file_size_text(path)}",
            f"Input: {path}",
        ]
        self._set_preview("\n".join(details))

    def _set_preview(self, text: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def _update_batch_preview(self, paths: list[Path]) -> None:
        lines = [f"{len(paths)} images selected.", "", "Files:"]
        lines.extend(str(path) for path in paths[:12])
        if len(paths) > 12:
            lines.append(f"...and {len(paths) - 12} more")
        self._set_preview("\n".join(lines))

    def _input_display_text(self) -> str:
        if len(self.input_paths) == 1:
            return str(self.input_paths[0])
        return f"{len(self.input_paths)} files selected"

    def _clear_selection(self) -> None:
        self.input_paths = []
        self.input_path.set("")
        self._set_preview("No file selected yet.")


def main() -> None:
    app = MediaUtilityApp()
    app.mainloop()


if __name__ == "__main__":
    main()
