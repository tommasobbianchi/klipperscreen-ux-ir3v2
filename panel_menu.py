import json
import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from jinja2 import Template
from ks_includes.screen_panel import ScreenPanel
from ks_includes.widgets.autogrid import AutoGrid
from ks_includes.KlippyGtk import find_widget


class Panel(ScreenPanel):

    def __init__(self, screen, title, items=None):
        super().__init__(screen, title)
        self.items = items
        self.j2_data = self._printer.get_printer_status_data()
        self.create_menu_items()
        self.scroll = self._gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.autogrid = AutoGrid()

    def activate(self):
        self.j2_data = self._printer.get_printer_status_data()
        self.add_content()

    def add_content(self):
        for child in self.content.get_children():
            self.content.remove(child)
        enabled = [
            self.labels[list(item)[0]]
            for item in self.items
            if self.evaluate_enable(item[list(item)[0]]['enable'])
        ]
        # u1: menus that fit stay a 2x2 grid; longer menus page one tile per screen
        if len(enabled) <= 4:
            grid = self.arrangeMenuItems(self.items, 2, True)
            grid.set_vexpand(True)
            grid.set_hexpand(True)
            grid.set_valign(Gtk.Align.FILL)
            grid.set_halign(Gtk.Align.FILL)
            self.content.pack_start(grid, True, True, 0)
        else:
            self.add_pager(enabled)

    def add_pager(self, buttons):
        self.pitems = buttons
        self.pindex = max(0, min(getattr(self, 'pindex', 0), len(buttons) - 1))
        self.card_holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        up = self._gtk.Button("arrow-up", scale=self.bts)
        up.connect("clicked", self.pager_up)
        down = self._gtk.Button("arrow-down", scale=self.bts)
        down.connect("clicked", self.pager_down)
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=False, vexpand=True,
                      halign=Gtk.Align.END)
        nav.pack_start(up, True, True, 0)
        nav.pack_start(down, True, True, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
        body.pack_start(self.card_holder, True, True, 0)
        body.pack_end(nav, False, False, 0)
        self.content.pack_start(body, True, True, 0)
        self.pager_show()

    def pager_show(self):
        for child in self.card_holder.get_children():
            self.card_holder.remove(child)
        btn = self.pitems[self.pindex]
        parent = btn.get_parent()
        if parent is not None:
            parent.remove(btn)
        btn.set_hexpand(True)
        btn.set_vexpand(True)
        # scale only enlarges the icon; bump the label too so it isn't tiny on
        # a full-screen tile (Pango markup wins over the button's inline font)
        lbl = find_widget(btn, Gtk.Label)
        if lbl is not None and "<span" not in lbl.get_label():
            lbl.set_markup(f'<span size="xx-large"><b>{lbl.get_text()}</b></span>')
        self.card_holder.pack_start(btn, True, True, 0)
        self.card_holder.show_all()

    def pager_up(self, widget=None):
        self.pindex = (self.pindex - 1) % len(self.pitems)
        self.pager_show()

    def pager_down(self, widget=None):
        self.pindex = (self.pindex + 1) % len(self.pitems)
        self.pager_show()

    def arrangeMenuItems(self, items, columns=None, expand_last=False):
        self.autogrid.clear()
        enabled = []
        for item in items:
            key = list(item)[0]
            if not self.evaluate_enable(item[key]['enable']):
                logging.debug(f"X > {key}")
                continue
            enabled.append(self.labels[key])
        self.autogrid.__init__(enabled, columns, expand_last, self._screen.vertical_mode)
        return self.autogrid

    def create_menu_items(self):
        count = sum(bool(self.evaluate_enable(i[next(iter(i))]['enable'])) for i in self.items)
        # >4 items page one tile per screen -> big icon+text to fill the screen;
        # 4 or fewer stay a 2x2 grid at the normal tile size
        if count > 4:
            scale = 3.0
        elif count <= 6:
            scale = 1.3
        elif 12 < count <= 16:
            scale = 1.1
        else:
            scale = None
        for i in range(len(self.items)):
            key = list(self.items[i])[0]
            item = self.items[i][key]

            name = self._screen.env.from_string(item['name']).render(self.j2_data)
            icon = self._screen.env.from_string(item['icon']).render(self.j2_data) if item['icon'] else None
            style = self._screen.env.from_string(item['style']).render(self.j2_data) if item['style'] else None

            if icon == "notifications" and (
                bool(self._screen.server_info["warnings"])
                or bool(self._printer.warnings)
                or bool(self._screen.server_info["failed_components"])
                or bool(self._screen.server_info["missing_klippy_requirements"])
            ):
                icon = "notification_important"

            b = self._gtk.Button(icon, name, style or "u1-tile", scale=scale)

            if item['panel']:
                b.connect("clicked", self.menu_item_clicked, item)
            elif item['method']:
                params = {}

                if item['params'] is not False:
                    try:
                        p = self._screen.env.from_string(item['params']).render(self.j2_data)
                        params = json.loads(p)
                    except Exception as e:
                        logging.exception(f"Unable to parse parameters for [{name}]:\n{e}")
                        params = {}

                if item['confirm'] is not None:
                    b.connect("clicked", self._screen._confirm_send_action, item['confirm'], item['method'], params)
                else:
                    b.connect("clicked", self._screen._send_action, item['method'], params)
            else:
                b.connect("clicked", self._screen._go_to_submenu, key)
            self.labels[key] = b

    def evaluate_enable(self, enable):
        if enable == "{{ moonraker_connected }}":
            logging.info(f"moonraker connected {self._screen._ws.connected}")
            return self._screen._ws.connected
        try:
            j2_temp = Template(enable, autoescape=True)
            return j2_temp.render(self.j2_data) == 'True'
        except Exception as e:
            logging.debug(f"Error evaluating enable statement: {enable}\n{e}")
            return False
