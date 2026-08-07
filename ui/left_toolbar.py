# ui/left_toolbar.py
import os
import io
import tkinter as tk
from PIL import Image, ImageTk

# Optional import of cairosvg for native vector rendering
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False


class ToolTip:
    """Floating Photoshop-style hover tooltip."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 48
        y = self.widget.winfo_rooty() + 2

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            bg="#252526",
            fg="#ffffff",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9, "normal"),
            padx=6,
            pady=3,
        )
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class LeftToolbar(tk.Frame):
    """Photoshop-style vertical left sidebar with SVG rendering support and hover tooltips."""

    ICON_SIZE = (22, 22)

    def __init__(self, parent, main_app, icons_dir="assets/icons"):
        self.app = main_app
        self.colors = main_app.colors
        self.icons_dir = icons_dir

        is_dark = self.app.current_mode == "dark"
        bg_color = self.colors.get("toolbar_bg", "#252526" if is_dark else "#e8e8e8")

        super().__init__(
            parent,
            bg=bg_color,
            width=48,
            bd=1,
            relief=tk.SOLID,
        )
        self.pack_propagate(False)

        self.loaded_images = {}
        self.buttons = {}

        self._build_tools()

    def _load_icon(self, filename):
        if not filename:
            return None

        file_path = os.path.join(self.icons_dir, filename)
        if not os.path.exists(file_path):
            return None

        try:
            if HAS_CAIROSVG and filename.lower().endswith(".svg"):
                # Convert SVG vector to crisp PNG bytes in memory via CairoSVG
                png_bytes = cairosvg.svg2png(
                    url=file_path,
                    output_width=self.ICON_SIZE[0],
                    output_height=self.ICON_SIZE[1],
                )
                pil_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                
                if self.app.current_mode == "dark":
                    _, _, _, a = pil_img.split()
                    white_layer = Image.new("RGB", pil_img.size, (255, 255, 255))
                    wr, wg, wb = white_layer.split()
                    pil_img = Image.merge("RGBA", (wr, wg, wb, a))

            else:
                pil_img = Image.open(file_path).resize(
                    self.ICON_SIZE, Image.Resampling.LANCZOS
                )

            return ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Error loading icon '{filename}': {e}")
            return None

    def _build_tools(self):
        tools = [
            ("crop", "crop.svg", "✂️", "Crop Image (Ctrl+X)", lambda: self.app.cropper.toggle_crop_mode()),
            ("rotate_left", "rotate_left.svg", "⮌", "Rotate Left (Ctrl+Shift+R)", lambda: self.app.rotator.rotate_selected(-90)),
            ("rotate_right", "rotate_right.svg", "⮎", "Rotate Right (Ctrl+R)", lambda: self.app.rotator.rotate_selected(90)),
            ("bw", "bw.svg", "◐", "Black & White (Ctrl+B)", lambda: self.app.color_invertor.grayscale_selected()),
            ("invert", "invert.svg", "☯", "Invert Colors (Ctrl+I)", lambda: self.app.color_invertor.invert_selected()),
            ("enhance", "enhance.svg", "☀️", "Enhance Quality (Ctrl+E)", lambda: self.app.enhancer.open_enhancer_dialog()),
            ("watermark", "watermark.svg", "🏷️", "Add Watermark (Ctrl+W)", lambda: self.app.watermarker.open_watermark_dialog()),
            ("sep", None, None, None, None),
            ("reset", "reset.svg", "🔄", "Reset to Original (Ctrl+O)", lambda: self.app.color_invertor.restore_original_selected()),
        ]

        is_dark = self.app.current_mode == "dark"
        fg_color = "#ffffff" if is_dark else "#111111"

        pad_top = tk.Frame(self, height=6, bg=self.cget("bg"))
        pad_top.pack(side=tk.TOP, fill=tk.X)

        for item in tools:
            tool_id = item[0]
            if tool_id == "sep":
                sep = tk.Frame(self, height=1, bg="#555555" if is_dark else "#cccccc", bd=0)
                sep.pack(fill=tk.X, padx=6, pady=6)
                continue

            icon_file, symbol, tooltip_text, command = item[1], item[2], item[3], item[4]

            icon_tk = self._load_icon(icon_file)
            if icon_tk:
                self.loaded_images[tool_id] = icon_tk

            has_icon = icon_tk is not None

            btn = tk.Button(
                self,
                image=icon_tk if has_icon else "",
                text="" if has_icon else symbol,
                command=command,
                bg=self.cget("bg"),
                fg=fg_color,
                activebackground="#3e3e42" if is_dark else "#d0d0d0",
                activeforeground="#ffffff" if is_dark else "#000000",
                bd=0,
                relief=tk.FLAT,
                cursor="hand2",
                font=("Segoe UI Symbol", 12, "bold"),
                width=38,
                height=34,
            )
            btn.pack(side=tk.TOP, pady=3, padx=4)

            btn.bind(
                "<Enter>",
                lambda e, b=btn: b.config(
                    bg="#3e3e42" if self.app.current_mode == "dark" else "#e0e0e0"
                ),
            )
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.cget("bg")))

            ToolTip(btn, tooltip_text)
            self.buttons[tool_id] = btn

    def update_theme(self, new_bg, is_dark=True):
        """Rebuilds left toolbar buttons so SVG icon colors re-render for active theme."""
        self.config(bg=new_bg)
        
        # Destroy old tool buttons and clear image references
        for child in self.winfo_children():
            child.destroy()
        self.buttons.clear()
        self.loaded_images.clear()

        # Re-build tool buttons under the newly selected mode
        self._build_tools()
