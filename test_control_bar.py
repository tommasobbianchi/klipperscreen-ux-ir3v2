#!/usr/bin/env python3
"""Regression check for the job-status control bar.

The pause/stop buttons used to sit in `self.grid`, which is column_homogeneous and
also carries the progress ring and the info grid. The grid's minimum width therefore
drove the bar's, and on a narrow panel the two rightmost buttons (pause, stop) were
pushed off the right edge — out of reach mid-print.

The fix packs the bar in its own homogeneous Gtk.Box under the grid and makes the four
print actions icon-only, so its width demand is small and independent of the grid.

This measures both layouts with real GTK geometry at the same font metrics the panel
uses (KlippyGtk font_ratio [27, 18], font_size=large) and asserts the new bar is never
worse. Needs a display: run under `xvfb-run -a python3 test_control_bar.py`.
"""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gtk


def metrics(w, h):
    """Mirrors KlippyGtk.__init__ for this repo's font_ratio, horizontal, font_size=large."""
    font = min(w / 27, h / 18) * 1.025
    img_scale = font * 2 * 0.85
    return font, img_scale, w - int(w * 0.1)  # content width = panel minus the left rail


def icon(px):
    # only the allocated size matters for layout, so a blank pixbuf stands in for the svg
    return Gtk.Image.new_from_pixbuf(
        GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, max(1, int(px)), max(1, int(px)))
    )


def bar_button(label, img_scale, scale):
    b = Gtk.Button(hexpand=True, vexpand=True, image_position=Gtk.PositionType.TOP,
                   always_show_image=True)
    if label:
        b.set_label(label)
    else:
        scale *= 1.4  # KlippyGtk bumps label-less icons by 1.4
    b.set_image(icon(img_scale * scale))
    return b


def side_button(label, img_scale):
    b = Gtk.Button(hexpand=True, vexpand=True, image_position=Gtk.PositionType.LEFT,
                   always_show_image=True, label=label)
    b.set_image(icon(img_scale * 0.65))
    b.set_halign(Gtk.Align.START)
    return b


def info_grid(img_scale):
    """create_status_grid(): the readouts whose labels drive the grid's minimum width."""
    sz = Gtk.Grid(column_homogeneous=True)
    sz.attach(side_button("100% 45/60 mm/s", img_scale), 0, 0, 3, 1)
    sz.attach(side_button("Z:  12.34/50.00 mm", img_scale), 2, 0, 2, 1)
    sz.attach(side_button("100%  12.5 mm³/s", img_scale), 0, 1, 3, 1)
    sz.attach(side_button(" 100%", img_scale), 2, 1, 2, 1)

    temps = Gtk.Grid()
    for i, lb in enumerate(["220/220 °C", "60/60 °C"]):
        temps.attach(side_button(lb, img_scale), i, 0, 1, 1)

    info = Gtk.Grid(row_homogeneous=True)
    info.attach(temps, 0, 0, 1, 1)
    info.attach(sz, 0, 1, 1, 2)
    info.attach(side_button("Elapsed:  1h 23m", img_scale), 0, 3, 1, 1)
    info.attach(side_button("Left:  45m", img_scale), 0, 4, 1, 1)

    ig = Gtk.Grid()
    ig.attach(Gtk.Button(label=""), 0, 0, 1, 1)  # thumbnail
    ig.attach(info, 1, 0, 1, 1)
    return ig


def measure(w, h, old):
    font, img_scale, content_w = metrics(w, h)
    win = Gtk.OffscreenWindow()
    win.set_default_size(w, h)
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

    grid = Gtk.Grid(column_homogeneous=True)
    ring = Gtk.DrawingArea()
    ring.set_size_request(int(font * 5), int(font * 5))
    grid.attach(ring, 0, 0, 1, 1)
    grid.attach(Gtk.Label(label="benchy_belt_v3.gcode"), 1, 0, 3, 1)
    grid.attach(info_grid(img_scale), 0, 1, 4, 2)

    if old:  # bar attached into the grid, labelled buttons
        bar = Gtk.Grid(row_homogeneous=True, column_homogeneous=True, vexpand=False)
        for i, lb in enumerate(["Settings", "Fine Tuning", "Pause", "Cancel"]):
            bar.attach(bar_button(lb, img_scale, 1.38), i, 0, 1, 1)
        grid.attach(bar, 0, 3, 4, 1)
        outer.pack_start(grid, True, True, 0)
    else:  # current: own homogeneous box, icon-only at scale .7
        bar = Gtk.Box(homogeneous=True, spacing=4, vexpand=False)
        for _ in range(4):
            bar.add(bar_button(None, img_scale, 0.7))
        outer.pack_start(grid, True, True, 0)
        outer.pack_end(bar, False, False, 0)

    win.add(outer)
    win.set_size_request(int(content_w), h)
    win.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()
    return content_w, bar.get_preferred_width()[0]


PANELS = [(320, 240), (400, 240), (480, 272), (480, 320), (640, 480), (800, 480), (1024, 600)]

if __name__ == "__main__":
    print(f"{'panel':>12} {'content':>8} | {'OLD':>10} {'':>6} | {'NEW':>10} {'':>6}")
    problems = []
    for w, h in PANELS:
        content_w, old_need = measure(w, h, old=True)
        _, new_need = measure(w, h, old=False)
        old_fits, new_fits = old_need <= content_w, new_need <= content_w
        print(f"{w}x{h:<7} {content_w:8.0f} | {old_need:10.0f} {'fits' if old_fits else 'CLIPS':>6}"
              f" | {new_need:10.0f} {'fits' if new_fits else 'CLIPS':>6}")
        if new_need > old_need:
            problems.append(f"{w}x{h}: bar got wider ({new_need} > {old_need})")
        if not new_fits:
            problems.append(f"{w}x{h}: bar clips ({new_need}px needed, {content_w}px available)")

    assert not problems, "control bar regressed:\n  " + "\n  ".join(problems)
    print("\nPASS: all four print actions fit at every panel size, down to 320x240.")
