import tkinter as tk
from PIL import Image, ImageEnhance, ImageOps, ImageStat, ImageTk
from theme import RoundedButton, set_title_bar_mode


class ImageEnhancerFeature:
    """Pro Image Adjustments: Auto-Enhance, Original Toggle, Exposure, Brightness, Contrast, Saturation, Hue, Shadows, Highlights & Sharpen."""

    def __init__(self, main_app):
        self.app = main_app

    def open_enhancer_dialog(self):
        """Launches the full adjustment window for the selected image."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to enhance!")
            return

        target_img = self.app.image_list[idx]
        ProEnhancerDialog(self.app, idx, target_img)


class ProEnhancerDialog(tk.Toplevel):
    """Interactive modal dialog with live preview, Auto-Enhance algorithm, and Original Toggle."""

    def __init__(self, main_app, image_idx, pil_image):
        super().__init__(main_app.root)

        self.app = main_app
        self.image_idx = image_idx
        self.original_pil = pil_image.copy()
        self.colors = main_app.colors

        self.title("Pro Image Adjustments")
        self.geometry("820x620")
        self.resizable(False, False)
        self.configure(bg=self.colors["bg"])

        # Center window relative to main app
        main_app.root.update_idletasks()
        pw = main_app.root.winfo_width()
        ph = main_app.root.winfo_height()
        px = main_app.root.winfo_x()
        py = main_app.root.winfo_y()

        cw = px + (pw // 2) - 410
        ch = py + (ph // 2) - 310
        self.geometry(f"820x620+{cw}+{ch}")

        self.transient(main_app.root)
        self.grab_set()

        if self.colors["bg"] == "#1e1e1e":
            set_title_bar_mode(self, dark=True)

        self.tk_preview = None
        self.show_original_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        # Header Label
        lbl_title = tk.Label(
            self,
            text="Advanced Color & Light Adjustments",
            font=("Arial", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_title.pack(pady=(10, 5))

        # Main Layout: Left Controls, Right Preview
        content_frame = tk.Frame(self, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # --- LEFT CONTROLS PANEL ---
        controls_frame = tk.Frame(content_frame, bg=self.colors["bg"], width=380)
        controls_frame.pack(side=tk.LEFT, fill="y", padx=(0, 10))

        # Top Preset Bar (Auto Enhance & Reset)
        preset_bar = tk.Frame(controls_frame, bg=self.colors["bg"])
        preset_bar.pack(anchor="w", fill="x", pady=(0, 8))

        self.btn_auto = RoundedButton(
            preset_bar,
            text="Auto Enhance",
            command=self._apply_auto_enhance,
            bg_color="#1F6AA5",
            hover_color="#144870",
            text_color="white",
            radius=6,
            width=120,
            height=30,
        )
        self.btn_auto.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_reset_sliders = RoundedButton(
            preset_bar,
            text="Reset All",
            command=self._reset_sliders,
            bg_color="#555555",
            hover_color="#666666",
            text_color="white",
            radius=6,
            width=90,
            height=30,
        )
        self.btn_reset_sliders.pack(side=tk.LEFT)

        # Helper to create styled sliders
        def create_slider(parent, label_text, from_val, to_val, default_val, res=0.05):
            lbl = tk.Label(
                parent,
                text=label_text,
                font=("Arial", 9, "bold"),
                bg=self.colors["bg"],
                fg=self.colors["text"],
            )
            lbl.pack(anchor="w", pady=(2, 0))

            slider = tk.Scale(
                parent,
                from_=from_val,
                to=to_val,
                resolution=res,
                orient=tk.HORIZONTAL,
                bg=self.colors["bg"],
                fg=self.colors["text"],
                highlightthickness=0,
                bd=0,
                length=350,
                command=self._on_slider_change,
            )
            slider.set(default_val)
            slider.pack(anchor="w", pady=(0, 2))
            return lbl, slider

        # Sliders Setup
        self.lbl_exposure, self.slider_exposure = create_slider(
            controls_frame, "Exposure: 0.0 EV", -2.0, 2.0, 0.0, 0.1
        )
        self.lbl_brightness, self.slider_brightness = create_slider(
            controls_frame, "Brightness: 1.0x", 0.2, 2.5, 1.0
        )
        self.lbl_contrast, self.slider_contrast = create_slider(
            controls_frame, "Contrast: 1.0x", 0.2, 2.5, 1.0
        )
        self.lbl_saturation, self.slider_saturation = create_slider(
            controls_frame, "Saturation: 1.0x", 0.0, 3.0, 1.0
        )
        self.lbl_hue, self.slider_hue = create_slider(
            controls_frame, "Hue Shift: 0°", -180, 180, 0, 1
        )
        self.lbl_shadows, self.slider_shadows = create_slider(
            controls_frame, "Shadows: 0", -100, 100, 0, 1
        )
        self.lbl_highlights, self.slider_highlights = create_slider(
            controls_frame, "Highlights: 0", -100, 100, 0, 1
        )
        self.lbl_sharpen, self.slider_sharpen = create_slider(
            controls_frame, "Sharpening: 1.0x", 0.0, 4.0, 1.0, 0.1
        )

        # --- RIGHT PREVIEW PANEL ---
        preview_container = tk.Frame(content_frame, bg=self.colors["bg"])
        preview_container.pack(side=tk.RIGHT, fill="both", expand=True)

        # Toggle Original Checkbox above preview
        self.chk_original = tk.Checkbutton(
            preview_container,
            text="Show Original (Hold/Toggle)",
            variable=self.show_original_var,
            command=self._update_preview,
            font=("Arial", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"],
        )
        self.chk_original.pack(anchor="w", pady=(0, 5))

        preview_frame = tk.Frame(
            preview_container,
            bg="#111111" if self.colors["bg"] == "#1e1e1e" else "#e5e5e5",
            bd=1,
            relief=tk.SOLID,
        )
        preview_frame.pack(fill="both", expand=True)

        self.lbl_preview = tk.Label(preview_frame, bg=preview_frame["bg"])
        self.lbl_preview.pack(fill="both", expand=True, padx=5, pady=5)

        # --- BOTTOM ACTION BUTTONS ---
        btn_frame = tk.Frame(self, bg=self.colors["bg"])
        btn_frame.pack(fill="x", pady=(8, 12), padx=20)

        self.btn_apply = RoundedButton(
            btn_frame,
            text="Apply Changes",
            command=self._apply_enhancements,
            bg_color="#1D9E21",
            hover_color="#10a018",
            text_color="white",
            radius=6,
            width=120,
            height=34,
        )
        self.btn_apply.pack(side=tk.RIGHT, padx=(5, 0))

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

    def _apply_auto_enhance(self):
        """Applies well-known auto-contrast & white-balance algorithms."""
        img = self.original_pil.copy()
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 1. Histogram Auto-Contrast (stretches pixel intensities, ignoring top/bottom 1% outliers)
        auto_img = ImageOps.autocontrast(img, cutoff=1)

        # 2. Calculate average brightness shift to set initial slider values automatically
        stat_orig = ImageStat.Stat(img)
        stat_auto = ImageStat.Stat(auto_img)

        orig_brightness = sum(stat_orig.mean) / 3.0
        auto_brightness = sum(stat_auto.mean) / 3.0

        # Map auto ratio back to sliders so user can fine-tune
        brightness_ratio = auto_brightness / max(orig_brightness, 1.0)
        
        self.slider_exposure.set(0.0)
        self.slider_brightness.set(round(min(max(brightness_ratio, 0.8), 1.6), 2))
        self.slider_contrast.set(1.25)  # Mild contrast boost for documents
        self.slider_saturation.set(1.05)
        self.slider_hue.set(0)
        self.slider_shadows.set(15)     # Recover shadow details
        self.slider_highlights.set(-10) # Reduce blown-out highlights
        self.slider_sharpen.set(1.5)    # Sharpen text/edges

        self._on_slider_change()

    def _on_slider_change(self, _=None):
        self.lbl_exposure.config(text=f"Exposure: {self.slider_exposure.get():.1f} EV")
        self.lbl_brightness.config(text=f"Brightness: {self.slider_brightness.get():.2f}x")
        self.lbl_contrast.config(text=f"Contrast: {self.slider_contrast.get():.2f}x")
        self.lbl_saturation.config(text=f"Saturation: {self.slider_saturation.get():.2f}x")
        self.lbl_hue.config(text=f"Hue Shift: {int(self.slider_hue.get())}°")
        self.lbl_shadows.config(text=f"Shadows: {int(self.slider_shadows.get())}")
        self.lbl_highlights.config(text=f"Highlights: {int(self.slider_highlights.get())}")
        self.lbl_sharpen.config(text=f"Sharpening: {self.slider_sharpen.get():.1f}x")

        self._update_preview()

    def _reset_sliders(self):
        self.slider_exposure.set(0.0)
        self.slider_brightness.set(1.0)
        self.slider_contrast.set(1.0)
        self.slider_saturation.set(1.0)
        self.slider_hue.set(0)
        self.slider_shadows.set(0)
        self.slider_highlights.set(0)
        self.slider_sharpen.set(1.0)
        self._on_slider_change()

    def _process_image(self, src_img):
        img = src_img.copy()
        if img.mode != "RGB":
            img = img.convert("RGB")

        exp_val = float(self.slider_exposure.get())
        b_val = float(self.slider_brightness.get())
        c_val = float(self.slider_contrast.get())
        sat_val = float(self.slider_saturation.get())
        hue_val = int(self.slider_hue.get())
        shd_val = int(self.slider_shadows.get())
        hl_val = int(self.slider_highlights.get())
        srp_val = float(self.slider_sharpen.get())

        if exp_val != 0.0:
            img = ImageEnhance.Brightness(img).enhance(2.0 ** exp_val)
        if b_val != 1.0:
            img = ImageEnhance.Brightness(img).enhance(b_val)
        if c_val != 1.0:
            img = ImageEnhance.Contrast(img).enhance(c_val)
        if sat_val != 1.0:
            img = ImageEnhance.Color(img).enhance(sat_val)

        if hue_val != 0:
            hsv = img.convert("HSV")
            h, s, v = hsv.split()
            shift_int = int((hue_val / 360.0) * 255)
            h = h.point(lambda p: (p + shift_int) % 256)
            img = Image.merge("HSV", (h, s, v)).convert("RGB")

        if shd_val != 0 or hl_val != 0:
            lut = []
            for i in range(256):
                val = i
                norm = i / 255.0
                if shd_val != 0:
                    val += shd_val * ((1.0 - norm) ** 2)
                if hl_val != 0:
                    val += hl_val * (norm ** 2)
                lut.append(int(max(0, min(255, val))))
            img = img.point(lut * 3)

        if srp_val != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(srp_val)

        return img

    def _update_preview(self):
        """Generates real-time preview (or displays unedited original if checkbox is checked)."""
        if self.show_original_var.get():
            preview_img = self.original_pil.copy()
        else:
            preview_img = self._process_image(self.original_pil)

        preview_img.thumbnail((360, 360), Image.Resampling.LANCZOS)
        self.tk_preview = ImageTk.PhotoImage(preview_img)
        self.lbl_preview.config(image=self.tk_preview)

    def _apply_enhancements(self):
        self.app.save_snapshot()

        final_img = self._process_image(self.original_pil)
        self.app.image_list[self.image_idx] = final_img

        self.app.rebuild_single_thumbnail(self.image_idx)
        self.app.update_main_canvas(final_img)
        self.app.refresh_thumbnail_layout()

        self.destroy()
