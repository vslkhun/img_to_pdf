#app.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image, ImageGrab, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from theme import THEMES, RoundedButton, CustomScrollbar
import ctypes

def set_title_bar_mode(window, dark=True):
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )
    except Exception:
        pass

class ImageToPdfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to PDF Creator")
        self.root.geometry("950x700")
        self.root.minsize(700, 500)

        self.current_mode = "light"
        self.colors = THEMES[self.current_mode]

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.image_list = []
        self.thumb_data = []
        self.selected_index = None
        self.dragged_index = None

        self.canvas_size = 350
        self.thumb_size = 70
        self.zoom_scale = 1.0

        self.setup_ui()

        self.root.bind("<Control-v>", self.handle_paste)
        self.root.bind("<Control-V>", self.handle_paste)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_drop)

    def setup_ui(self):
        # Workspace Container
        self.workspace = tk.Frame(self.root, bg=self.colors["bg"], padx=15, pady=10)
        self.workspace.grid(row=0, column=0, sticky="nsew")
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(1, weight=1)

        self.instruction_label = tk.Label(
            self.workspace,
            text="Drop Image/PDF / Ctrl+V to Paste | Click thumbnail to view | Drag thumbnails to reorder",
            font=("Arial", 11),
            bg=self.colors["bg"],
            fg=self.colors["subtext"],
        )
        self.instruction_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        # Main Image Preview Canvas
        self.canvas = tk.Canvas(
            self.workspace,
            bg=self.colors["card_bg"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=5)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        self.canvas.bind("<Configure>", self.respond_to_canvas_resize)
        self.canvas.bind("<MouseWheel>", self.on_canvas_zoom)

        self.info_label = tk.Label(
            self.workspace,
            text="Press 'Delete' key or Right-Click a thumbnail to remove it.",
            font=("Arial", 9, "italic"),
            bg=self.colors["bg"],
            fg=self.colors["subtext"],
        )
        self.info_label.grid(row=2, column=0, pady=2, sticky="ew")

        # Scrollable Thumbnail Shelf
        self.thumb_outer_frame = tk.Frame(
            self.workspace,
            bg=self.colors["tray_bg"],
            height=150,
            bd=1,
            relief=tk.SUNKEN,
        )
        self.thumb_outer_frame.grid(row=3, column=0, sticky="ew", pady=(5, 5))
        self.thumb_outer_frame.grid_propagate(False)
        self.thumb_outer_frame.columnconfigure(0, weight=1)
        self.thumb_outer_frame.rowconfigure(0, weight=1)

        self.thumb_canvas = tk.Canvas(
            self.thumb_outer_frame,
            bg=self.colors["tray_bg"],
            highlightthickness=0,
        )
        self.scrollbar = CustomScrollbar(
            self.thumb_outer_frame,
            command=self.thumb_canvas.xview,
            track_color=self.colors["scrollbar_track"],
            thumb_color=self.colors["scrollbar_thumb"],
            height=10,
        )
        self.thumb_inner_frame = tk.Frame(
            self.thumb_canvas, bg=self.colors["tray_bg"]
        )
        self.thumb_inner_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(
                scrollregion=self.thumb_canvas.bbox("all")
            ),
        )
        self.thumb_inner_frame.bind(
            "<Enter>", lambda e: self.thumb_canvas.focus_set()
        )
        self.thumb_inner_frame.bind("<MouseWheel>", self.on_mousewheel)

        self.thumb_canvas.create_window(
            (0, 0), window=self.thumb_inner_frame, anchor="nw"
        )
        self.thumb_canvas.configure(xscrollcommand=self.scrollbar.set)

        self.thumb_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=0, sticky="ew")

        self.thumb_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.thumb_outer_frame.bind("<MouseWheel>", self.on_mousewheel)

        # =====================================================================
        # BOTTOM CONTROL TOOLBAR (Comfortable / Larger Sizing)
        # =====================================================================
        self.toolbar = tk.Frame(
            self.workspace,
            bg=self.colors["toolbar_bg"],
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=8,
        )
        self.toolbar.grid(row=4, column=0, sticky="ew", pady=(5, 0))

        # Canvas Preview Size Control
        self.lbl_canvas_icon = tk.Label(
            self.toolbar,
            text="🖼️ Canvas",
            font=("Arial", 10, "bold"),
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
        )
        self.lbl_canvas_icon.pack(side=tk.LEFT, padx=(5, 5))

        self.canvas_slider = tk.Scale(
            self.toolbar,
            from_=200,
            to=600,
            orient=tk.HORIZONTAL,
            length=140,  # Increased slider length
            showvalue=False,
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            width=12,  # Thicker slider track
        )
        self.canvas_slider.set(self.canvas_size)
        self.canvas_slider.pack(side=tk.LEFT, padx=(0, 20))
        self.canvas_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Thumbnail Size Control
        self.lbl_thumb_icon = tk.Label(
            self.toolbar,
            text="🔍 Thumbs",
            font=("Arial", 10, "bold"),
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
        )
        self.lbl_thumb_icon.pack(side=tk.LEFT, padx=(5, 5))

        self.thumb_slider = tk.Scale(
            self.toolbar,
            from_=40,
            to=120,
            orient=tk.HORIZONTAL,
            length=140,  # Increased slider length
            showvalue=False,
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            width=12,  # Thicker slider track
        )
        self.thumb_slider.set(self.thumb_size)
        self.thumb_slider.pack(side=tk.LEFT, padx=(0, 20))
        self.thumb_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Right-aligned Larger Action Buttons
        self.btn_reset = RoundedButton(
            self.toolbar,
            text="🗑️ Reset",
            command=self.reset_all,
            bg_color="#9b2118",
            hover_color="#b62f28",
            text_color="white",
            radius=8,
            width=90,
            height=36,
            font=("Arial", 10, "bold"),
        )
        self.btn_reset.pack(side=tk.RIGHT, padx=6)

        self.btn_create = RoundedButton(
            self.toolbar,
            text="📄 Create PDF",
            command=self.create_pdf,
            bg_color="#1D9E21",
            hover_color="#10a018",
            text_color="white",
            radius=8,
            width=110,
            height=36,
            font=("Arial", 10, "bold"),
        )
        self.btn_create.pack(side=tk.RIGHT, padx=6)

        self.btn_theme = RoundedButton(
            self.toolbar,
            text="🌙 Theme",
            command=self.toggle_theme,
            bg_color=self.colors["btn_theme_bg"],
            hover_color=self.colors["btn_theme_hover"],
            text_color=self.colors["btn_theme_fg"],
            radius=8,
            width=85,
            height=36,
            font=("Arial", 10, "bold"),
        )
        self.btn_theme.pack(side=tk.RIGHT, padx=6)

        self.canvas_text = '' #None
        self.draw_placeholder()

    def toggle_theme(self):
        self.current_mode = "dark" if self.current_mode == "light" else "light"
        self.colors = THEMES[self.current_mode]

        mode_text = "☀️ Theme" if self.current_mode == "dark" else "🌙 Theme"
        self.btn_theme.text = mode_text
        self.btn_theme.update_colors(
            parent_bg=self.colors["toolbar_bg"],
            bg_color=self.colors["btn_theme_bg"],
            hover_color=self.colors["btn_theme_hover"],
            text_color=self.colors["btn_theme_fg"],
        )

        self.btn_create.update_colors(parent_bg=self.colors["toolbar_bg"])
        self.btn_reset.update_colors(parent_bg=self.colors["toolbar_bg"])

        # Update Custom Scrollbar Theme Colors
        self.scrollbar.update_colors(
            track_color=self.colors["scrollbar_track"],
            thumb_color=self.colors["scrollbar_thumb"],
        )

        self.root.configure(bg=self.colors["bg"])
        self.workspace.config(bg=self.colors["bg"])
        self.toolbar.config(bg=self.colors["toolbar_bg"])

        self.lbl_canvas_icon.config(
            bg=self.colors["toolbar_bg"], fg=self.colors["text"]
        )
        self.lbl_thumb_icon.config(
            bg=self.colors["toolbar_bg"], fg=self.colors["text"]
        )

        self.canvas_slider.config(
            bg=self.colors["toolbar_bg"], fg=self.colors["text"]
        )
        self.thumb_slider.config(
            bg=self.colors["toolbar_bg"], fg=self.colors["text"]
        )

        self.instruction_label.config(
            bg=self.colors["bg"], fg=self.colors["subtext"]
        )
        self.info_label.config(bg=self.colors["bg"], fg=self.colors["subtext"])

        self.canvas.config(
            bg=self.colors["card_bg"], highlightbackground=self.colors["border"]
        )
        self.thumb_outer_frame.config(bg=self.colors["tray_bg"])
        self.thumb_canvas.config(bg=self.colors["tray_bg"])
        self.thumb_inner_frame.config(bg=self.colors["tray_bg"])

        if not self.image_list:
            self.draw_placeholder()
        self.refresh_thumbnail_layout()
        set_title_bar_mode(self.root, dark=(self.current_mode == "dark"))
        
    def draw_placeholder(self):
        if not self.image_list:
            self.canvas.delete("all")
            w = (
                self.canvas.winfo_width()
                if self.canvas.winfo_width() > 1
                else 500
            )
            h = (
                self.canvas.winfo_height()
                if self.canvas.winfo_height() > 1
                else 350
            )
            placeholder_color = (
                "#888888" if self.current_mode == "dark" else "#aaaaaa"
            )
            self.canvas_text = self.canvas.create_text(
                w // 2,
                h // 2,
                text="[ Drop Image/PDF or Paste Here ]",
                fill=placeholder_color,
                font=("Arial", 14, "italic"),
            )

    def on_layout_slider_change(self, event=None):
        self.canvas_size = self.canvas_slider.get()
        self.thumb_size = self.thumb_slider.get()
        self.thumb_outer_frame.config(height=self.thumb_size + 75)

        self.rebuild_thumbnails_cache()
        if self.selected_index is not None:
            self.update_main_canvas(self.image_list[self.selected_index])
        self.refresh_thumbnail_layout()

    def respond_to_canvas_resize(self, event):
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
                        if path.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".bmp", ".gif")
                        ):
                            self.process_and_store_image(Image.open(path))
                        elif path.lower().endswith(".pdf"):
                            self.load_pdf_pages(path)
            else:
                messagebox.showwarning(
                    "Paste Failed", "No valid image or file path found in clipboard!"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste element: {str(e)}")

    def process_and_store_image(self, pil_img):
        if not self.image_list:
            self.canvas.delete(self.canvas_text)

        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")

        self.image_list.append(pil_img)

        idx = len(self.image_list) - 1
        item_frame = tk.Frame(
            self.thumb_inner_frame,
            bg=self.colors["tray_bg"],
            bd=2,
            relief=tk.FLAT,
        )
        lbl_img = tk.Label(item_frame, bg="white")
        lbl_img.pack()
        lbl_num = tk.Label(
            item_frame,
            text="",
            font=("Arial", 9, "bold"),
            bg=self.colors["tray_bg"],
            fg=self.colors["card_text"],
        )
        lbl_num.pack()

        self.thumb_data.append(
            {
                "frame": item_frame,
                "lbl_img": lbl_img,
                "lbl_num": lbl_num,
                "tk_thumb": None,
            }
        )

        self.rebuild_single_thumbnail(idx)
        self.selected_index = idx
        self.zoom_scale = 1.0
        self.update_main_canvas(pil_img)
        self.refresh_thumbnail_layout()

    def rebuild_single_thumbnail(self, idx):
        orig_img = self.image_list[idx]
        thumb_img = orig_img.copy()
        thumb_img.thumbnail((self.thumb_size, self.thumb_size))
        tk_thumb = ImageTk.PhotoImage(thumb_img)

        data = self.thumb_data[idx]
        data["tk_thumb"] = tk_thumb
        data["lbl_img"].config(image=tk_thumb)

    def rebuild_thumbnails_cache(self):
        for idx in range(len(self.image_list)):
            self.rebuild_single_thumbnail(idx)

    def update_main_canvas(self, pil_img):
        self.root.update_idletasks()
        cw = self.canvas.winfo_width() - 10
        ch = self.canvas.winfo_height() - 10

        cw = max(cw, 100)
        ch = max(ch, 100)

        max_w = min(cw, self.canvas_size * 1.5)
        max_h = min(ch, self.canvas_size)

        final_w = int(max_w * self.zoom_scale)
        final_h = int(max_h * self.zoom_scale)

        final_w = max(min(final_w, 3000), 20)
        final_h = max(min(final_h, 3000), 20)

        display_img = pil_img.copy()
        display_img.thumbnail((final_w, final_h))
        self.current_canvas_tk = ImageTk.PhotoImage(display_img)

        self.canvas.delete("all")
        self.canvas.create_image(
            cw // 2, ch // 2, image=self.current_canvas_tk, anchor=tk.CENTER
        )

    def refresh_thumbnail_layout(self):
        for data in self.thumb_data:
            data["frame"].pack_forget()

        for idx, data in enumerate(self.thumb_data):
            data["frame"].pack(side=tk.LEFT, padx=8, pady=5)
            data["lbl_num"].config(text=f"#{idx + 1}")

            if self.selected_index == idx:
                data["frame"].config(
                    relief=tk.SOLID, bg=self.colors["card_selected"]
                )
                data["lbl_num"].config(
                    bg=self.colors["card_selected"],
                    fg=self.colors["card_text_selected"],
                )
            else:
                data["frame"].config(relief=tk.FLAT, bg=self.colors["tray_bg"])
                data["lbl_num"].config(
                    bg=self.colors["tray_bg"], fg=self.colors["card_text"]
                )

            for w in (data["frame"], data["lbl_img"], data["lbl_num"]):
                w.bind("<Button-1>", lambda e, index=idx: self.select_thumbnail(index))
                w.bind("<Button-3>", lambda e, index=idx: self.delete_thumbnail(index))
                w.bind(
                    "<ButtonPress-1>",
                    lambda e, index=idx: self.on_drag_start(index),
                    add="+",
                )
                w.bind("<B1-Motion>", lambda e, index=idx: self.on_dragging(e, index))

        self.thumb_canvas.update_idletasks()
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))

    def select_thumbnail(self, index):
        self.selected_index = index
        self.zoom_scale = 1.0
        self.update_main_canvas(self.image_list[index])
        self.refresh_thumbnail_layout()
        self.root.bind(
            "<Delete>", lambda event: self.delete_thumbnail(self.selected_index)
        )

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
            child = data["frame"]
            child_x = child.winfo_x()
            child_width = child.winfo_width()

            if child_x <= x_on_inner_frame <= (child_x + child_width):
                if target_idx != self.dragged_index:
                    img = self.image_list.pop(self.dragged_index)
                    self.image_list.insert(target_idx, img)

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
            self.thumb_data[index]["frame"].destroy()
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
            title="Save Compiled PDF As",
        )
        if not file_path:
            return

        try:
            first_image = self.image_list[0]
            subsequent_images = self.image_list[1:]
            first_image.save(file_path, save_all=True, append_images=subsequent_images)
            messagebox.showinfo(
                "Success",
                f"PDF created successfully with {len(self.image_list)} images!",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save PDF:\n{str(e)}")

    def reset_all(self):
        if not self.image_list:
            return

        if messagebox.askyesno(
            "Confirm Reset", "Are you sure you want to clear all images?"
        ):
            self.image_list.clear()
            for data in self.thumb_data:
                data["frame"].destroy()
            self.thumb_data.clear()
            self.selected_index = None
            self.root.unbind("<Delete>")
            self.draw_placeholder()

    def on_mousewheel(self, event):
        delta = 0
        if hasattr(event, "delta") and event.delta:
            delta = int(-1 * (event.delta / 120))
        elif hasattr(event, "num"):
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1

        if delta:
            self.thumb_canvas.xview_scroll(delta, "units")

    def handle_drop(self, event):
        raw_data = event.data
        paths = []

        if raw_data.startswith("{"):
            items = raw_data.split("}")
            for item in items:
                cleaned = item.strip("{ ").strip()
                if cleaned:
                    paths.append(cleaned)
        else:
            paths = [p.strip() for p in raw_data.split() if p.strip()]

        valid_extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
            ".webp",
            ".tiff",
            ".pdf",
        )
        loaded_any = False

        for path in paths:
            path = path.strip('"').strip("'")
            if os.path.isfile(path) and path.lower().endswith(valid_extensions):
                try:
                    if path.lower().endswith(".pdf"):
                        self.load_pdf_pages(path)
                    else:
                        self.load_image_from_path(path)
                    loaded_any = True
                except Exception as e:
                    print(f"Error parsing asset target payload: {e}")

        if not loaded_any:
            messagebox.showwarning(
                "Format Warning", "Dropped files must be valid image or PDF formats!"
            )

    def load_image_from_path(self, path):
        file_img = Image.open(path)
        self.process_and_store_image(file_img)

    def on_canvas_zoom(self, event):
        if not self.image_list or self.selected_index is None:
            return

        if event.delta > 0:
            self.zoom_scale += 0.1
        else:
            self.zoom_scale -= 0.1

        self.zoom_scale = max(min(self.zoom_scale, 4.0), 0.2)
        self.update_main_canvas(self.image_list[self.selected_index])

    def load_pdf_pages(self, path):
        try:
            pages = convert_from_path(path)
            if not pages:
                return

            for page in pages:
                self.process_and_store_image(page)

        except PDFInfoNotInstalledError:
            messagebox.showerror(
                "System Dependency Missing",
                "Poppler is required to convert PDF files into images.\n\n"
                "Please open your command prompt/terminal and execute:\n"
                "winget install oschwartz10612.Poppler\n\n"
                "Note: Make sure to restart your editor or terminal after it finishes installing!",
            )
        except Exception as e:
            messagebox.showerror(
                "PDF Error", f"Failed to extract pages from PDF:\n{str(e)}"
            )


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageToPdfApp(root)
    root.mainloop()