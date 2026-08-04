from PIL import Image, ImageOps

class ColorInverterFeature:
    """Standalone feature to handle Invert, Grayscale, and Reset to Original operations."""

    def __init__(self, main_app):
        self.app = main_app

    def invert_selected(self):
        """Inverts the colors of the currently selected image."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to invert colors!")
            return

        self.app.save_snapshot()

        orig_img = self.app.image_list[idx]
        rgb_img = orig_img.convert("RGB") if orig_img.mode != "RGB" else orig_img

        inverted_img = ImageOps.invert(rgb_img)
        self.app.image_list[idx] = inverted_img

        self.app.rebuild_single_thumbnail(idx)
        self.app.update_main_canvas(inverted_img)
        self.app.refresh_thumbnail_layout()

    def grayscale_selected(self):
        """Converts the currently selected image to Grayscale (B&W)."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to convert to grayscale!")
            return

        self.app.save_snapshot()

        orig_img = self.app.image_list[idx]
        # Convert to 'L' (Grayscale) and then back to 'RGB' so Pillow/Tkinter handles rendering smoothly
        grayscale_img = orig_img.convert("L").convert("RGB")

        self.app.image_list[idx] = grayscale_img

        self.app.rebuild_single_thumbnail(idx)
        self.app.update_main_canvas(grayscale_img)
        self.app.refresh_thumbnail_layout()

    def restore_original_selected(self):
        """Restores the selected image back to its original unmodified state."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to reset!")
            return

        # Fetch stored original backup copy from thumb_data
        original_backup = self.app.thumb_data[idx].get("original_copy")
        if original_backup is None:
            self.app.show_warning("Restore Failed", "No original backup found for this image.")
            return

        self.app.save_snapshot()

        # Restore a clean deep copy of the original source
        restored_img = original_backup.copy()
        self.app.image_list[idx] = restored_img

        self.app.rebuild_single_thumbnail(idx)
        self.app.update_main_canvas(restored_img)
        self.app.refresh_thumbnail_layout()
