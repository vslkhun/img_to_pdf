# app.py
import ctypes
import os
import tkinter as tk
from tkinter import filedialog

from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image, ImageGrab, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

from theme import LAYOUT, THEMES, CustomDialog, CustomScrollbar, RoundedButton
import webbrowser

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
        self.root.title(LAYOUT["app_title"])
        self.root.geometry(LAYOUT["window_size"])
        min_w, min_h = LAYOUT["min_window_size"]
        self.root.minsize(min_w, min_h)

        self.current_mode = "light"
        self.colors = THEMES[self.current_mode]

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.image_list = []
        self.thumb_data = []
        self.selected_index = None
        self.dragged_index = None

        self.canvas_size = LAYOUT["default_canvas_size"]
        self.thumb_size = LAYOUT["default_thumb_size"]
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
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.instruction_label = tk.Label(
            self.workspace,
            text="Drop Image/PDF / Ctrl+V to Paste | Click thumbnail to view | Drag thumbnails to reorder",
            font=LAYOUT["font_instruction"],
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
            font=LAYOUT["font_info"],
            bg=self.colors["bg"],
            fg=self.colors["subtext"],
        )
        self.info_label.grid(row=2, column=0, pady=2, sticky="ew")

        # Scrollable Thumbnail Shelf
        self.thumb_outer_frame = tk.Frame(
            self.workspace,
            bg=self.colors["tray_bg"],
            height=LAYOUT["thumb_tray_height"],
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
            height=LAYOUT["scrollbar_height"],
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

        # Bottom Control Toolbar
        self.toolbar = tk.Frame(
            self.workspace,
            bg=self.colors["toolbar_bg"],
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=8,
        )
        self.toolbar.grid(row=4, column=0, sticky="ew", pady=(5, 0))
        # Footer Label
        self.lbl_footer = tk.Label(
            self.workspace,
            text=LAYOUT["footer_text"]["text"],
            font=LAYOUT["font_footer"],
            bg=self.colors["bg"],
            fg=self.colors["subtext"],
        )
        self.lbl_footer.grid(row=5, column=0, pady=(6, 0), sticky="ew")
        # Open link on click
        self.lbl_footer.bind(
            "<Button-1>",
            lambda e: webbrowser.open_new(LAYOUT["footer_text"]["url"]),
        )
        # Canvas Preview Size Control
        self.lbl_canvas_icon = tk.Label(
            self.toolbar,
            text="🖼️ Canvas",
            font=LAYOUT["font_bold"],
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
        )
        self.lbl_canvas_icon.pack(side=tk.LEFT, padx=(5, 5))

        c_min, c_max = LAYOUT["slider_canvas_range"]
        self.canvas_slider = tk.Scale(
            self.toolbar,
            from_=c_min,
            to=c_max,
            orient=tk.HORIZONTAL,
            length=LAYOUT["slider_length"],
            showvalue=False,
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            width=LAYOUT["slider_width"],
        )
        self.canvas_slider.set(c_max)
        self.canvas_slider.pack(side=tk.LEFT, padx=(0, 20))
        self.canvas_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Thumbnail Size Control
        self.lbl_thumb_icon = tk.Label(
            self.toolbar,
            text="🔍 Thumbs",
            font=LAYOUT["font_bold"],
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
        )
        self.lbl_thumb_icon.pack(side=tk.LEFT, padx=(5, 5))

        t_min, t_max = LAYOUT["slider_thumb_range"]
        self.thumb_slider = tk.Scale(
            self.toolbar,
            from_=t_min,
            to=t_max,
            orient=tk.HORIZONTAL,
            length=LAYOUT["slider_length"],
            showvalue=False,
            bg=self.colors["toolbar_bg"],
            fg=self.colors["text"],
            highlightthickness=0,
            bd=0,
            width=LAYOUT["slider_width"],
        )
        self.thumb_slider.set(self.thumb_size)
        self.thumb_slider.pack(side=tk.LEFT, padx=(0, 20))
        self.thumb_slider.bind("<ButtonRelease-1>", self.on_layout_slider_change)

        # Action Buttons
        reset_cfg = LAYOUT["btn_reset_size"]
        self.btn_reset = RoundedButton(
            self.toolbar,
            text="🗑️ Reset",
            command=self.reset_all,
            bg_color=LAYOUT["btn_reset_bg"],
            hover_color=LAYOUT["btn_reset_hover"],
            text_color="white",
            radius=reset_cfg["radius"],
            width=reset_cfg["width"],
            height=reset_cfg["height"],
            font=LAYOUT["font_bold"],
        )
        self.btn_reset.pack(side=tk.RIGHT, padx=6)

        create_cfg = LAYOUT["btn_create_size"]
        self.btn_create = RoundedButton(
            self.toolbar,
            text="📄 Create PDF",
            command=self.create_pdf,
            bg_color=LAYOUT["btn_create_bg"],
            hover_color=LAYOUT["btn_create_hover"],
            text_color="white",
            radius=create_cfg["radius"],
            width=create_cfg["width"],
            height=create_cfg["height"],
            font=LAYOUT["font_bold"],
        )
        self.btn_create.pack(side=tk.RIGHT, padx=6)

        theme_cfg = LAYOUT["btn_theme_size"]
        self.btn_theme = RoundedButton(
            self.toolbar,
            text="🌙 Theme",
            command=self.toggle_theme,
            bg_color=self.colors["btn_theme_bg"],
            hover_color=self.colors["btn_theme_hover"],
            text_color=self.colors["btn_theme_fg"],
            radius=theme_cfg["radius"],
            width=theme_cfg["width"],
            height=theme_cfg["height"],
            font=LAYOUT["font_bold"],
        )
        self.btn_theme.pack(side=tk.RIGHT, padx=6)

        self.canvas_text = ""
        self.draw_placeholder()
        # Bind Canvas Panning (Click & Drag to move zoomed image)
        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_panning)

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

        self.lbl_footer.config(
            bg=self.colors["bg"], fg=self.colors["subtext"]
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
                font=LAYOUT["font_placeholder"],
            )

    def on_layout_slider_change(self, event=None):
        self.canvas_size = self.canvas_slider.get()
        self.thumb_size = self.thumb_slider.get()
        self.thumb_outer_frame.config(height=self.thumb_size + 75)

        self.rebuild_thumbnails_cache()
        if self.selected_index is not None:
            self.update_main_canvas_on_slide(self.image_list[self.selected_index])
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
                self.show_warning(
                    "Paste Failed", "No valid image or file path found in clipboard!"
                )
        except Exception as e:
            self.show_error("Error", f"Failed to paste element:\n{str(e)}")

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
            font=LAYOUT["font_thumb_num"],
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

    def update_main_canvas_on_slide(self, pil_img):
        self.root.update_idletasks()
        
        # Get actual canvas viewport dimensions (with small 10px margin)
        cw = max(self.canvas.winfo_width() - 10, 100)
        ch = max(self.canvas.winfo_height() - 10, 100)

        img_w, img_h = pil_img.size

        # 1. Calculate the exact "Fit to Canvas" scale factor (contained within bounds)
        ratio = min(cw / img_w, ch / img_h)
        
        # 2. At slider = 100%, width & height equal exact fit-to-canvas dimensions
        slider_factor = self.canvas_slider.get() / 100.0
        
        fit_w = int(img_w * ratio * slider_factor)
        fit_h = int(img_h * ratio * slider_factor)

        fit_w = max(fit_w, 20)
        fit_h = max(fit_h, 20)

        # 3. High-quality smooth resize
        display_img = pil_img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)
        self.current_canvas_tk = ImageTk.PhotoImage(display_img)

        # Render perfectly centered
        self.canvas.delete("all")
        self.canvas.create_image(
            cw // 2, ch // 2, image=self.current_canvas_tk, anchor=tk.CENTER, tags="img"
        )
    def update_main_canvas(self, pil_img):
        self.root.update_idletasks()
        cw = max(self.canvas.winfo_width() - 10, 100)
        ch = max(self.canvas.winfo_height() - 10, 100)

        # Reads canvas slider (10% to 100%) and multiplies by zoom_scale
        scale_factor = (self.canvas_slider.get() / 100.0) * self.zoom_scale

        max_w = int(cw * scale_factor)
        max_h = int(ch * scale_factor)

        display_img = pil_img.copy()
        display_img.thumbnail((max(max_w, 20), max(max_h, 20)))
        self.current_canvas_tk = ImageTk.PhotoImage(display_img)

        # Render centered image on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            cw // 2, ch // 2, image=self.current_canvas_tk, anchor=tk.CENTER, tags="img"
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
            self.show_warning("Empty", "No images pasted yet to generate a PDF!")
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
            self.show_info(
                "Success",
                f"PDF created successfully with {len(self.image_list)} images!",
            )
        except Exception as e:
            self.show_error("Error", f"Failed to save PDF:\n{str(e)}")

    def reset_all(self):
        if not self.image_list:
            return

        if self.ask_yes_no(
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
            self.show_warning(
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
            self.show_error(
                "System Dependency Missing",
                "Poppler is required to convert PDF files into images.\n\n"
                "Please open your command prompt/terminal and execute:\n"
                "winget install oschwartz10612.Poppler\n\n"
                "Note: Make sure to restart your editor or terminal after it finishes installing!",
            )
        except Exception as e:
            self.show_error(
                "PDF Error", f"Failed to extract pages from PDF:\n{str(e)}"
            )

    def show_info(self, title, message):
        CustomDialog(
            self.root,
            title,
            message,
            dialog_type="info",
            colors=self.colors,
            dark_title_bar_func=set_title_bar_mode,
        )

    def show_warning(self, title, message):
        CustomDialog(
            self.root,
            title,
            message,
            dialog_type="warning",
            colors=self.colors,
            dark_title_bar_func=set_title_bar_mode,
        )

    def show_error(self, title, message):
        CustomDialog(
            self.root,
            title,
            message,
            dialog_type="error",
            colors=self.colors,
            dark_title_bar_func=set_title_bar_mode,
        )

    def ask_yes_no(self, title, message):
        dialog = CustomDialog(
            self.root,
            title,
            message,
            dialog_type="yesno",
            colors=self.colors,
            dark_title_bar_func=set_title_bar_mode,
        )
        return dialog.result

    def on_pan_start(self, event):
        """Record starting mouse coordinates when drag begins on canvas."""
        self.canvas.focus_set()
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_panning(self, event):
        """Move canvas items smoothly based on mouse drag distance."""
        if not self.image_list:
            return

        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y

        # Move the image on the canvas
        self.canvas.move("all", dx, dy)

        # Update reference points
        self.pan_start_x = event.x
        self.pan_start_y = event.y
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageToPdfApp(root)
    root.mainloop()