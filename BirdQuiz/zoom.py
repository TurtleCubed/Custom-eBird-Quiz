"""Resizable, pan-and-zoom Tkinter image canvas."""

import tkinter as tk
from PIL import Image, ImageTk


class ZoomableImageCanvas(tk.Canvas):
    """Show a PIL image fitted to the available area with wheel zoom and drag pan."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("background", "#101820")
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self.image: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._image_item = None
        self._fit_scale = 1.0
        self._zoom = 1.0
        self._render_after_id = None

        self.bind("<Configure>", self._on_configure)
        self.bind("<ButtonPress-1>", self._pan_start)
        self.bind("<B1-Motion>", self._pan_move)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<Button-4>", self._wheel)
        self.bind("<Button-5>", self._wheel)
        self.bind("<Double-Button-1>", lambda _event: self.reset_zoom())

    def set_image(self, image: Image.Image | None):
        self.image = image.copy() if image is not None else None
        self._zoom = 1.0
        self._schedule_render()

    def zoom_in(self):
        self._change_zoom(1.2)

    def zoom_out(self):
        self._change_zoom(1 / 1.2)

    def reset_zoom(self):
        self._zoom = 1.0
        self._schedule_render()

    def _change_zoom(self, factor):
        if self.image is None:
            return
        self._zoom = min(5.0, max(0.25, self._zoom * factor))
        self._schedule_render()

    def _wheel(self, event):
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"

    def _pan_start(self, event):
        if self.image is not None and self._zoom > 1:
            self.scan_mark(event.x, event.y)

    def _pan_move(self, event):
        if self.image is not None and self._zoom > 1:
            self.scan_dragto(event.x, event.y, gain=1)

    def _on_configure(self, _event):
        self._schedule_render()

    def _schedule_render(self):
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except tk.TclError:
                pass
        self._render_after_id = self.after_idle(self._render)

    def _render(self):
        self._render_after_id = None
        self.delete("all")
        self._image_item = None
        if self.image is None:
            self.configure(scrollregion=(0, 0, 1, 1))
            return

        area_width = max(self.winfo_width(), 1)
        area_height = max(self.winfo_height(), 1)
        self._fit_scale = min(
            area_width / self.image.width,
            area_height / self.image.height,
        )
        scale = self._fit_scale * self._zoom
        target_width = max(1, int(self.image.width * scale))
        target_height = max(1, int(self.image.height * scale))

        # Avoid allocating an enormous bitmap after repeated zooming.
        longest_side = max(target_width, target_height)
        if longest_side > 5000:
            scale *= 5000 / longest_side
            target_width = max(1, int(self.image.width * scale))
            target_height = max(1, int(self.image.height * scale))

        resized = self.image.resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
        self._photo = ImageTk.PhotoImage(resized)
        region_width = max(area_width, target_width)
        region_height = max(area_height, target_height)
        x = region_width / 2
        y = region_height / 2
        self._image_item = self.create_image(
            x, y, image=self._photo, anchor="center"
        )
        self.configure(scrollregion=(0, 0, region_width, region_height))
        self.xview_moveto(0)
        self.yview_moveto(0)


# Preserve the previous import name for any local scripts that use it.
Zoom_Advanced = ZoomableImageCanvas
