import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
from ks_includes.screen_panel import ScreenPanel


class Panel(ScreenPanel):

    def __init__(self, screen, title):
        title = title or _("Limits")
        super().__init__(screen, title)
        self.limits = {}
        self.options = None
        self.values = {}
        self.grid = Gtk.Grid()

        conf = self._printer.get_config_section("printer")
        self.options = [
            {
                "name": _("Max Acceleration"),
                "option": "max_accel",
                "units": _("mm/s²"),
                "value": int(float(conf['max_accel']))
            },
            {
                "name": _("Minimum Cruise Ratio"),
                "option": "minimum_cruise_ratio",
                "units": "%",
                "value": int(float(conf['minimum_cruise_ratio']) * 100) if "minimum_cruise_ratio" in conf else 50,
                "max": 99
            },
            {
                "name": _("Max Velocity"),
                "option": "max_velocity",
                "units": _("mm/s"),
                "value": int(float(conf["max_velocity"]))},
            {
                "name": _("Square Corner Velocity"),
                "option": "square_corner_velocity",
                "units": _("mm/s"),
                "value": int(float(conf['square_corner_velocity'])) if "square_corner_velocity" in conf else 5
            }
        ]

        for opt in self.options:
            self.add_option(opt)

        # u1 pager: one limit per screen, up/down on the far right (no scroll)
        self.order = [o['option'] for o in self.options]
        self.index = 0
        self.card_holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True,
                                   valign=Gtk.Align.CENTER)
        up = self._gtk.Button("arrow-up", scale=self.bts)
        up.connect("clicked", self.nav_up)
        down = self._gtk.Button("arrow-down", scale=self.bts)
        down.connect("clicked", self.nav_down)
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=False, vexpand=True,
                      halign=Gtk.Align.END)
        nav.pack_start(up, True, True, 0)
        nav.pack_start(down, True, True, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
        body.pack_start(self.card_holder, True, True, 0)
        body.pack_end(nav, False, False, 0)
        self.content.add(body)
        self.show_current()
        self.content.show_all()

    def show_current(self):
        for child in self.card_holder.get_children():
            self.card_holder.remove(child)
        opt = self.order[self.index]
        row = self.limits[opt]['row']
        parent = row.get_parent()
        if parent is not None:
            parent.remove(row)
        row.set_vexpand(True)
        row.set_hexpand(True)
        row.set_valign(Gtk.Align.CENTER)
        self.card_holder.pack_start(row, True, True, 0)
        self.card_holder.show_all()

    def nav_up(self, widget=None):
        self.index = (self.index - 1) % len(self.order)
        self.show_current()

    def nav_down(self, widget=None):
        self.index = (self.index + 1) % len(self.order)
        self.show_current()

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        for opt in self.limits:
            if "toolhead" in data and opt in data["toolhead"]:
                self.update_option(opt, data["toolhead"][opt])

    def update_option(self, option, value):
        logging.info(f"{option} {value}")

        if option not in self.limits:
            logging.debug("not in self limits")
            return

        if self.limits[option]['scale'].has_grab():
            return
        if option == "minimum_cruise_ratio" and value < 1:
            self.values[option] = int(value * 100)
        else:
            self.values[option] = int(value)
        for opt in self.options:
            if opt["option"] == option and 'max' not in opt:
                if self.values[option] > opt["value"]:
                    self.limits[option]['scale'].get_style_context().add_class("option_slider_max")
                    # Infinite scale
                    self.limits[option]['adjustment'].set_upper(self.values[option] * 1.5)
                else:
                    self.limits[option]['scale'].get_style_context().remove_class("option_slider_max")
                    self.limits[option]['adjustment'].set_upper(opt["value"] * 1.5)
        self.limits[option]['scale'].disconnect_by_func(self.set_opt_value)
        self.limits[option]['scale'].set_value(self.values[option])
        self.limits[option]['scale'].connect("button-release-event", self.set_opt_value, option)

    def add_option(self, option):
        logging.info(f"Adding option: {option['option']}")

        name = Gtk.Label(hexpand=True, vexpand=True, halign=Gtk.Align.START, valign=Gtk.Align.CENTER,
                         wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
        name.set_markup(f"<big><b>{option['name']}</b></big> ({option['units']})")

        # adj (value, lower, upper, step_increment, page_increment, page_size)
        max_value = option['max'] if 'max' in option else option['value'] * 1.5
        adj = Gtk.Adjustment(option['value'], 1, max_value, 1, 5, 0)
        scale = Gtk.Scale(adjustment=adj, digits=0, hexpand=True, has_origin=True)
        scale.get_style_context().add_class("option_slider")
        scale.connect("button-release-event", self.set_opt_value, option)
        self.values[option['option']] = option['value']

        reset = self._gtk.Button("refresh", style="color1")
        reset.connect("clicked", self.reset_value, option['option'])
        reset.set_hexpand(False)

        item = Gtk.Grid()
        item.attach(name, 0, 0, 2, 1)
        item.attach(scale, 0, 1, 1, 1)
        item.attach(reset, 1, 1, 1, 1)

        self.limits[option['option']] = {
            "row": item,
            "scale": scale,
            "adjustment": adj,
        }

        limits = sorted(self.limits)
        pos = limits.index(option['option'])

        self.grid.insert_row(pos)
        self.grid.attach(self.limits[option['option']]['row'], 0, pos, 1, 1)
        self.grid.show_all()

    def reset_value(self, widget, option):
        for x in self.options:
            if x["option"] == option:
                self.update_option(option, x["value"])
                logging.debug(f"Reset {option} to {x['value']}")
        self.set_opt_value(None, None, option)

    def set_opt_value(self, widget, event, opt):
        value = self.limits[opt]['scale'].get_value()

        if opt == "max_accel":
            self._screen._ws.klippy.gcode_script(f"SET_VELOCITY_LIMIT ACCEL={value}")
        elif opt == "minimum_cruise_ratio":
            self._screen._ws.klippy.gcode_script(f"SET_VELOCITY_LIMIT MINIMUM_CRUISE_RATIO={value / 100}")
        elif opt == "max_velocity":
            self._screen._ws.klippy.gcode_script(f"SET_VELOCITY_LIMIT VELOCITY={value}")
        elif opt == "square_corner_velocity":
            self._screen._ws.klippy.gcode_script(f"SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY={value}")
