#theme.py
import tkinter as tk

# Application Theme Color Palettes
THEMES = {
    "light": {
        "bg": "#f5f5f5",
        "toolbar_bg": "#e8e8e8",
        "tray_bg": "#e0e0e0",
        "text": "#333333",
        "subtext": "#666666",
        "card_bg": "#ffffff",
        # "card_selected": "#0078d7",
        "card_selected": "#7D7D7E",
        "card_text": "#000000",
        "card_text_selected": "#ffffff",
        "border": "#cccccc",
        "btn_theme_bg": "#333333",
        "btn_theme_hover": "#555555",
        "btn_theme_fg": "#ffffff",
        "scrollbar_track": "#e0e0e0",
        "scrollbar_thumb": "#aaaaaa",
    },
    "dark": {
        "bg": "#1e1e1e",
        "toolbar_bg": "#252526",
        "tray_bg": "#2d2d2d",
        "text": "#cccccc",
        "subtext": "#888888",
        "card_bg": "#333333",
        # "card_selected": "#0078d7",
        "card_selected": "#909192",
        "card_text": "#ffffff",
        "card_text_selected": "#ffffff",
        "border": "#3c3c3c",
        "btn_theme_bg": "#8a8888",
        "btn_theme_hover": "#c9c7c7",
        "btn_theme_fg": "#FFFFFF",
        "scrollbar_track": "#2d2d2d",
        "scrollbar_thumb": "#555555",
    },
}

# Application Layout & Dimension Constants
LAYOUT = {
    # Window & Canvas
    "app_title": "Image to PDF Creator",
    "window_size": "950x700",
    "min_window_size": (700, 500),
    "dialog_size": (380, 180),
    "default_canvas_size": 350,
    "default_thumb_size": 70,
    "thumb_tray_height": 150,
    "scrollbar_height": 10,
    # Fonts
    "font_main": ("Arial", 11),
    "font_instruction": ("Arial", 11),
    "font_info": ("Arial", 9, "italic"),
    "font_bold": ("Arial", 10, "bold"),
    "font_thumb_num": ("Arial", 9, "bold"),
    "font_placeholder": ("Arial", 14, "italic"),
    "font_footer": ("Arial", 8),
    # Sliders
    "slider_canvas_range": (200, 600),
    "slider_thumb_range": (40, 120),
    "slider_length": 140,
    "slider_width": 12,
    # Buttons
    "btn_reset_size": {"width": 90, "height": 36, "radius": 8},
    "btn_create_size": {"width": 110, "height": 36, "radius": 8},
    "btn_theme_size": {"width": 85, "height": 36, "radius": 8},
    "btn_dialog_yesno_size": {"width": 80, "height": 32, "radius": 6},
    "btn_dialog_ok_size": {"width": 90, "height": 32, "radius": 6},
    # Footer
    "footer_text": {"text": "© 2026 Image to PDF  •  Developed with ❤️ by Veeshel Khundrakpam"},
    "footer_link": "https://github.com/vslkhun",
    # Colors independent of light/dark themes
    "btn_reset_bg": "#9b2118",
    "btn_reset_hover": "#b62f28",
    "btn_create_bg": "#1D9E21",
    "btn_create_hover": "#10a018",
}

