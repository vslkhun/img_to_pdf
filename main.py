import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
import os

class ImageToPdfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to PDF Creator")
        self.root.geometry("800x600")
        self.root.configure(bg="#f5f5f5")

        # Core data storage
        self.image_list = []      # Stores original PIL Images in order
        self.thumbnail_list = []  # Stores Tkinter PhotoImage references for display
        self.thumb_labels = []    # Stores the widget references in the bottom bar
        self.selected_index = None # Tracks which thumbnail is clicked for deletion

        self.setup_ui()
        
        # Bind the global paste event (Ctrl+V) to the window
        self.root.bind("<Control-v>", self.handle_paste)
        self.root.bind("<Control-V>", self.handle_paste)

    def setup_ui(self):
        # --- Top Area: Instructions & Main Canvas ---
        instruction_label = tk.Label(
            self.root, 
            text="Click inside the canvas and press Ctrl+V to paste an image", 
            font=("Arial", 11), bg="#f5f5f5", fg="#555"
        )
        instruction_label.pack(pady=10)

        # Canvas for pasting
        self.canvas = tk.Canvas(self.root, width=500, height=300, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack(pady=10)
        
        # Draw placeholder text in canvas
        self.canvas_text = self.canvas.create_text(
            250, 150, 
            text="[ Paste Image Here ]", 
            fill="#aaa", font=("Arial", 14, "italic")
        )
        
        # Allow clicking canvas to focus it (helps ensure paste events capture cleanly)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())

        # --- Middle Area: Delete Action Info ---
        self.info_label = tk.Label(
            self.root, 
            text="Click a thumbnail below to select it, then press 'Delete' key or right-click to remove.", 
            font=("Arial", 9, "italic"), bg="#f5f5f5", fg="#777"
        )
        self.info_label.pack(pady=5)

        # --- Bottom Area: Thumbnail Tracker Scrollbar Frame ---
        self.thumb_outer_frame = tk.Frame(self.root, bg="#e0e0e0", height=120)
        self.thumb_outer_frame.pack(fill=tk.X, padx=20, pady=10)
        self.thumb_outer_frame.pack_propagate(False) # Keep fixed height

        # Canvas + Scrollbar setup for horizontal scrolling thumbnails
        self.thumb_canvas = tk.Canvas(self.thumb_outer_frame, bg="#e0e0e0", height=100, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.thumb_outer_frame, orient="horizontal", command=self.thumb_canvas.xview)
        self.thumb_inner_frame = tk.Frame(self.thumb_canvas, bg="#e0e0e0")

        self.thumb_inner_frame.bind(
            "<Configure>", 
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        )
        self.thumb_canvas.create_window((0, 0), window=self.thumb_inner_frame, anchor="nw")
        self.thumb_canvas.configure(xscrollcommand=self.scrollbar.set)

        self.thumb_canvas.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.scrollbar.pack(fill=tk.X, side=tk.BOTTOM)

        # --- Footer Area: Control Buttons ---
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(pady=20)
        self.btn_create = tk.Button(
            btn_frame, text="Create PDF", font=("Arial", 11, "bold"), 
            bg="#4CAF50", fg="white", padx=15, pady=5, command=self.create_pdf
        )
        self.btn_create.pack(side=tk.LEFT, padx=15)

        self.btn_reset = tk.Button(
            btn_frame, text="Reset All", font=("Arial", 11), 
            bg="#f44336", fg="white", padx=15, pady=5, command=self.reset_all
        )
        self.btn_reset.pack(side=tk.LEFT, padx=15)

    def handle_paste(self, event=None):
        try:
            # Grab image data directly from system clipboard
            img = ImageGrab.grabclipboard()
            
            if isinstance(img, Image.Image):
                # We have a valid PIL Image instance from clipboard
                self.process_and_store_image(img)
            elif isinstance(img, list):
                # In some OS environments, grabbing clipboard returns a list of file paths instead
                for path in img:
                    if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        file_img = Image.open(path)
                        self.process_and_store_image(file_img)
            else:
                messagebox.showwarning("Paste Failed", "No valid image found in clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste image: {str(e)}")

    def process_and_store_image(self, pil_img):
        # Clear canvas default placeholder text on first paste
        if not self.image_list:
            self.canvas.delete(self.canvas_text)

        # 1. Store original copy (convert to RGB right away for easy PDF compiling later)
        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
        self.image_list.append(pil_img)

        # 2. Update Central Canvas View to display the most recently pasted image
        display_img = pil_img.copy()
        display_img.thumbnail((500, 300))
        self.current_canvas_tk = ImageTk.PhotoImage(display_img)
        self.canvas.delete("all") # Clear previous main view image
        self.canvas.create_image(250, 150, image=self.current_canvas_tk, anchor=tk.CENTER)

        # 3. Refresh the thumbnail tray
        self.refresh_thumbnails()

    def refresh_thumbnails(self):
        # Destory existing widgets inside the thumbnail strip frame
        for widget in self.thumb_inner_frame.winfo_children():
            widget.destroy()
        
        self.thumb_labels.clear()
        self.thumbnail_list.clear()

        # Re-populate the frame using current image state array
        for idx, orig_img in enumerate(self.image_list):
            # Create a thumbnail sized copy
            thumb_img = orig_img.copy()
            thumb_img.thumbnail((70, 70))
            tk_thumb = ImageTk.PhotoImage(thumb_img)
            self.thumbnail_list.append(tk_thumb) # preserve reference

            # Container widget for Thumbnail + Number stack
            item_frame = tk.Frame(self.thumb_inner_frame, bg="#e0e0e0", bd=2, relief=tk.FLAT)
            item_frame.pack(side=tk.LEFT, padx=8, pady=5)

            # Display Thumbnail image label
            lbl_img = tk.Label(item_frame, image=tk_thumb, bg="white")
            lbl_img.pack()

            # Display ordering index label (1-indexed for users)
            lbl_num = tk.Label(item_frame, text=f"#{idx + 1}", font=("Arial", 9, "bold"), bg="#e0e0e0")
            lbl_num.pack()

            # Highlight layout if this item is currently selected
            if self.selected_index == idx:
                item_frame.config(relief=tk.SOLID, bg="#0078d7")
                lbl_num.config(bg="#0078d7", fg="white")

            # Bind mouse clicks to select the thumbnail for removal
            # Bind events across all sub-components of the thumbnail frame item
            for widget in (item_frame, lbl_img, lbl_num):
                widget.bind("<Button-1>", lambda e, index=idx: self.select_thumbnail(index))
                widget.bind("<Button-3>", lambda e, index=idx: self.delete_thumbnail(index)) # Right click deletes

        # Make sure layout automatically shifts into view if row gets wide
        self.thumb_canvas.yview_moveto(0)

    def select_thumbnail(self, index):
        self.selected_index = index
        self.refresh_thumbnails()
        # Bind the keyboard Delete key to instantly wipe selected index out
        self.root.bind("<Delete>", lambda event: self.delete_thumbnail(self.selected_index))

    def delete_thumbnail(self, index):
        if index is not None and 0 <= index < len(self.image_list):
            del self.image_list[index]
            self.selected_index = None
            self.root.unbind("<Delete>")
            
            # Reset Central Canvas look if last item was removed completely
            if not self.image_list:
                self.canvas.delete("all")
                self.canvas_text = self.canvas.create_text(250, 150, text="[ Paste Image Here ]", fill="#aaa", font=("Arial", 14, "italic"))
            else:
                # Fallback central window visualization to the new last item 
                last_img = self.image_list[-1].copy()
                last_img.thumbnail((500, 300))
                self.current_canvas_tk = ImageTk.PhotoImage(last_img)
                self.canvas.delete("all")
                self.canvas.create_image(250, 150, image=self.current_canvas_tk, anchor=tk.CENTER)

            self.refresh_thumbnails()

    def create_pdf(self):
        if not self.image_list:
            messagebox.showwarning("Empty", "No images pasted yet to generate a PDF!")
            return

        # Prompt user to choose save destination file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Compiled PDF As"
        )
        
        if not file_path:
            return # User canceled saving dialog box

        try:
            # Pillow natively converts an image list sequence into an ordered Multi-page PDF layout
            first_image = self.image_list[0]
            subsequent_images = self.image_list[1:]
            
            first_image.save(
                file_path,
                save_all=True,
                append_images=subsequent_images
            )
            messagebox.showinfo("Success", f"PDF successfully created with {len(self.image_list)} images!\nSaved to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF structural profile:\n{str(e)}")

    def reset_all(self):
        if not self.image_list:
            return
            
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to clear all images?"):
            self.image_list.clear()
            self.thumbnail_list.clear()
            self.thumb_labels.clear()
            self.selected_index = None
            self.root.unbind("<Delete>")
            
            # Clear canvas layout elements back to original state
            self.canvas.delete("all")
            self.canvas_text = self.canvas.create_text(250, 150, text="[ Paste Image Here ]", fill="#aaa", font=("Arial", 14, "italic"))
            
            # Destory visual items inside container block
            for widget in self.thumb_inner_frame.winfo_children():
                widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToPdfApp(root)
    root.mainloop()
