#!/usr/bin/env python3
"""Regression check for the job-status control bar.

The control bar used to be row 3 of `self.grid`, competing with the progress ring and
the 5-row info grid for space. On the IR3 V2's 800x480 panel that grid needed 429px of
the 425px content height, so the bar was allocated y=336..429 and its bottom edge fell
outside the visible area — the print controls were unreachable mid-print.

The fix packs the bar into its own homogeneous Gtk.Box, pack_end'd under the grid, so it
reserves its natural height at the bottom *first* and the grid absorbs the squeeze. The
four print actions are icon-only, which shrinks the bar on both axes.

Height is the binding constraint at 800x480; width binds on narrow panels. This checks
BOTH with real GTK geometry at the panel's font metrics (KlippyGtk font_ratio [27, 18],
font_size=large). Run under `xvfb-run -a python3 test_control_bar.py`.
"""
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gtk


def metrics(w, h):
    """Mirrors KlippyGtk.__init__ for this repo's font_ratio, horizontal, font_size=large.

    The ux chrome (panel_base.py) drops the left action rail, so content spans the full
    width; the titlebar (font*2) is the only vertical chrome.
    """
    font = min(w / 27, h / 18) * 1.025
    img_scale = font * 2 * 0.85
    return font, img_scale, w, h - font * 2


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
    font, img_scale, content_w, content_h = metrics(w, h)
    # size the window to the CONTENT box, not the panel: that is what the panel is given
    # after the titlebar. Do not set_default_size — it would override the request and the
    # bar would always appear to land at the bottom of a full-height window.
    win = Gtk.OffscreenWindow()
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
    win.set_size_request(int(content_w), int(content_h))
    win.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()

    alloc = bar.get_allocation()
    return {
        "content_w": content_w,
        "content_h": content_h,
        "need_w": bar.get_preferred_width()[0],
        "need_h": outer.get_preferred_height()[0],       # whole panel column
        "bar_bottom": alloc.y + alloc.height,            # where the bar actually lands
    }


# 800x480 is the real IR3 V2 panel — the one that clipped. The rest guard other builds.
PANELS = [(320, 240), (400, 240), (480, 272), (480, 320), (640, 480), (800, 480), (1024, 600)]


def verdict(m):
    """The bar is reachable only if it fits horizontally AND lands inside the content box."""
    return m["need_w"] <= m["content_w"] and m["bar_bottom"] <= m["content_h"] + 1


if __name__ == "__main__":
    print(f"{'panel':>11} {'avail w x h':>13} | {'OLD w/h/bottom':>20} {'':>7}"
          f" | {'NEW w/h/bottom':>20} {'':>7}")
    problems = []
    for w, h in PANELS:
        old, new = measure(w, h, old=True), measure(w, h, old=False)
        ok_old, ok_new = verdict(old), verdict(new)
        tag = " <- IR3 V2" if (w, h) == (800, 480) else ""
        print(f"{w}x{h:<6} {old['content_w']:6.0f} x{old['content_h']:5.0f} |"
              f" {old['need_w']:5.0f}/{old['need_h']:4.0f}/{old['bar_bottom']:5.0f}"
              f" {'ok' if ok_old else 'CLIPS':>7} |"
              f" {new['need_w']:5.0f}/{new['need_h']:4.0f}/{new['bar_bottom']:5.0f}"
              f" {'ok' if ok_new else 'CLIPS':>7}{tag}")

        # Assert only where the job panel can fit at all. Below 480px of height the info
        # grid alone (5 rows of buttons) overflows the content box no matter how the bar
        # is packed — a pre-existing limit this change reduces but does not solve.
        if h >= 480 and not ok_new:
            problems.append(
                f"{w}x{h}: control bar unreachable — needs {new['need_w']:.0f}x{new['need_h']:.0f}px, "
                f"bar bottom at {new['bar_bottom']:.0f} vs content height {new['content_h']:.0f}")
        # the bar must never demand more room than the layout it replaced, at any size
        if new["need_w"] > old["need_w"] or new["need_h"] > old["need_h"]:
            problems.append(f"{w}x{h}: bar grew vs the layout it replaced")

    assert not problems, "control bar regressed:\n  " + "\n  ".join(problems)
    print("\nPASS: bar is smaller on both axes everywhere, and fully reachable at >=480px height")
    print("      (including the IR3 V2's 800x480). Panels under 480px tall overflow in the")
    print("      info grid regardless — out of scope for this fix.")
