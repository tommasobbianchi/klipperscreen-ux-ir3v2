import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
from datetime import datetime
from ks_includes.screen_panel import ScreenPanel
from ks_includes.KlippyGtk import find_widget
from ks_includes.widgets.flowboxchild_extended import PrintListItem


def format_label(widget):
    label = find_widget(widget, Gtk.Label)
    if label is not None:
        label.set_line_wrap_mode(Pango.WrapMode.CHAR)
        label.set_line_wrap(True)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_lines(3)


class Panel(ScreenPanel):
    def __init__(self, screen, title):
        title = title or (_("Print") if self._printer.extrudercount > 0 else _("Gcodes"))
        super().__init__(screen, title)
        sortdir = self._config.get_main_config().get("print_sort_dir", "name_asc")
        sortdir = sortdir.split('_')
        self.sort_items = {
            "name": _("Name"),
            "date": _("Date"),
            "size": _("Size"),
        }
        if sortdir[0] not in self.sort_items or sortdir[1] not in ["asc", "desc"]:
            sortdir = ["name", "asc"]
        self.sort_current = [sortdir[0], 0 if sortdir[1] == "asc" else 1]  # 0 for asc, 1 for desc
        self.sort_icon = ["arrow-up", "arrow-down"]
        self.source = ""
        self.time_24 = self._config.get_main_config().getboolean("24htime", True)
        self.showing_rename = False
        self.loading = False
        self.cur_directory = 'gcodes'
        self.list_button_size = self._gtk.img_scale * self.bts

        self.headerbox = Gtk.Box(hexpand=True, vexpand=False)
        n = 0
        for name, val in self.sort_items.items():
            s = self._gtk.Button(None, val, f"color{n % 4 + 1}", .5, Gtk.PositionType.RIGHT, 1)
            s.get_style_context().add_class("buttons_slim")
            if name == self.sort_current[0]:
                s.set_image(self._gtk.Image(self.sort_icon[self.sort_current[1]], self._gtk.img_scale * self.bts))
            s.connect("clicked", self.change_sort, name)
            self.labels[f'sort_{name}'] = s
            self.headerbox.add(s)
            n += 1

        self.refresh = self._gtk.Button("refresh", style=f"color{n % 4 + 1}", scale=self.bts)
        self.refresh.get_style_context().add_class("buttons_slim")
        self.refresh.connect('clicked', self._refresh_files)
        n += 1
        self.headerbox.add(self.refresh)

        self.switch_mode = self._gtk.Button("fine-tune", style=f"color{n % 4 + 1}", scale=self.bts)
        self.switch_mode.get_style_context().add_class("buttons_slim")
        self.switch_mode.connect('clicked', self.switch_view_mode)
        n += 1
        self.headerbox.add(self.switch_mode)

        self.loading_msg = _('Loading...')
        self.labels['path'] = Gtk.Label(label=self.loading_msg, vexpand=True, no_show_all=True)
        self.labels['path'].show()
        self.thumbsize = self._screen.width / 5
        logging.info(f"Thumbsize: {self.thumbsize:.1f}")

        # u1 pager: exactly one item per page, full width, up/down on the far right
        self.items = []
        self.index = 0
        self.card_holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)

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

        self.main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        self.main.add(self.labels['path'])
        self.main.add(body)
        self.content.add(self.main)
        self.set_loading(True)
        self._screen._ws.klippy.get_dir_info(self.load_files, self.cur_directory)

    def switch_view_mode(self, widget):
        self.list_mode ^= True
        logging.info(f"lista {self.list_mode}")
        if self.list_mode:
            self.flowbox.set_min_children_per_line(1)
            self.flowbox.set_max_children_per_line(1)
        else:
            columns = 3 if self._screen.vertical_mode else 4
            self.flowbox.set_min_children_per_line(columns)
            self.flowbox.set_max_children_per_line(columns)
        self._config.set("main", "print_view", 'list' if self.list_mode else 'thumbs')
        self._config.save_user_config_options()
        self._refresh_files()

    def activate(self):
        if self.cur_directory != "gcodes":
            self.change_dir()
        self._screen.files.add_callback(self._callback)

    def deactivate(self):
        self._screen.files.remove_callback(self._callback)

    def create_item(self, item):
        fbchild = PrintListItem()
        fbchild.set_date(item['modified'])
        fbchild.set_size(item['size'])
        if 'dirname' in item:
            if item['dirname'].startswith("."):
                return
            name = item['dirname']
            path = f"{self.cur_directory}/{name}"
            fbchild.set_as_dir(True)
        elif 'filename' in item:
            if (item['filename'].startswith(".") or
                    os.path.splitext(item['filename'])[1] not in {'.gcode', '.gco', '.g'}):
                return
            name = item['filename']
            path = f"{self.cur_directory}/{name}"
            path = path.replace('gcodes/', '')
        else:
            logging.error(f"Unknown item {item}")
            return
        basename = os.path.splitext(name)[0]
        fbchild.set_path(path)
        fbchild.set_name(basename.casefold())
        if self.list_mode:
            itemname = Gtk.Label(
                hexpand=True, halign=Gtk.Align.CENTER, justify=Gtk.Justification.CENTER,
                wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, lines=2,
                ellipsize=Pango.EllipsizeMode.END,
            )
            itemname.get_style_context().add_class("print-filename")
            itemname.set_markup(f"<big><b>{basename}</b></big>")
            icon = Gtk.Button(hexpand=True, vexpand=True)
            # name UNDER the thumbnail, full width -> room for long names
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True,
                           valign=Gtk.Align.CENTER)
            card.get_style_context().add_class("frame-item")
            card.pack_start(icon, True, True, 0)
            card.pack_start(itemname, False, False, 0)
            imgsize = int(self._screen.height * 0.55)
            # tap the thumbnail -> print/delete dialog (files) or open (folders)
            if 'filename' in item:
                icon.connect("clicked", self.confirm_print, path)
                image_args = (path, icon, imgsize, True, "file")
            elif 'dirname' in item:
                icon.connect("clicked", self.change_dir, path)
                image_args = (None, icon, imgsize, True, "folder")
            else:
                return
            fbchild.add(card)
            fbchild.set_size_request(-1, self.item_h)
        else:  # Thumbnail view
            icon = self._gtk.Button(label=basename)
            if 'filename' in item:
                icon.connect("clicked", self.confirm_print, path)
                image_args = (path, icon, self.thumbsize, False, "file")
            elif 'dirname' in item:
                icon.connect("clicked", self.change_dir, path)
                image_args = (None, icon, self.thumbsize, False, "folder")
            else:
                return
            fbchild.add(icon)
        self.image_load(*image_args)
        return fbchild

    def show_path(self):
        self.labels['path'].set_vexpand(False)
        if self.cur_directory == 'gcodes':
            self.labels['path'].hide()
        else:
            self.labels['path'].set_text(self.cur_directory)
            self.labels['path'].show()

    def image_load(self, filepath, widget, size=-1, small=True, iconname=None):
        pixbuf = self.get_file_image(filepath, size, size, small)
        if pixbuf is not None:
            widget.set_image(Gtk.Image.new_from_pixbuf(pixbuf))
        elif iconname is not None:
            widget.set_image(self._gtk.Image(iconname, size, size))
        format_label(widget)

    def confirm_delete_file(self, widget, filepath):
        logging.debug(f"Sending delete_file {filepath}")
        params = {"path": f"{filepath}"}
        self._screen._confirm_send_action(
            None,
            _("Delete File?") + "\n\n" + filepath,
            "server.files.delete_file",
            params
        )

    def confirm_delete_directory(self, widget, dirpath):
        logging.debug(f"Sending delete_directory {dirpath}")
        params = {"path": f"{dirpath}", "force": True}
        self._screen._confirm_send_action(
            None,
            _("Delete Directory?") + "\n\n" + dirpath,
            "server.files.delete_directory",
            params
        )

    def back(self):
        if self.showing_rename:
            self.hide_rename()
            return True
        if self.cur_directory != 'gcodes':
            self.change_dir(None, os.path.dirname(self.cur_directory))
            return True
        return False

    def nav_up(self, widget=None):
        if self.items:
            self.index = (self.index - 1) % len(self.items)
            self.show_current()

    def nav_down(self, widget=None):
        if self.items:
            self.index = (self.index + 1) % len(self.items)
            self.show_current()

    def change_dir(self, widget=None, directory='gcodes'):
        if directory == '':
            directory = 'gcodes'
        if directory != self.cur_directory:
            logging.info(f'Changing directory to: {directory}')
            self.cur_directory = directory
        self.show_path()
        self._refresh_files()

    def change_sort(self, widget, key):
        if self.sort_current[0] == key:
            self.sort_current[1] = (self.sort_current[1] + 1) % 2
        else:
            oldkey = self.sort_current[0]
            logging.info(f"Changing from {oldkey} to {key}")
            self.labels[f'sort_{oldkey}'].set_image(None)
            self.labels[f'sort_{oldkey}'].show_all()
            self.sort_current = [key, 0]
        self.labels[f'sort_{key}'].set_image(self._gtk.Image(self.sort_icon[self.sort_current[1]],
                                                             self._gtk.img_scale * self.bts))
        self.labels[f'sort_{key}'].show()

        self.set_sort()

        self._config.set("main", "print_sort_dir", f'{key}_{"asc" if self.sort_current[1] == 0 else "desc"}')
        self._config.save_user_config_options()

    def set_sort(self):
        reverse = self.sort_current[1] != 0
        if self.sort_current[0] == "name":
            self.flowbox.set_sort_func(self.sort_names, reverse)
        elif self.sort_current[0] == "date":
            self.flowbox.set_sort_func(self.sort_dates, reverse)
        elif self.sort_current[0] == "size":
            self.flowbox.set_sort_func(self.sort_sizes, reverse)

    @staticmethod
    def sort_names(a: PrintListItem, b: PrintListItem, reverse):
        if a.get_is_dir() - b.get_is_dir() != 0:
            return a.get_is_dir() - b.get_is_dir()
        if a.get_name() < b.get_name():
            return 1 if reverse else -1
        if a.get_name() > b.get_name():
            return -1 if reverse else 1
        return 0

    @staticmethod
    def sort_sizes(a: PrintListItem, b: PrintListItem, reverse):
        if a.get_is_dir() - b.get_is_dir() != 0:
            return a.get_is_dir() - b.get_is_dir()
        return b.get_size() - a.get_size() if reverse else a.get_size() - b.get_size()

    @staticmethod
    def sort_dates(a: PrintListItem, b: PrintListItem, reverse):
        if a.get_is_dir() - b.get_is_dir() != 0:
            return a.get_is_dir() - b.get_is_dir()
        return b.get_date() - a.get_date() if reverse else a.get_date() - b.get_date()

    def confirm_print(self, widget, filename):
        action = _("Print") if self._printer.extrudercount > 0 else _("Start")

        buttons = [
            {"name": _("Delete"), "response": Gtk.ResponseType.REJECT, "style": 'dialog-error'},
            {"name": action, "response": Gtk.ResponseType.OK, "style": 'dialog-primary'},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL, "style": 'dialog-secondary'}
        ]

        label = Gtk.Label(
            hexpand=True, vexpand=True, lines=2,
            wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR,
            ellipsize=Pango.EllipsizeMode.END
        )
        label.set_markup(f"<b>{filename}</b>")

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        main_box.pack_start(label, False, False, 0)

        orientation = Gtk.Orientation.VERTICAL if self._screen.vertical_mode else Gtk.Orientation.HORIZONTAL
        inside_box = Gtk.Box(orientation=orientation, vexpand=True)

        if self._screen.vertical_mode:
            width = self._screen.width * .9
            height = (self._screen.height - self._gtk.dialog_buttons_height - self._gtk.font_size * 5) * .45
        else:
            width = self._screen.width * .5
            height = (self._screen.height - self._gtk.dialog_buttons_height - self._gtk.font_size * 6)
        pixbuf = self.get_file_image(filename, width, height)
        if pixbuf is not None:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image_button = self._gtk.Button()
            image_button.set_image(image)
            image_button.connect("clicked", self.show_fullscreen_thumbnail, filename)
            inside_box.pack_start(image_button, True, True, 0)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        fileinfo = Gtk.Label(
            label=self.get_file_info_extended(filename), use_markup=True, ellipsize=Pango.EllipsizeMode.END
        )
        info_box.pack_start(fileinfo, True, True, 0)

        inside_box.pack_start(info_box, True, True, 0)
        main_box.pack_start(inside_box, True, True, 0)
        self._gtk.Dialog(f'{action} {filename}', buttons, main_box, self.confirm_print_response, filename)

    def confirm_print_response(self, dialog, response_id, filename):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.CANCEL:
            return
        elif response_id == Gtk.ResponseType.OK:
            logging.info(f"Starting print: {filename}")
            self._screen._ws.klippy.print_start(filename)
        elif response_id == Gtk.ResponseType.REJECT:
            self.confirm_delete_file(None, f"gcodes/{filename}")

    def get_info_str(self, item, path):
        info = ""
        if "modified" in item:
            info += _("Modified")
            if self.time_24:
                info += f':<b> {datetime.fromtimestamp(item["modified"]):%Y/%m/%d %H:%M}</b>\n'
            else:
                info += f':<b> {datetime.fromtimestamp(item["modified"]):%Y/%m/%d %I:%M %p}</b>\n'
        if "size" in item:
            info += _("Size") + f': <b>{self.format_size(item["size"])}</b>\n'
        if 'filename' in item:
            info += self.get_file_info(path)
        return info

    def get_file_info(self, path):
        info = ""
        fileinfo = self._screen.files.get_file_info(path)
        if "layer_height" in fileinfo:
            info += _("Layer Height") + f': <b>{fileinfo["layer_height"]}</b> ' + _("mm") + '\n'
        if "filament_type" in fileinfo:
            info += _("Filament") + f': <b>{fileinfo["filament_type"]}</b>\n'
        if "filament_name" in fileinfo:
            info += f'<b>{fileinfo["filament_name"]}</b>\n'
        if "estimated_time" in fileinfo:
            info += _("Estimated Time") + f': <b>{self.format_time(fileinfo["estimated_time"])}</b>'
        return info

    def get_file_info_extended(self, filename):
        fileinfo = self._screen.files.get_file_info(filename)
        info = ""
        if "modified" in fileinfo:
            info += _("Modified")
            if self.time_24:
                info += f':<b> {datetime.fromtimestamp(fileinfo["modified"]):%Y/%m/%d %H:%M}</b>\n'
            else:
                info += f':<b> {datetime.fromtimestamp(fileinfo["modified"]):%Y/%m/%d %I:%M %p}</b>\n'
        if "layer_height" in fileinfo:
            info += _("Layer Height") + f': <b>{fileinfo["layer_height"]}</b> ' + _("mm") + '\n'
        if "filament_type" in fileinfo or "filament_name" in fileinfo:
            info += _("Filament") + ':\n'
        if "filament_type" in fileinfo:
            info += f'    <b>{fileinfo["filament_type"]}</b>\n'
        if "filament_name" in fileinfo:
            info += f'    <b>{fileinfo["filament_name"]}</b>\n'
        if "filament_weight_total" in fileinfo:
            info += f'    <b>{fileinfo["filament_weight_total"]:.2f}</b> ' + _("g") + '\n'
        if "nozzle_diameter" in fileinfo:
            info += _("Nozzle diameter") + f': <b>{fileinfo["nozzle_diameter"]}</b> ' + _("mm") + '\n'
        if "slicer" in fileinfo:
            info += (
                _("Slicer") +
                f': <b>{fileinfo["slicer"]} '
                f'{fileinfo["slicer_version"] if "slicer_version" in fileinfo else ""}</b>\n'
            )
        if "size" in fileinfo:
            info += _("Size") + f': <b>{self.format_size(fileinfo["size"])}</b>\n'
        if "estimated_time" in fileinfo:
            info += _("Estimated Time") + f': <b>{self.format_time(fileinfo["estimated_time"])}</b>\n'
        if "job_id" in fileinfo:
            history = self._screen.apiclient.send_request(f"server/history/job?uid={fileinfo['job_id']}")
            if history and history['job']['status'] == "completed":
                info += _("Last Duration") + f": <b>{self.format_time(history['job']['print_duration'])}</b>"
        return info

    def load_files(self, result, method, params):
        self.set_loading(True)
        if not result.get("result") or not isinstance(result["result"], dict):
            logging.info(result)
            return
        raw = [*result["result"]["dirs"], *result["result"]["files"]]
        self.items = [e for e in (self._entry(i) for i in raw) if e]
        self.items.sort(key=lambda e: (not e["is_dir"], e["name"].casefold()))
        self.index = 0
        self.set_loading(False)
        self.show_current()

    def _entry(self, item):
        if 'dirname' in item:
            if item['dirname'].startswith("."):
                return None
            name = item['dirname']
            return {"is_dir": True, "name": name, "basename": name,
                    "path": f"{self.cur_directory}/{name}"}
        if 'filename' in item:
            fn = item['filename']
            if fn.startswith(".") or os.path.splitext(fn)[1] not in {'.gcode', '.gco', '.g'}:
                return None
            path = f"{self.cur_directory}/{fn}".replace('gcodes/', '')
            return {"is_dir": False, "name": fn, "basename": os.path.splitext(fn)[0], "path": path}
        return None

    def show_current(self):
        for child in self.card_holder.get_children():
            self.card_holder.remove(child)
        if not self.items:
            self.card_holder.add(Gtk.Label(label=_("No files"), hexpand=True, vexpand=True))
            self.card_holder.show_all()
            return
        self.index = max(0, min(self.index, len(self.items) - 1))
        e = self.items[self.index]
        name = Gtk.Label(hexpand=True, halign=Gtk.Align.CENTER, justify=Gtk.Justification.CENTER,
                         wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, lines=2,
                         ellipsize=Pango.EllipsizeMode.END)
        name.get_style_context().add_class("print-filename")
        name.set_markup(f"<big><b>{e['basename']}</b></big>")
        icon = Gtk.Button(hexpand=True, vexpand=True)
        icon.get_style_context().add_class("frame-item")
        imgsize = int(self._screen.height * 0.6)
        if e["is_dir"]:
            icon.connect("clicked", self.change_dir, e["path"])
            self.image_load(None, icon, imgsize, True, "folder")
        else:
            icon.connect("clicked", self.confirm_print, e["path"])
            self.image_load(e["path"], icon, imgsize, True, "file")
        self.card_holder.pack_start(icon, True, True, 0)
        self.card_holder.pack_start(name, False, False, 0)
        self.card_holder.show_all()

    def delete_from_list(self, path):
        # pager: a file/dir changed -> just reload the current directory
        self._refresh_files()
        return True

    def add_item_from_callback(self, action, data):
        self._refresh_files()

    def _callback(self, action, data):
        logging.info(f"{action}: {data}")
        if action in {"create_dir", "create_file"}:
            self.add_item_from_callback(action, data)
        elif action == "delete_file":
            self.delete_from_list(data['item']["path"])
        elif action == "delete_dir":
            self.delete_from_list(os.path.join("gcodes", data['item']["path"]))
        elif action in {"modify_file", "move_file", "move_dir"}:
            if "path" in data['item'] and data['item']["path"].startswith("gcodes/"):
                data['item']["path"] = data['item']["path"][7:]
            self.add_item_from_callback(action, data)

    def _refresh_files(self, *args):
        logging.info("Refreshing")
        self.set_loading(True)
        self._screen._ws.klippy.get_dir_info(self.load_files, self.cur_directory)

    def set_loading(self, loading):
        self.loading = loading
        for child in self.headerbox.get_children():
            child.set_sensitive(not loading)
        self._gtk.Button_busy(self.refresh, loading)
        if loading:
            self.labels['path'].set_text(self.loading_msg)
            self.labels['path'].show()
            return
        self.show_path()
        self.content.show_all()

    def show_rename(self, widget, fullpath):
        self.source = fullpath
        logging.info(self.source)

        for child in self.content.get_children():
            self.content.remove(child)

        if "rename_file" not in self.labels:
            self._create_rename_box(fullpath)
        self.content.add(self.labels['rename_file'])
        self.labels['new_name'].set_text(fullpath[7:])
        self.labels['new_name'].grab_focus_without_selecting()
        self.showing_rename = True

    def _create_rename_box(self, fullpath):
        lbl = Gtk.Label(label=_("Rename/Move:"), halign=Gtk.Align.START, hexpand=False)
        self.labels['new_name'] = Gtk.Entry(text=fullpath, hexpand=True)
        self.labels['new_name'].connect("activate", self.rename)
        self.labels['new_name'].connect("focus-in-event", self._screen.show_keyboard)

        save = self._gtk.Button("complete", _("Save"), "color3")
        save.set_hexpand(False)
        save.connect("clicked", self.rename)

        box = Gtk.Box()
        box.pack_start(self.labels['new_name'], True, True, 5)
        box.pack_start(save, False, False, 5)

        self.labels['rename_file'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5,
                                             hexpand=True, vexpand=True, valign=Gtk.Align.CENTER)
        self.labels['rename_file'].pack_start(lbl, True, True, 5)
        self.labels['rename_file'].pack_start(box, True, True, 5)

    def hide_rename(self):
        self._screen.remove_keyboard()
        for child in self.content.get_children():
            self.content.remove(child)
        self.content.add(self.main)
        self.content.show()
        self.showing_rename = False

    def rename(self, widget):
        params = {"source": self.source, "dest": f"gcodes/{self.labels['new_name'].get_text()}"}
        self._screen._send_action(
            widget,
            "server.files.move",
            params
        )
        self.back()

    def show_fullscreen_thumbnail(self, widget, filename):
        pixbuf = self.get_file_image(filename, self._screen.width * .9, self._screen.height * .75)
        if pixbuf is None:
            return
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_vexpand(True)
        self._gtk.Dialog(filename, None, image, self.close_fullscreen_thumbnail)

    def close_fullscreen_thumbnail(self, dialog, response_id):
        self._gtk.remove_dialog(dialog)
