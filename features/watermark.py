import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
from theme import RoundedButton, set_title_bar_mode


class WatermarkFeature:
    """Standalone feature to apply text or image logo watermarks across all or selected pages."""

    def __init__(self, main_app):
        self.app = main_app

    def open_watermark_dialog(self):
        """Launches the Watermark configuration window."""
        if not self.app.image_list:
            self.app.show_warning("Empty", "No images pasted yet to watermark!")
            return

        WatermarkDialog(self.app)


class WatermarkDialog(tk.Toplevel):
    """Interactive modal dialog for configuring and previewing watermarks."""

    POSITIONS = [
        "Center",
        "Top-Left",
        "Top-Right",
        "Bottom-Left",
        "Bottom-Right",
        "Tiled Matrix",
    ]

    def __init__(self, main_app):
        super().__init__(main_app.root)

        self.app = main_app
        self.colors = main_app.colors

        # Default working copy of currently selected image (or first image)
        preview_idx = self.app.selected_index if self.app.selected_index is not None else 0
        self.sample_pil = self.app.image_list[preview_idx].copy()

        self.title("🏷️ Custom Watermark Tool")
        self.geometry("820x620")
        self.resizable(False, False)
        self.configure(bg=self.colors["bg"])

        # Center relative to parent
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

        self.watermark_type_var = tk.StringVar(value="Text")
        self.position_var = tk.StringVar(value="Center")
        self.apply_scope_var = tk.StringVar(value="All Pages")
        self.logo_path = None
        self.logo_pil = None
        self.tk_preview = None

        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        # Header Label
        lbl_title = tk.Label(
            self,
            text="Custom Watermarking (Text or Logo)",
            font=("Arial", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_title.pack(pady=(12, 6))

        # Main Layout: Left Controls, Right Preview
        content_frame = tk.Frame(self, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # --- LEFT CONTROLS PANEL ---
        controls_frame = tk.Frame(content_frame, bg=self.colors["bg"], width=380)
        controls_frame.pack(side=tk.LEFT, fill="y", padx=(0, 10))

        # 1. Type Radio Selector (Text vs Logo Image)
        lbl_type = tk.Label(
            controls_frame,
            text="Watermark Type:",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_type.pack(anchor="w", pady=(2, 2))

        type_radio_frame = tk.Frame(controls_frame, bg=self.colors["bg"])
        type_radio_frame.pack(anchor="w", pady=(0, 8))

        rb_text = tk.Radiobutton(
            type_radio_frame,
            text="Text",
            variable=self.watermark_type_var,
            value="Text",
            command=self._on_type_change,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"],
            font=("Arial", 9, "bold"),
        )
        rb_text.pack(side=tk.LEFT, padx=(0, 15))

        rb_logo = tk.Radiobutton(
            type_radio_frame,
            text="Logo Image",
            variable=self.watermark_type_var,
            value="Logo",
            command=self._on_type_change,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"],
            font=("Arial", 9, "bold"),
        )
        rb_logo.pack(side=tk.LEFT)

        # 2. Text Input / Logo Selection Frame
        self.frame_text_input = tk.Frame(controls_frame, bg=self.colors["bg"])
        self.frame_text_input.pack(fill="x", pady=(0, 8))

        lbl_text = tk.Label(
            self.frame_text_input,
            text="Watermark Text:",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_text.pack(anchor="w")

        self.entry_text = tk.Entry(
            self.frame_text_input,
            font=("Arial", 10),
            bg="#2b2b2b" if self.colors["bg"] == "#1e1e1e" else "#ffffff",
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            bd=1,
            relief=tk.SOLID,
        )
        self.entry_text.insert(0, "CONFIDENTIAL")
        self.entry_text.pack(fill="x", pady=(2, 0))
        self.entry_text.bind("<KeyRelease>", lambda e: self._update_preview())

        self.frame_logo_input = tk.Frame(controls_frame, bg=self.colors["bg"])

        self.btn_browse_logo = RoundedButton(
            self.frame_logo_input,
            text="Choose Logo Image",
            command=self._browse_logo,
            bg_color="#1F6AA5",
            hover_color="#144870",
            text_color="white",
            radius=6,
            width=160,
            height=30,
        )
        self.btn_browse_logo.pack(anchor="w", pady=(2, 2))

        self.lbl_logo_file = tk.Label(
            self.frame_logo_input,
            text="No logo file chosen",
            font=("Arial", 8, "italic"),
            bg=self.colors["bg"],
            fg=self.colors["subtext"],
        )
        self.lbl_logo_file.pack(anchor="w")

        # 3. Position Dropdown Selector
        lbl_pos = tk.Label(
            controls_frame,
            text="Position:",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_pos.pack(anchor="w", pady=(4, 0))

        opt_pos = tk.OptionMenu(
            controls_frame,
            self.position_var,
            *self.POSITIONS,
            command=lambda _: self._update_preview(),
        )
        opt_pos.config(
            bg="#2b2b2b" if self.colors["bg"] == "#1e1e1e" else "#e5e5e5",
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
        )
        opt_pos.pack(fill="x", pady=(2, 8))

        # 4. Opacity Slider (10% to 100%)
        self.lbl_opacity = tk.Label(
            controls_frame,
            text="Opacity: 35%",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.lbl_opacity.pack(anchor="w")

        self.slider_opacity = tk.Scale(
            controls_frame,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            length=350,
            command=self._on_slider_change,
        )
        self.slider_opacity.set(35)
        self.slider_opacity.pack(anchor="w", pady=(0, 6))

        # 5. Size / Scale Slider
        self.lbl_size = tk.Label(
            controls_frame,
            text="Size / Scale: 50",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.lbl_size.pack(anchor="w")

        self.slider_size = tk.Scale(
            controls_frame,
            from_=10,
            to=150,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            length=350,
            command=self._on_slider_change,
        )
        self.slider_size.set(50)
        self.slider_size.pack(anchor="w", pady=(0, 6))

        # 6. Rotation Angle Slider (-90° to +90°)
        self.lbl_angle = tk.Label(
            controls_frame,
            text="Rotation Angle: -30°",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        self.lbl_angle.pack(anchor="w")

        self.slider_angle = tk.Scale(
            controls_frame,
            from_=-90,
            to=90,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            length=350,
            command=self._on_slider_change,
        )
        self.slider_angle.set(-30)
        self.slider_angle.pack(anchor="w", pady=(0, 8))

        # 7. Apply Scope (Current Page vs All Pages)
        lbl_scope = tk.Label(
            controls_frame,
            text="Apply To:",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["text"],
        )
        lbl_scope.pack(anchor="w", pady=(2, 2))

        scope_radio_frame = tk.Frame(controls_frame, bg=self.colors["bg"])
        scope_radio_frame.pack(anchor="w")

        rb_all = tk.Radiobutton(
            scope_radio_frame,
            text="All Pages",
            variable=self.apply_scope_var,
            value="All Pages",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"],
            font=("Arial", 9),
        )
        rb_all.pack(side=tk.LEFT, padx=(0, 15))

        rb_current = tk.Radiobutton(
            scope_radio_frame,
            text="Selected Page Only",
            variable=self.apply_scope_var,
            value="Selected Page Only",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            selectcolor=self.colors["bg"],
            activebackground=self.colors["bg"],
            activeforeground=self.colors["text"],
            font=("Arial", 9),
        )
        rb_current.pack(side=tk.LEFT)

        # --- RIGHT PREVIEW PANEL ---
        preview_container = tk.Frame(content_frame, bg=self.colors["bg"])
        preview_container.pack(side=tk.RIGHT, fill="both", expand=True)

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
            text="Apply Watermark",
            command=self._apply_watermark,
            bg_color="#1D9E21",
            hover_color="#10a018",
            text_color="white",
            radius=6,
            width=140,
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

    def _on_type_change(self):
        w_type = self.watermark_type_var.get()
        if w_type == "Text":
            self.frame_logo_input.pack_forget()
            self.frame_text_input.pack(fill="x", pady=(0, 8))
        else:
            self.frame_text_input.pack_forget()
            self.frame_logo_input.pack(fill="x", pady=(0, 8))

        self._update_preview()

    def _browse_logo(self):
        file_path = filedialog.askopenfilename(
            title="Select Watermark Logo Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")],
        )
        if file_path:
            self.logo_path = file_path
            self.logo_pil = Image.open(file_path).convert("RGBA")
            file_name = file_path.split("/")[-1].split("\\")[-1]
            self.lbl_logo_file.config(text=file_name)
            self._update_preview()

    def _on_slider_change(self, _=None):
        self.lbl_opacity.config(text=f"Opacity: {int(self.slider_opacity.get())}%")
        self.lbl_size.config(text=f"Size / Scale: {int(self.slider_size.get())}")
        self.lbl_angle.config(text=f"Rotation Angle: {int(self.slider_angle.get())}°")
        self._update_preview()

    def _render_watermark_on_image(self, src_img):
        """Applies configured text or logo watermark onto a PIL image copy."""
        target = src_img.copy().convert("RGBA")
        w_type = self.watermark_type_var.get()
        opacity_val = int(self.slider_opacity.get()) / 100.0
        alpha_byte = int(255 * opacity_val)
        size_val = int(self.slider_size.get())
        angle_val = int(self.slider_angle.get())
        pos_val = self.position_var.get()

        if w_type == "Text":
            text_str = self.entry_text.get().strip()
            if not text_str:
                return target.convert("RGB")

            # Create text layer
            try:
                font = ImageFont.truetype("arial.ttf", size=size_val)
            except IOError:
                font = ImageFont.load_default()

            dummy_draw = ImageDraw.Draw(target)
            bbox = dummy_draw.textbbox((0, 0), text_str, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            txt_img = Image.new("RGBA", (tw + 20, th + 20), (255, 255, 255, 0))
            d = ImageDraw.Draw(txt_img)
            d.text((10, 10), text_str, fill=(128, 128, 128, alpha_byte), font=font)

            if angle_val != 0:
                txt_img = txt_img.rotate(angle_val, expand=True, resample=Image.Resampling.BICUBIC)

            wm_layer = txt_img
        else:
            if not self.logo_pil:
                return target.convert("RGB")

            # Scale logo
            logo_w = int(target.width * (size_val / 200.0))
            ratio = logo_w / float(self.logo_pil.width)
            logo_h = int(self.logo_pil.height * ratio)

            logo_resized = self.logo_pil.resize((max(logo_w, 10), max(logo_h, 10)), Image.Resampling.LANCZOS)

            # Apply opacity
            r, g, b, a = logo_resized.split()
            a = a.point(lambda p: int(p * opacity_val))
            logo_resized = Image.merge("RGBA", (r, g, b, a))

            if angle_val != 0:
                logo_resized = logo_resized.rotate(angle_val, expand=True, resample=Image.Resampling.BICUBIC)

            wm_layer = logo_resized

        # Stamp watermark onto canvas based on position setting
        img_w, img_h = target.size
        wm_w, wm_h = wm_layer.size

        if pos_val == "Tiled Matrix":
            for x in range(0, img_w, wm_w + 80):
                for y in range(0, img_h, wm_h + 80):
                    target.alpha_composite(wm_layer, (x, y))
        else:
            if pos_val == "Center":
                px = (img_w - wm_w) // 2
                py = (img_h - wm_h) // 2
            elif pos_val == "Top-Left":
                px, py = 30, 30
            elif pos_val == "Top-Right":
                px, py = img_w - wm_w - 30, 30
            elif pos_val == "Bottom-Left":
                px, py = 30, img_h - wm_h - 30
            elif pos_val == "Bottom-Right":
                px, py = img_w - wm_w - 30, img_h - wm_h - 30

            px = max(0, min(px, img_w - wm_w))
            py = max(0, min(py, img_h - wm_h))
            target.alpha_composite(wm_layer, (px, py))

        return target.convert("RGB")

    def _update_preview(self):
        watermarked = self._render_watermark_on_image(self.sample_pil)
        watermarked.thumbnail((360, 360), Image.Resampling.LANCZOS)

        self.tk_preview = ImageTk.PhotoImage(watermarked)
        self.lbl_preview.config(image=self.tk_preview)

    def _apply_watermark(self):
        self.app.save_snapshot()

        scope = self.apply_scope_var.get()
        if scope == "Selected Page Only":
            idx = self.app.selected_index if self.app.selected_index is not None else 0
            indices = [idx]
        else:
            indices = list(range(len(self.app.image_list)))

        for i in indices:
            watermarked_img = self._render_watermark_on_image(self.app.image_list[i])
            self.app.image_list[i] = watermarked_img
            self.app.rebuild_single_thumbnail(i)

        # Update main workspace canvas
        curr_idx = self.app.selected_index if self.app.selected_index is not None else 0
        self.app.update_main_canvas(self.app.image_list[curr_idx])
        self.app.refresh_thumbnail_layout()

        self.destroy()