class RoundedButton(tk.Canvas):
    """Custom Canvas-drawn Button with rounded corners and smooth hover states."""

    def __init__(
        self,
        parent,
        text="",
        command=None,
        radius=8,
        bg_color="#1D9E21",
        hover_color="#10a018",
        text_color="#ffffff",
        font=("Arial", 10, "bold"),
        width=36,
        height=32,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            **kwargs,
        )
        self.command = command
        self.radius = radius
        self.normal_bg = bg_color
        self.hover_bg = hover_color
        self.text_color = text_color
        self.font = font
        self.text = text

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, event=None, color=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = min(self.radius, h // 2, w // 2)
        fill_color = color or self.normal_bg

        if w <= 1 or h <= 1:
            return

        self.create_arc(
            0, 0, 2 * r, 2 * r, start=90, extent=90, fill=fill_color, outline=fill_color
        )
        self.create_arc(
            w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=fill_color, outline=fill_color
        )
        self.create_arc(
            0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=fill_color, outline=fill_color
        )
        self.create_arc(
            w - 2 * r,
            h - 2 * r,
            w,
            h,
            start=270,
            extent=90,
            fill=fill_color,
            outline=fill_color,
        )
        self.create_polygon(
            r, 0, w - r, 0, w - r, h, r, h, fill=fill_color, outline=fill_color
        )
        self.create_polygon(
            0, r, w, r, w, h - r, 0, h - r, fill=fill_color, outline=fill_color
        )
        self.create_text(
            w // 2, h // 2, text=self.text, fill=self.text_color, font=self.font
        )

    def _on_enter(self, e):
        self._draw(color=self.hover_bg)

    def _on_leave(self, e):
        self._draw(color=self.normal_bg)

    def _on_click(self, e):
        if self.command:
            self.command()

    def update_colors(
        self, parent_bg, bg_color=None, hover_color=None, text_color=None
    ):
        self.configure(bg=parent_bg)
        if bg_color:
            self.normal_bg = bg_color
        if hover_color:
            self.hover_bg = hover_color
        if text_color:
            self.text_color = text_color
        self._draw()

class CustomScrollbar(tk.Canvas):
    """Custom, theme-matching horizontal scrollbar."""

    def __init__(self, parent, command=None, track_color="#2d2d2d", thumb_color="#555555", height=10, **kwargs):
        super().__init__(
            parent,
            height=height,
            bg=track_color,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            **kwargs,
        )
        self.command = command
        self.track_color = track_color
        self.thumb_color = thumb_color
        self.first = 0.0
        self.last = 1.0

        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

    def set(self, first, last):
        """Update position based on linked Canvas xscrollcommand."""
        self.first = float(first)
        self.last = float(last)
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 1 or h <= 1:
            return

        x0 = w * self.first
        x1 = w * self.last

        # Track background
        self.create_rectangle(0, 0, w, h, fill=self.track_color, outline="")

        # Thumb Pill
        if (x1 - x0) < w:
            r = min(4, h // 2)
            self.create_rectangle(x0 + r, 1, x1 - r, h - 1, fill=self.thumb_color, outline="")
            self.create_oval(x0, 1, x0 + 2 * r, h - 1, fill=self.thumb_color, outline="")
            self.create_oval(x1 - 2 * r, 1, x1, h - 1, fill=self.thumb_color, outline="")

    def _on_click(self, event):
        self._scroll_to(event.x)

    def _on_drag(self, event):
        self._scroll_to(event.x)

    def _scroll_to(self, mouse_x):
        w = self.winfo_width()
        if w > 0 and self.command:
            fraction = max(0.0, min(1.0, mouse_x / w))
            self.command("moveto", fraction)

    def update_colors(self, track_color, thumb_color):
        """Updates scrollbar colors when switching themes."""
        self.track_color = track_color
        self.thumb_color = thumb_color
        self.configure(bg=track_color)
        self._draw()

class CustomDialog(tk.Toplevel):
    """A theme-aware replacement for tkinter.messagebox."""

    def __init__(
        self,
        parent,
        title,
        message,
        dialog_type="info",
        colors=None,
        dark_title_bar_func=None,
    ):
        super().__init__(parent)
        self.result = False
        self.colors = colors or THEMES["light"]

        self.title(title)
        self.resizable(False, False)
        self.configure(bg=self.colors["bg"])

        # Prevent modal window flickering while calculating geometry
        # self.withdraw()

        # Update parent layout geometry math
        parent.update_idletasks()

        dialog_w, dialog_h = 380, 180
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()

        # Calculate exact center offset relative to the main app window
        center_x = parent_x + (parent_w // 2) - (dialog_w // 2)
        center_y = parent_y + (parent_h // 2) - (dialog_h // 2)

        self.geometry(f"{dialog_w}x{dialog_h}+{center_x}+{center_y}")
        self.deiconify()

        # Focus modal binding
        self.transient(parent)
        self.grab_set()

        # Apply dark title bar to popup if in dark mode
        if dark_title_bar_func and self.colors["bg"] == "#1e1e1e":
            dark_title_bar_func(self, dark=True)

        # Message Text
        lbl_msg = tk.Label(
            self,
            text=message,
            font=("Arial", 10),
            bg=self.colors["bg"],
            fg=self.colors["text"],
            wraplength=340,
            justify="center",
        )
        lbl_msg.pack(expand=True, fill=tk.BOTH, padx=20, pady=(20, 10))

        # Button Container
        btn_frame = tk.Frame(self, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, pady=(0, 20))

        if dialog_type == "yesno":
            btn_yes = RoundedButton(
                btn_frame,
                text="Yes",
                command=self._on_yes,
                bg_color="#1D9E21",
                hover_color="#10a018",
                text_color="white",
                radius=6,
                width=80,
                height=32,
            )
            btn_yes.pack(side=tk.RIGHT, padx=(5, 20))

            btn_no = RoundedButton(
                btn_frame,
                text="No",
                command=self._on_no,
                bg_color="#9b2118",
                hover_color="#b62f28",
                text_color="white",
                radius=6,
                width=80,
                height=32,
            )
            btn_no.pack(side=tk.RIGHT, padx=5)
        else: # info, warning, error
            btn_color = "#9b2118" if dialog_type == "error" else "#0078d7"
            btn_hover = "#b62f28" if dialog_type == "error" else "#005a9e"

            btn_ok = RoundedButton(
                btn_frame,
                text="OK",
                command=self._on_yes,
                bg_color=btn_color,
                hover_color=btn_hover,
                text_color="white",
                radius=6,
                width=90,
                height=32,
            )
            # btn_ok.pack(side=tk.CENTER)
            btn_ok.pack(anchor="center")

        self.wait_window()

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()