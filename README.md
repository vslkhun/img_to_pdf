## Image to PDF — README

### Intro
Image to PDF is a lightweight desktop utility that converts dropped or pasted images and PDF pages into a single compiled PDF. It provides a visual preview, thumbnail ordering, and quick export so you can assemble multi-page PDFs from screenshots, photos, or document scans.

### Features and how it works
- Drag & drop image files or PDFs into the window (supports common image formats and multi-page PDFs).
- Paste images from the clipboard (Ctrl+V) to add them directly.
- Scrollable thumbnail tray for quick reordering — click a thumbnail to preview it in the main canvas.
- Drag thumbnails left/right to reorder pages; right-click (or Delete) to remove a page.
- Zoom in/out on the main preview using the mouse wheel.
- Export the current sequence as a single PDF using the "Create PDF" button.
- Multi-page PDFs are converted to individual images (requires Poppler).

### Screenshot
Some screenshots are here:

![App Screenshot](images/sc1.png)
![App Screenshot](images/sc2.png)



### System Dependencies
This application requires the following dependencies:

- Python 3.8+ (Anaconda or standard Python distribution)
- Pillow
- pdf2image
- tkinterdnd2 (for drag-and-drop support)
- customtkinter (UI theming; required for `cmain.py`)
- Poppler (for converting PDF pages to images)

Platform-specific Poppler install instructions:

- **Windows**: Run `winget install oschwartz10612.Poppler`
- **macOS**: Run `brew install poppler`
- **Linux**: Run `sudo apt-get install poppler-utils`

Add Python packages with pip, for example:

```bash
pip install -r requirements.txt
```

### Tested on
- Windows 11



