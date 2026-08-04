# features/pdf_compressor.py
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from theme import set_title_bar_mode, RoundedButton

class PDFCompressorFeature:
    """Standalone feature to compress images with live Quality & Scale sliders in a popup dialog."""

    def __init__(self, main_app):
        self.app = main_app

    def compress_and_export(self):
        """Main entry point: validates image list and opens the compression dialog."""
        if not self.app.image_list:
            self.app.show_warning("Empty", "No images pasted yet to compress!")
            return

        # Open Compression Popup directly
        CompressionDialog(self.app, self._execute_save)
    def _execute_save(self, quality_val, scale_val):
        """Internal module callback: Prompts for save path and compiles compressed PDF."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Compressed PDF As",
        )
        if not file_path:
            return

        try:
            # Process resolution downscaling & force RGB conversion for JPEG compression
            export_images = self._process_images(self.app.image_list, scale_val)

            first_image = export_images[0]
            subsequent_images = export_images[1:]

            # FIX: Explicitly specify format="PDF" and resolution params
            first_image.save(
                file_path,
                format="PDF",
                save_all=True,
                append_images=subsequent_images,
                quality=quality_val,  # Now applies cleanly to all converted JPEG streams
                optimize=True,
            )

            self.app.show_info(
                "Success",
                f"Compressed PDF saved successfully!\n"
                f"Pages: {len(self.app.image_list)} | Quality: {quality_val}% | Scale: {scale_val}%",
            )
        except Exception as e:
            self.app.show_error("Error", f"Failed to save PDF:\n{str(e)}")

    def _process_images(self, image_list, scale_val):
        """Downscales PIL images and forces RGB mode so JPEG compression works."""
        processed_images = []
        scale_factor = scale_val / 100.0

        for img in image_list:
            working_img = img.copy()

            # CRITICAL FIX: Convert RGBA/P/L images to RGB on a white background.
            # JPEG does not support alpha channel. Without this, Pillow saves raw uncompressed bitmaps!
            if working_img.mode in ("RGBA", "LA") or (working_img.mode == "P" and "transparency" in working_img.info):
                background = Image.new("RGB", working_img.size, (255, 255, 255))
                if working_img.mode != "RGBA":
                    working_img = working_img.convert("RGBA")
                background.paste(working_img, mask=working_img.split()[3]) # 3 is alpha channel
                working_img = background
            elif working_img.mode != "RGB":
                working_img = working_img.convert("RGB")

            # Dimensional downscaling
            if scale_factor < 1.0:
                new_w = max(int(working_img.width * scale_factor), 10)
                new_h = max(int(working_img.height * scale_factor), 10)
                working_img = working_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            processed_images.append(working_img)

        return processed_images
class CompressionDialog(tk.Toplevel):
    """Popup modal using standard tkinter elements styled with theme.py."""

    def __init__(self, main_app, on_confirm_callback):
        super().__init__(main_app.root)

        self.app = main_app
        self.on_confirm = on_confirm_callback
        self.colors = main_app.colors

        self.title("PDF Compression Settings")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(bg=self.colors["bg"])

        # Center relative to parent window
        main_app.root.update_idletasks()
        pw = main_app.root.winfo_width()
        ph = main_app.root.winfo_height()
        px = main_app.root.winfo_x()
        py = main_app.root.winfo_y()

        cw = px + (pw // 2) - 200
        ch = py + (ph // 2) - 160
        self.geometry(f"400x320+{cw}+{ch}")

        self.transient(main_app.root)
        self.grab_set()

        if self.colors["bg"] == "#1e1e1e":
            set_title_bar_mode(self, dark=True)

        self._build_ui()

    def _build_ui(self):
        # Header Label
        lbl_title = tk.Label(
            self,
            text="🗜️ PDF Compression Settings",
            font=("Arial", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_title.pack(pady=(15, 10))

        # 1. Quality Slider Frame
        frame_quality = tk.Frame(self, bg=self.colors["bg"])
        frame_quality.pack(fill="x", padx=25, pady=8)

        self.lbl_quality_val = tk.Label(
            frame_quality,
            text="Quality: 85%",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.lbl_quality_val.pack(anchor="w")

        self.slider_quality = tk.Scale(
            frame_quality,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            command=self._update_quality_label,
        )
        self.slider_quality.set(85)
        self.slider_quality.pack(fill="x", pady=2)

        # 2. Scale Factor Slider Frame
        frame_scale = tk.Frame(self, bg=self.colors["bg"])
        frame_scale.pack(fill="x", padx=25, pady=8)

        self.lbl_scale_val = tk.Label(
            frame_scale,
            text="Scale Down Dimensions: 100%",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.lbl_scale_val.pack(anchor="w")

        self.slider_scale = tk.Scale(
            frame_scale,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            command=self._update_scale_label,
        )
        self.slider_scale.set(100)
        self.slider_scale.pack(fill="x", pady=2)

        # Action Buttons
        btn_frame = tk.Frame(self, bg=self.colors["bg"])
        btn_frame.pack(fill="x", pady=(15, 0), padx=25)

        self.btn_export = RoundedButton(
            btn_frame,
            text="Save PDF",
            command=self._on_export,
            bg_color="#1D9E21",
            hover_color="#10a018",
            text_color="white",
            radius=6,
            width=100,
            height=34,
        )
        self.btn_export.pack(side=tk.RIGHT, padx=(5, 0))

        self.btn_cancel = RoundedButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bg_color="#8a8888",
            hover_color="#c9c7c7",
            text_color="white",
            radius=6,
            width=80,
            height=34,
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _update_quality_label(self, val):
        self.lbl_quality_val.config(text=f"Quality (Res): {int(float(val))}%")

    def _update_scale_label(self, val):
        self.lbl_scale_val.config(text=f"Scale Down Dimensions: {int(float(val))}%")

    def _on_export(self):
        quality = int(self.slider_quality.get())
        scale = int(self.slider_scale.get())
        self.destroy()
        self.on_confirm(quality, scale)
