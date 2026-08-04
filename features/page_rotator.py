
class PageRotatorFeature:
    """Standalone feature to rotate the currently selected page."""

    def __init__(self, main_app):
        # Store reference to main ImageToPdfApp instance
        self.app = main_app

    def rotate_selected(self, degrees=90):
        """Rotates the image at the selected index and updates the UI."""
        idx = self.app.selected_index
        if idx is None or not (0 <= idx < len(self.app.image_list)):
            self.app.show_warning("No Selection", "Please select an image to rotate!")
            return

        # Save state for Ctrl+Z undo support
        self.app.save_snapshot()

        # Rotate PIL image
        img = self.app.image_list[idx]
        rotated_img = img.rotate(-degrees, expand=True)  # Clockwise rotation
        self.app.image_list[idx] = rotated_img

        # Refresh UI for this thumbnail and main canvas
        self.app.rebuild_single_thumbnail(idx)
        self.app.update_main_canvas(rotated_img)
        self.app.refresh_thumbnail_layout()
