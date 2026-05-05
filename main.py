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


APP_TITLE = "Media Utility Desktop App"
IMAGE_INPUT = [
    ("Image files", "*.png *.jpg *.jpeg *.webp *.heic *.heif *.ico"),
    ("PNG images", "*.png"),
    ("JPEG images", "*.jpg *.jpeg"),
    ("WebP images", "*.webp"),
    ("HEIC images", "*.heic *.heif"),
    ("ICO images", "*.ico"),
    ("All files", "*.*"),
]
OUTPUT_FORMATS = ["JPG", "PNG", "WebP", "HEIC", "ICO"]
CONVERSION_FORMAT_TEXT = "JPG, PNG, WebP, HEIC, or ICO"
COMPRESSION_FORMAT_TEXT = "JPG, PNG, or WebP"


class MediaUtilityApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("700x660")    # w,h
        self.minsize(650, 300)   # w,h

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.input_path = ctk.StringVar()
        self.output_dir = ctk.StringVar(value=str(Path.cwd() / "output"))
        self.output_format = ctk.StringVar(value="JPG")
        self.image_tool = ctk.StringVar(value="Convert")
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
            text="MediaPrime: Media Utility App",
            font=ctk.CTkFont(size=30, weight="bold"),
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
            values=["Image Work", "Video Work"],
            command=self._mode_changed,
        )
        self.mode_tabs.set("Image Work")
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
        ctk.CTkLabel(parent, text="Image Tool", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.tool_tabs = ctk.CTkSegmentedButton(
            parent,
            values=["Convert", "Compress"],
            variable=self.image_tool,
            command=self._tool_changed,
        )
        self.tool_tabs.grid(row=1, column=0, sticky="ew", pady=(8, 18))

    def _add_file_picker(self, parent: ctk.CTkFrame) -> None:
        self.input_label = ctk.CTkLabel(
            parent,
            text="Input Image",
            font=ctk.CTkFont(weight="bold"),
        )
        self.input_label.grid(row=2, column=0, sticky="w")

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=3, column=0, sticky="ew", pady=(8, 18))
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(row, textvariable=self.input_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(row, text="Browse", width=108, command=self.pick_file).grid(
            row=0, column=1
        )

    def _add_output_picker(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Output Folder", font=ctk.CTkFont(weight="bold")).grid(
            row=4, column=0, sticky="w"
        )

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=5, column=0, sticky="ew", pady=(8, 18))
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(row, textvariable=self.output_dir).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ctk.CTkButton(row, text="Choose", width=108, command=self.pick_output_dir).grid(
            row=0, column=1
        )

    def _add_conversion_controls(self, parent: ctk.CTkFrame) -> None:
        options = ctk.CTkFrame(parent, fg_color="transparent")
        options.grid(row=6, column=0, sticky="ew")
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
        self.convert_button.grid(row=7, column=0, sticky="ew", pady=(10, 0))

    def _mode_changed(self, value: str) -> None:
        if value == "Video Work":
            self.mode_tabs.set("Image Work")
            messagebox.showinfo(
                "Coming soon",
                "Video tools are planned next. Image conversion and compression are available now.",
            )

    def _quality_changed(self, value: float) -> None:
        quality = int(value)
        self.quality.set(quality)
        self.quality_label.configure(text=f"{quality}%")

    def _tool_changed(self, value: str) -> None:
        self.progress.set(0)
        if value == "Compress":
            self.input_label.configure(text="Input Image")
            self.format_label.configure(text="Output Format")
            self.format_menu.configure(state="disabled")
            self.convert_button.configure(text="Compress Image")
            self.status.set(f"Choose a {COMPRESSION_FORMAT_TEXT} image to compress.")
        else:
            self.input_label.configure(text="Input Image")
            self.format_menu.configure(state="normal")
            self.convert_button.configure(text=self._convert_button_text())
            self.status.set(f"Choose a {CONVERSION_FORMAT_TEXT} image to convert.")

    def _format_changed(self, _value: str) -> None:
        if self.image_tool.get() == "Convert":
            self.convert_button.configure(text=self._convert_button_text())

    def _convert_button_text(self) -> str:
        return f"Convert to {self.output_format.get()}"

    def pick_file(self) -> None:
        if self.image_tool.get() == "Compress":
            title = "Select image to compress"
        else:
            title = "Select image to convert"
        filetypes = IMAGE_INPUT

        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if not path:
            return

        self.input_path.set(path)
        if self.image_tool.get() == "Compress":
            self.status.set("Image selected. Ready to compress.")
        else:
            self.status.set(f"Image selected. Ready to convert to {self.output_format.get()}.")
        self.progress.set(0)
        self._update_preview(Path(path))

    def pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_dir.set(path)

    def process_selected_image(self) -> None:
        input_path = Path(self.input_path.get().strip())
        output_dir = Path(self.output_dir.get().strip())
        tool = self.image_tool.get()
        output_format = self.output_format.get().lower()

        if not input_path.exists():
            messagebox.showerror("Missing file", "Please choose an image first.")
            return

        if tool == "Convert" and input_path.suffix.lower() not in CONVERTIBLE_IMAGE_INPUTS:
            messagebox.showerror("Unsupported file", f"Conversion supports {CONVERSION_FORMAT_TEXT} images.")
            return

        if tool == "Convert" and output_format not in SUPPORTED_IMAGE_OUTPUTS:
            messagebox.showerror("Unsupported format", f"Choose {CONVERSION_FORMAT_TEXT} as the output format.")
            return

        if tool == "Compress" and input_path.suffix.lower() not in COMPRESSIBLE_IMAGE_INPUTS:
            messagebox.showerror("Unsupported file", f"Compression supports {COMPRESSION_FORMAT_TEXT} images.")
            return

        busy_text = "Compressing..." if tool == "Compress" else "Converting..."
        self.convert_button.configure(state="disabled", text=busy_text)
        self.status.set("Compressing image..." if tool == "Compress" else "Converting image...")
        self.progress.set(0.35)

        thread = threading.Thread(
            target=self._image_worker,
            args=(tool, input_path, output_dir, output_format, self.quality.get()),
            daemon=True,
        )
        thread.start()

    def _image_worker(
        self,
        tool: str,
        input_path: Path,
        output_dir: Path,
        output_format: str,
        quality: int,
    ) -> None:
        try:
            if tool == "Compress":
                output_path = compress_image(input_path, output_dir=output_dir, quality=quality)
            else:
                output_path = convert_image(
                    input_path,
                    output_dir=output_dir,
                    output_format=output_format,
                    quality=quality,
                )
        except Exception as exc:
            self.after(0, self._conversion_failed, str(exc))
            return

        self.after(0, self._conversion_finished, tool, input_path, output_path)

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
        button_text = "Compress Image" if self.image_tool.get() == "Compress" else self._convert_button_text()
        self.convert_button.configure(state="normal", text=button_text)
        messagebox.showerror("Processing failed", error)

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

    def _set_preview(self, text: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")


def main() -> None:
    app = MediaUtilityApp()
    app.mainloop()


if __name__ == "__main__":
    main()
