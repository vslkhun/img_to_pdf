import tkinter as tk
from PIL import Image, ImageEnhance, ImageTk


class ImageCropperFeature:
    """Direct-canvas cropping module with keyboard shortcuts (Enter/ESC) and translucent selection."""

    def __init__(self, main_app):
        self.app = main_app
        self.is_active = False

        # Selection coordinates relative to main canvas viewport
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        # Canvas overlay item IDs
        self.rect_id = None
        self.overlay_img_tk = None

    def toggle_crop_mode(self, event=None):
        """Activates or toggles direct canvas crop mode."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to crop!")
            return "break"

        if self.is_active:
            self.cancel_crop()
        else:
            self.start_crop_mode()

        return "break"

    def start_crop_mode(self):
        """Enables interactive cropping on the main workspace canvas."""
        self.is_active = True
        self.start_x = self.start_y = self.end_x = self.end_y = None

        # Bind temporary crop controls to main canvas and window
        self.app.canvas.config(cursor="crosshair")
        self.app.canvas.bind("<ButtonPress-1>", self._on_start_drag)
        self.app.canvas.bind("<B1-Motion>", self._on_dragging)

        # Bind Escape & Enter keys globally while in crop mode
        self.app.root.bind("<Escape>", lambda e: self.cancel_crop())
        self.app.root.bind("<Return>", lambda e: self.apply_crop())
        self.app.root.bind("<KP_Enter>", lambda e: self.apply_crop())

        self.app.info_label.config(
            text="✂️ CROP MODE: Click & Drag to select | Press ENTER to apply | Press ESC to cancel",
            fg="#1F9E21",
        )

    def _on_start_drag(self, event):
        if not self.is_active:
            return

        self.start_x = event.x
        self.start_y = event.y
        self.end_x = event.x
        self.end_y = event.y

        self._clear_drawings()

    def _on_dragging(self, event):
        if not self.is_active or self.start_x is None:
            return

        self.end_x = event.x
        self.end_y = event.y

        self._render_translucent_box()

    def _render_translucent_box(self):
        """Draws a translucent grey overlay inside the crop region on top of the image."""
        self._clear_drawings()

        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        y1, y2 = min(self.start_y, self.end_y), max(self.start_y, self.end_y)

        w = x2 - x1
        h = y2 - y1

        if w < 5 or h < 5:
            return

        # 1. Generate translucent grey box using PIL Alpha layer
        # RGBA: Dark grey (50, 50, 50) with 120/255 opacity (~47% translucent)
        grey_overlay = Image.new("RGBA", (w, h), (50, 50, 50, 120))
        self.overlay_img_tk = ImageTk.PhotoImage(grey_overlay)

        # 2. Draw overlay image and outline on Tkinter Canvas
        self.app.canvas.create_image(
            x1, y1, image=self.overlay_img_tk, anchor="nw", tags="crop_overlay"
        )
        self.rect_id = self.app.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="#ffffff",
            width=2,
            dash=(4, 4),
            tags="crop_overlay",
        )

    def apply_crop(self):
        """Calculates actual crop box relative to original source image and crops."""
        if not self.is_active:
            return

        idx = self.app.selected_index
        if (
            idx is None
            or self.start_x is None
            or self.end_x is None
            or None in (self.start_x, self.start_y, self.end_x, self.end_y)
        ):
            self.cancel_crop()
            return

        x1, x2 = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        y1, y2 = min(self.start_y, self.end_y), max(self.start_y, self.end_y)

        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.cancel_crop()
            return


        # Fetch original full-res image and main canvas item bounding box
        orig_img = self.app.image_list[idx]
        img_bbox = self.app.canvas.bbox("img")  # (left, top, right, bottom) on canvas

        if not img_bbox:
            self.cancel_crop()
            return

        canvas_img_left, canvas_img_top, canvas_img_right, canvas_img_bottom = img_bbox
        disp_w = canvas_img_right - canvas_img_left
        disp_h = canvas_img_bottom - canvas_img_top

        # Clamp selection to display image boundaries
        crop_canvas_left = max(x1, canvas_img_left) - canvas_img_left
        crop_canvas_top = max(y1, canvas_img_top) - canvas_img_top
        crop_canvas_right = min(x2, canvas_img_right) - canvas_img_left
        crop_canvas_bottom = min(y2, canvas_img_bottom) - canvas_img_top

        # Scale factor mapping canvas pixels back to high-res PIL pixels
        scale_x = orig_img.width / float(disp_w)
        scale_y = orig_img.height / float(disp_h)

        real_crop_box = (
            int(crop_canvas_left * scale_x),
            int(crop_canvas_top * scale_y),
            int(crop_canvas_right * scale_x),
            int(crop_canvas_bottom * scale_y),
        )

        # Apply crop
        self.app.save_snapshot()
        cropped_img = orig_img.crop(real_crop_box)

        self.app.image_list[idx] = cropped_img
        self.cancel_crop()

        # Update UI displays
        self.app.rebuild_single_thumbnail(idx)
        self.app.update_main_canvas(cropped_img)
        self.app.refresh_thumbnail_layout()

    def cancel_crop(self):
        """Exits crop mode and restores normal main canvas bindings."""
        self.is_active = False
        self._clear_drawings()

        # Restore default canvas bindings & cursor
        self.app.canvas.config(cursor="")
        self.app.canvas.bind("<ButtonPress-1>", self.app.on_pan_start)
        self.app.canvas.bind("<B1-Motion>", self.app.on_panning)

        # Unbind temp Escape and Enter keys
        self.app.root.unbind("<Escape>")
        self.app.root.unbind("<Return>")
        self.app.root.unbind("<KP_Enter>")

        # Restore normal info label text
        self.app.info_label.config(
            text="Press 'Delete' key or Right-Click a thumbnail to remove it.",
            fg=self.app.colors["subtext"],
        )

    def _clear_drawings(self):
        """Removes overlay elements from canvas."""
        self.app.canvas.delete("crop_overlay")
        self.overlay_img_tk = None
        self.rect_id = None
