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
        "card_selected": "#0078d7",
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
        "card_selected": "#0078d7",
        "card_text": "#ffffff",
        "card_text_selected": "#ffffff",
        "border": "#3c3c3c",
        "btn_theme_bg": "#e0e0e0",
        "btn_theme_hover": "#ffffff",
        "btn_theme_fg": "#000000",
        "scrollbar_track": "#2d2d2d",
        "scrollbar_thumb": "#555555",
    },
}


class RoundedButton(tk.Canvas):
    """Custom Canvas-drawn Button with rounded corners and smooth hover states."""

    def __init__(
        self,
        parent,
        text="",
        command=None,
        radius=8,
        bg_color="#4CAF50",
        hover_color="#45a049",
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

