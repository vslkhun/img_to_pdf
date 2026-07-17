import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
import os

# Import drag-and-drop architecture extensions
from tkinterdnd2 import TkinterDnD, DND_FILES

# Import PDF conversion engine and system exception guardrails
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

class ImageToPdfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to PDF Creator")
        self.root.geometry("950x700")
        self.root.minsize(700, 500)
        self.root.configure(bg="#f5f5f5")

        # Configure root grid weights for responsiveness
        self.root.columnconfigure(0, weight=0) # Sidebar panel stays fixed width
        self.root.columnconfigure(1, weight=1) # Main workspace scales horizontally
        self.root.rowconfigure(0, weight=1)    # Dynamic height distribution

        # Core data storage
        self.image_list = []       
        self.thumb_data = []       
        self.selected_index = None  
        self.dragged_index = None   

        # User-adjustable size parameters
        self.canvas_size = 350     # Height/width bounding square for canvas
        self.thumb_size = 70       # Height/width bounding square for thumbnails
        self.zoom_scale = 1.0      # Current zoom factor for the main canvas image

        self.setup_ui()
        
        # Bind global paste events
        self.root.bind("<Control-v>", self.handle_paste)
        self.root.bind("<Control-V>", self.handle_paste)

        # Register entire window surface layout map to receive dropped files
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)

    def setup_ui(self):
        # =====================================================================
        # LEFT PANEL: Control Sidebar (Dynamic Scale & Reset Controls)
        # =====================================================================
        self.sidebar = tk.Frame(self.root, bg="#e8e8e8", width=200, padx=15, pady=15, bd=1, relief=tk.SOLID)
        self.sidebar.grid(row=0, column=0, sticky="nws")
        self.sidebar.grid_propagate(False)

        side_title = tk.Label(self.sidebar, text="Layout Controls", font=("Arial", 12, "bold"), bg="#e8e8e8")
        side_title.pack(pady=(0, 15))

        # Canvas Size Slider
        tk.Label(self.sidebar, text="Canvas Preview Size:", font=("Arial", 10), bg="#e8e8e8").pack(anchor="w")
        self.canvas_slider = tk.Scale(self.sidebar, from_=200, to=600, orient=tk.HORIZONTAL, bg="#e8e8e8", highlightthickness=0)
        self.canvas_slider.set(self.canvas_size)
        self.canvas_slider.pack(fill=tk.X, pady=(0, 15))
        self.canvas_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Thumbnail Size Slider
        tk.Label(self.sidebar, text="Thumbnail Size:", font=("Arial", 10), bg="#e8e8e8").pack(anchor="w")
        self.thumb_slider = tk.Scale(self.sidebar, from_=40, to=120, orient=tk.HORIZONTAL, bg="#e8e8e8", highlightthickness=0)
        self.thumb_slider.set(self.thumb_size)
        self.thumb_slider.pack(fill=tk.X, pady=(0, 30))
        self.thumb_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Bottom Actions in Sidebar
        self.btn_create = tk.Button(self.sidebar, text="Create PDF", font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", pady=6, command=self.create_pdf)
        self.btn_create.pack(fill=tk.X, pady=8)

        self.btn_reset = tk.Button(self.sidebar, text="Reset All", font=("Arial", 11), bg="#f44336", fg="white", pady=6, command=self.reset_all)
        self.btn_reset.pack(fill=tk.X, pady=8)

        # =====================================================================
        # RIGHT PANEL: Main Dynamic Workspace
        # =====================================================================
        self.workspace = tk.Frame(self.root, bg="#f5f5f5", padx=15, pady=10)
        self.workspace.grid(row=0, column=1, sticky="nsew")
        
        # Grid weights inside workspace
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(1, weight=1) # The canvas grid square expands vertically

        # Instructions
        instruction_label = tk.Label(
            self.workspace, 
            text="Drop Image/PDF / Ctrl+V to Paste | Click thumbnail to view | Drag thumbnails to reorder", 
            font=("Arial", 11), bg="#f5f5f5", fg="#555"
        )
        instruction_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        # Interactive Canvas Preview Box
        self.canvas = tk.Canvas(self.workspace, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=5)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        # Bind structural canvas scaling triggers to window size updates
        self.canvas.bind("<Configure>", self.respond_to_canvas_resize)

        # Bind zoom triggers specifically when hovering over the canvas surface area
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)

        # Info line
        self.info_label = tk.Label(self.workspace, text="Press 'Delete' key or Right-Click a thumbnail to remove it.", font=("Arial", 9, "italic"), bg="#f5f5f5", fg="#777")
        self.info_label.grid(row=2, column=0, pady=2, sticky="ew")

        # =====================================================================
        # BOTTOM TRAY: Scrollable Thumbnail Shelf
        # =====================================================================
        # Outer container frame
        self.thumb_outer_frame = tk.Frame(self.workspace, bg="#e0e0e0", height=150, bd=1, relief=tk.SUNKEN)
        self.thumb_outer_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.thumb_outer_frame.grid_propagate(False)

        # Set weights for tray items to move fluidly
        self.thumb_outer_frame.columnconfigure(0, weight=1)
        self.thumb_outer_frame.rowconfigure(0, weight=1)

        self.thumb_canvas = tk.Canvas(self.thumb_outer_frame, bg="#e0e0e0", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.thumb_outer_frame, orient="horizontal", command=self.thumb_canvas.xview)
        
        self.thumb_inner_frame = tk.Frame(self.thumb_canvas, bg="#e0e0e0")
        self.thumb_inner_frame.bind("<Configure>", lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all")))
        
        self.thumb_canvas.create_window((0, 0), window=self.thumb_inner_frame, anchor="nw")
        self.thumb_canvas.configure(xscrollcommand=self.scrollbar.set)

        self.thumb_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind scroll wheel event tracking directly to the scroll viewport container frame
        self.thumb_canvas.bind("<MouseWheel>", self.on_mousewheel)

        # Init workspace strings
        self.canvas_text = None
        self.draw_placeholder()

    def draw_placeholder(self):
        if not self.image_list:
            self.canvas.delete("all")
            w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 500
            h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 350
            self.canvas_text = self.canvas.create_text(w//2, h//2, text="[ Drop Image/PDF or Paste Here ]", fill="#aaa", font=("Arial", 14, "italic"))

    def on_layout_slider_change(self, event=None):
        """Monitors modifications made to the sizes via the scale sliders."""
        self.canvas_size = self.canvas_slider.get()
        self.thumb_size = self.thumb_slider.get()
        
        # Dynamically bump the bottom frame layout height up/down based on thumbnail settings
        self.thumb_outer_frame.config(height=self.thumb_size + 75)
        
        # Regenerate display calculations
        self.rebuild_thumbnails_cache()
        if self.selected_index is not None:
            self.update_main_canvas(self.image_list[self.selected_index])
        self.refresh_thumbnail_layout()

    def respond_to_canvas_resize(self, event):
        """Triggers every time the user stretches the main application window window frames."""
        if not self.image_list:
            self.draw_placeholder()
        elif self.selected_index is not None:
            self.update_main_canvas(self.image_list[self.selected_index])

    def handle_paste(self, event=None):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.process_and_store_image(img)
            elif isinstance(img, list):
                for path in img:
                    if os.path.isfile(path):
                        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                            self.process_and_store_image(Image.open(path))
                        elif path.lower().endswith('.pdf'):
                            self.load_pdf_pages(path)
            else:
                messagebox.showwarning("Paste Failed", "No valid image or file path found in clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste element: {str(e)}")

    def process_and_store_image(self, pil_img):
        if not self.image_list:
            self.canvas.delete(self.canvas_text)

        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
            
        self.image_list.append(pil_img)
        
        # Create corresponding image cache block array
        idx = len(self.image_list) - 1
        item_frame = tk.Frame(self.thumb_inner_frame, bg="#e0e0e0", bd=2, relief=tk.FLAT)
        lbl_img = tk.Label(item_frame, bg="white")
        lbl_img.pack()
        lbl_num = tk.Label(item_frame, text="", font=("Arial", 9, "bold"), bg="#e0e0e0")
        lbl_num.pack()

        self.thumb_data.append({
            'frame': item_frame,
            'lbl_img': lbl_img,
            'lbl_num': lbl_num,
            'tk_thumb': None # Set dynamically in cache builder
        })

        self.rebuild_single_thumbnail(idx)
        self.selected_index = idx
        self.zoom_scale = 1.0 # Reset zoom level on a fresh addition
        self.update_main_canvas(pil_img)
        self.refresh_thumbnail_layout()

    def rebuild_single_thumbnail(self, idx):
        """Re-scales a single element thumbnail asset without impacting structural layout maps."""
        orig_img = self.image_list[idx]
        thumb_img = orig_img.copy()
        thumb_img.thumbnail((self.thumb_size, self.thumb_size))
        tk_thumb = ImageTk.PhotoImage(thumb_img)
        
        data = self.thumb_data[idx]
        data['tk_thumb'] = tk_thumb
        data['lbl_img'].config(image=tk_thumb)

    def rebuild_thumbnails_cache(self):
        """Re-scales all elements inside the current sequence storage line arrays."""
        for idx in range(len(self.image_list)):
            self.rebuild_single_thumbnail(idx)

    def update_main_canvas(self, pil_img):
        """Scales active selection down/up to natively fit current window grid geometry sizes."""
        self.root.update_idletasks() # Refresh structural bounds mappings
        cw = self.canvas.winfo_width() - 10
        ch = self.canvas.winfo_height() - 10
        
        # Prevent boundary collapse
        cw = max(cw, 100)
        ch = max(ch, 100)

        # Respect user explicit scaling controls bound settings limiters
        max_w = min(cw, self.canvas_size * 1.5)
        max_h = min(ch, self.canvas_size)

        # Apply the cumulative mouse zoom multiplier bounds factor
        final_w = int(max_w * self.zoom_scale)
        final_h = int(max_h * self.zoom_scale)

        # Keep resolution bounded to avoid memory crashes on extreme zooms
        final_w = max(min(final_w, 3000), 20)
        final_h = max(min(final_h, 3000), 20)

        display_img = pil_img.copy()
        display_img.thumbnail((final_w, final_h))
        self.current_canvas_tk = ImageTk.PhotoImage(display_img)
        
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.current_canvas_tk, anchor=tk.CENTER)

    def refresh_thumbnail_layout(self):
        for data in self.thumb_data:
            data['frame'].pack_forget()

        for idx, data in enumerate(self.thumb_data):
            data['frame'].pack(side=tk.LEFT, padx=8, pady=5)
            data['lbl_num'].config(text=f"#{idx + 1}")

            if self.selected_index == idx:
                data['frame'].config(relief=tk.SOLID, bg="#0078d7")
                data['lbl_num'].config(bg="#0078d7", fg="white")
            else:
                data['frame'].config(relief=tk.FLAT, bg="#e0e0e0")
                data['lbl_num'].config(bg="#e0e0e0", fg="black")

            for w in (data['frame'], data['lbl_img'], data['lbl_num']):
                w.bind("<Button-1>", lambda e, index=idx: self.select_thumbnail(index))
                w.bind("<Button-3>", lambda e, index=idx: self.delete_thumbnail(index))
                w.bind("<ButtonPress-1>", lambda e, index=idx: self.on_drag_start(index), add="+")
                w.bind("<B1-Motion>", lambda e, index=idx: self.on_dragging(e, index))

    def select_thumbnail(self, index):
        self.selected_index = index
        self.zoom_scale = 1.0 # Reset zoom to baseline when swapping target selections
        self.update_main_canvas(self.image_list[index])
        self.refresh_thumbnail_layout()
        self.root.bind("<Delete>", lambda event: self.delete_thumbnail(self.selected_index))

    def on_drag_start(self, index):
        self.dragged_index = index

    def on_dragging(self, event, index):
        if self.dragged_index is None:
            return
        
        widget = event.widget
        if isinstance(widget, str):
            widget = self.root.nametowidget(widget)
            
        x_on_inner_frame = event.x + widget.winfo_x() + widget.master.winfo_x()
        
        for target_idx, data in enumerate(self.thumb_data):
            child = data['frame']
            child_x = child.winfo_x()
            child_width = child.winfo_width()
            
            if child_x <= x_on_inner_frame <= (child_x + child_width):
                if target_idx != self.dragged_index:
                    # Sync Image List
                    img = self.image_list.pop(self.dragged_index)
                    self.image_list.insert(target_idx, img)
                    
                    # Sync Widget Mapping Data Dictionary
                    frame_data = self.thumb_data.pop(self.dragged_index)
                    self.thumb_data.insert(target_idx, frame_data)
                    
                    if self.selected_index == self.dragged_index:
                        self.selected_index = target_idx
                    elif self.selected_index == target_idx:
                        self.selected_index = self.dragged_index
                        
                    self.dragged_index = target_idx
                    self.refresh_thumbnail_layout()
                break

    def delete_thumbnail(self, index):
        if index is not None and 0 <= index < len(self.image_list):
            del self.image_list[index]
            self.thumb_data[index]['frame'].destroy()
            del self.thumb_data[index]
            
            self.selected_index = None
            self.root.unbind("<Delete>")
            
            if not self.image_list:
                self.draw_placeholder()
            else:
                self.selected_index = len(self.image_list) - 1
                self.zoom_scale = 1.0
                self.update_main_canvas(self.image_list[self.selected_index])

            self.refresh_thumbnail_layout()

    def create_pdf(self):
        if not self.image_list:
            messagebox.showwarning("Empty", "No images pasted yet to generate a PDF!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Compiled PDF As"
        )
        if not file_path:
            return

        try:
            first_image = self.image_list[0]
            subsequent_images = self.image_list[1:]
            first_image.save(file_path, save_all=True, append_images=subsequent_images)
            messagebox.showinfo("Success", f"PDF created successfully with {len(self.image_list)} images!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF:\n{str(e)}")

    def reset_all(self):
        if not self.image_list:
            return
            
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to clear all images?"):
            self.image_list.clear()
            for data in self.thumb_data:
                data['frame'].destroy()
            self.thumb_data.clear()
            self.selected_index = None
            self.root.unbind("<Delete>")
            self.draw_placeholder()

    def on_mousewheel(self, event):
        """Redirects vertical mouse wheel scroll actions to the horizontal preview canvas frame."""
        if event.delta:
            self.thumb_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def handle_drop(self, event):
        """Processes drop structural events received globally via system shell managers."""
        raw_data = event.data
        paths = []
        
        # Intercept curly bracket path groups generated by OS window spaces
        if raw_data.startswith('{'):
            items = raw_data.split('}')
            for item in items:
                cleaned = item.strip('{ ').strip()
                if cleaned:
                    paths.append(cleaned)
        else:
            paths = [p.strip() for p in raw_data.split() if p.strip()]

        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.pdf')
        loaded_any = False

        for path in paths:
            path = path.strip('"').strip("'")
            if os.path.isfile(path) and path.lower().endswith(valid_extensions):
                try:
                    if path.lower().endswith('.pdf'):
                        self.load_pdf_pages(path)
                    else:
                        self.load_image_from_path(path)
                    loaded_any = True
                except Exception as e:
                    print(f"Error parsing asset target payload: {e}")
                    
        if not loaded_any:
            messagebox.showwarning("Format Warning", "Dropped files must be valid image or PDF formats!")

    def load_image_from_path(self, path):
        """Decoupled helper to load standalone localized disk images directly into the runtime sequence."""
        file_img = Image.open(path)
        self.process_and_store_image(file_img)

    def on_canvas_zoom(self, event):
        """Calculates canvas dimensions when scroll event fires over main workbench."""
        if not self.image_list or self.selected_index is None:
            return

        # Upward scroll increases scale factor, downward drops it
        if event.delta > 0:
            self.zoom_scale += 0.1
        else:
            self.zoom_scale -= 0.1

        # Clip values to ensure safe display ranges (minimum 20% zoom, max 400%)
        self.zoom_scale = max(min(self.zoom_scale, 4.0), 0.2)
        
        # Re-render the canvas visualization
        self.update_main_canvas(self.image_list[self.selected_index])

    def load_pdf_pages(self, path):
        """Converts each page of a dropped/pasted PDF into an image and pushes it to storage."""
        try:
            # Convert PDF pages directly to a list of PIL Images in memory
            # Note: If poppler is not in your system path on Windows, pass poppler_path=r"C:\Program Files\Poppler\bin"
            pages = convert_from_path(path)
            
            if not pages:
                return

            for page in pages:
                self.process_and_store_image(page)
                
        except PDFInfoNotInstalledError:
            # Trap missing background binary error cleanly and point out immediate fix
            messagebox.showerror(
                "System Dependency Missing", 
                "Poppler is required to convert PDF files into images.\n\n"
                "Please open your command prompt/terminal and execute:\n"
                "winget install oschwartz10612.Poppler\n\n"
                "Note: Make sure to restart your editor or terminal after it finishes installing!"
            )
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to extract pages from PDF:\n{str(e)}")

if __name__ == "__main__":
    # Standard tk.Tk() initialization is replaced with the custom TkinterDnD context framework
    root = TkinterDnD.Tk()
    app = ImageToPdfApp(root)
    root.mainloop()
