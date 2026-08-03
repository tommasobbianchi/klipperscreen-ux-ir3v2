# u1 Home — KlipperScreen main menu reflowed into the flat tool-changer idiom.
# Original work for the IdeaFormer IR3 V2. Reproduces the U1 home *layout*
# (left icon column + tool chip + message/Start card), not a colour theme.
# Subclasses MenuPanel so the full __main menu stays reachable behind the
# settings icon — nothing the printer needs is removed.
import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from panels.menu import Panel as MenuPanel


class Panel(MenuPanel):
    def __init__(self, screen, title, items=None):
        super().__init__(screen, title, items)
        self.items = items
        self.home = self.build_home()
        self.content.add(self.home)

    # ---- layout ---------------------------------------------------------
    def build_home(self):
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                       hexpand=True, vexpand=True)
        root.get_style_context().add_class("u1-home")

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left.set_valign(Gtk.Align.START)
        for icon, cb in (("settings", self.show_grid),
                         ("sd", lambda w: self.go("gcodes")),
                         ("filament", lambda w: self.go("infinity_flow"))):
            b = self._gtk.Button(icon, None, "u1-icon", scale=1.1)
            b.set_hexpand(False)
            b.set_vexpand(False)
            b.connect("clicked", cb)
            left.add(b)
        root.add(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                        hexpand=True, vexpand=True)
        tool_row = self.build_tool_row()
        tool_row.set_vexpand(False)
        tool_row.set_valign(Gtk.Align.START)
        right.add(tool_row)
        right.add(self.build_start_card())
        root.add(right)
        return root

    def build_tool_row(self):
        # single-extruder printer: one honest chip, not a fake 4-up row
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        row.get_style_context().add_class("u1-card")
        n = self._printer.extrudercount if hasattr(self._printer, "extrudercount") else 1
        for i in range(max(1, n)):
            chip_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            chip_box.set_halign(Gtk.Align.CENTER)
            lbl = Gtk.Label(label=_("Tool"))
            lbl.get_style_context().add_class("u1-tool-label")
            chip = self._gtk.Button(None, str(i + 1), "u1-chip", scale=0.7)
            chip.set_hexpand(False)
            chip.set_vexpand(False)
            chip.set_halign(Gtk.Align.CENTER)
            chip.set_valign(Gtk.Align.CENTER)
            chip.connect("clicked", lambda w: self.go("temperature"))
            chip_box.add(lbl)
            chip_box.add(chip)
            row.add(chip_box)
        row.set_halign(Gtk.Align.START)
        return row

    def build_start_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10,
                       hexpand=True, vexpand=True)
        card.get_style_context().add_class("u1-card")
        msg = Gtk.Label(label=_("Ready when you are."), hexpand=True, xalign=0.0)
        msg.get_style_context().add_class("u1-msg")
        msg.set_line_wrap(True)
        start = self._gtk.Button(None, _("Start"), "u1-start")
        start.set_hexpand(False)
        start.set_vexpand(False)
        start.set_halign(Gtk.Align.END)
        start.set_valign(Gtk.Align.END)
        start.connect("clicked", lambda w: self.go("gcodes"))
        card.add(msg)
        card.add(start)
        return card

    # ---- navigation -----------------------------------------------------
    def go(self, panel):
        try:
            self._screen.show_panel(panel, title=None)
        except Exception as e:
            logging.exception(f"u1 home: cannot open {panel}: {e}")

    def show_grid(self, widget=None):
        # push the full __main menu as a native panel: KlipperScreen's own
        # back button then returns here (no in-panel reparenting).
        items = self._config.get_menu_items("__main")
        if items:
            self._screen.show_panel("menu", _("Menu"), panel_name="u1_menu", items=items)
