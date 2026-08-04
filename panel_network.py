import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel
from ks_includes.sdbus_nm import SdbusNm
from datetime import datetime


class Panel(ScreenPanel):

    def __init__(self, screen, title):
        title = title or _("Network")
        super().__init__(screen, title)
        self.last_drop_time = datetime.now()
        self.show_add = False
        try:
            self.sdbus_nm = SdbusNm(self.popup_callback)
        except Exception as e:
            logging.exception("Failed to initialize")
            self.sdbus_nm = None
            self.error_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                hexpand=True,
                vexpand=True
            )
            message = (
                _("Failed to initialize") + "\n"
                + "This panel needs NetworkManager installed into the system\n"
                + "And the apropriate permissions, without them it will not function.\n"
                + f"\n{e}\n"
            )
            self.error_box.add(
                Gtk.Label(
                    label=message,
                    wrap=True,
                    wrap_mode=Pango.WrapMode.WORD_CHAR,
                )
            )
            self.error_box.set_valign(Gtk.Align.CENTER)
            self.content.add(self.error_box)
            self._screen.panels_reinit.append(self._screen._cur_panels[-1])
            return
        self.update_timeout = None

        self.network_interfaces = self.sdbus_nm.get_interfaces()
        self.wireless_interfaces = [iface.interface for iface in self.sdbus_nm.get_wireless_interfaces()]
        self.interface = self.sdbus_nm.get_primary_interface()

        # ---- compact header: interface / IP + reload + wifi toggle ----
        self.labels['interface'] = Gtk.Label(hexpand=True, halign=Gtk.Align.START)
        self.labels['ip'] = Gtk.Label(hexpand=True, halign=Gtk.Align.START)
        if self.interface is not None:
            self.labels['interface'].set_text(_("Interface") + f': {self.interface}')
            self.labels['ip'].set_text(f"IP: {self.sdbus_nm.get_ip_address()}")

        self.reload_button = self._gtk.Button("refresh", None, "color1", self.bts)
        self.reload_button.set_no_show_all(True)
        self.reload_button.show()
        self.reload_button.connect("clicked", self.reload_networks)
        self.reload_button.set_hexpand(False)

        self.wifi_toggle = Gtk.Switch(
            width_request=round(self._gtk.font_size * 2),
            height_request=round(self._gtk.font_size),
            active=self.sdbus_nm.is_wifi_enabled()
        )
        self.wifi_toggle.set_valign(Gtk.Align.CENTER)
        self.wifi_toggle.connect("notify::active", self.toggle_wifi)

        sbox = Gtk.Box(hexpand=True, vexpand=False, spacing=8)
        sbox.add(self.labels['interface'])
        sbox.add(self.labels['ip'])
        sbox.add(self.reload_button)
        sbox.add(self.wifi_toggle)

        # ---- u1 pager: exactly one network per page, up/down on the far right ----
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

        self.labels['main_box'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)

        if self.sdbus_nm.wifi:
            self.labels['main_box'].pack_start(sbox, False, False, 5)
            self.labels['main_box'].pack_start(body, True, True, 0)
            GLib.idle_add(self.load_networks)
            self.sdbus_nm.enable_monitoring(True)
            self.conn_status = GLib.timeout_add_seconds(1, self.sdbus_nm.monitor_connection_status)
        else:
            self._screen.show_popup_message(_("No wireless interface has been found"), level=2)
            self.labels['networkinfo'] = Gtk.Label()
            self.labels['main_box'].pack_start(self.labels['networkinfo'], True, True, 0)
            self.update_single_network_info()

        self.content.add(self.labels['main_box'])

    def popup_callback(self, msg, level=3):
        self._screen.show_popup_message(msg, level)

    # ---- pager rendering ----

    @staticmethod
    def signal_icon_name(signal_level):
        if signal_level > 75:
            return 'wifi_excellent'
        elif signal_level > 60:
            return 'wifi_good'
        elif signal_level > 30:
            return 'wifi_fair'
        return 'wifi_weak'

    def load_networks(self):
        self.refresh_networks()
        GLib.timeout_add_seconds(10, self._gtk.Button_busy, self.reload_button, False)
        self.content.show_all()
        return False

    def refresh_networks(self):
        if not (self.sdbus_nm is not None and self.sdbus_nm.wifi):
            return False
        prev_bssid = self.items[self.index]['BSSID'] if self.items else None
        nets = self.sdbus_nm.get_networks()
        connected = self.sdbus_nm.get_connected_bssid()
        nets.sort(key=lambda n: (n['BSSID'] != connected, -n.get('signal_level', 0)))
        self.items = nets
        if prev_bssid is not None:
            for i, n in enumerate(self.items):
                if n['BSSID'] == prev_bssid:
                    self.index = i
                    break
        self.interface = self.sdbus_nm.get_primary_interface()
        self.labels['interface'].set_text(_("Interface") + f': {self.interface}')
        self.labels['ip'].set_text(f"IP: {self.sdbus_nm.get_ip_address()}")
        self.show_current()
        return True

    def show_current(self):
        for child in self.card_holder.get_children():
            self.card_holder.remove(child)
        if not self.items:
            self.card_holder.add(Gtk.Label(label=_("No networks"), hexpand=True, vexpand=True))
            self.card_holder.show_all()
            return
        self.index = max(0, min(self.index, len(self.items) - 1))
        net = self.items[self.index]
        connected = net['BSSID'] == self.sdbus_nm.get_connected_bssid()
        ssid = net['SSID']
        if connected:
            ssid += ' (' + _("Connected") + ')'

        name = Gtk.Label(hexpand=True, halign=Gtk.Align.CENTER, justify=Gtk.Justification.CENTER,
                         wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, lines=2,
                         ellipsize=Pango.EllipsizeMode.END)
        name.get_style_context().add_class("print-filename")
        name.set_markup(f"<big><b>{ssid}</b></big>")

        saved = "  ·  " + _("Saved") if net.get('known') else ""
        detail = Gtk.Label(halign=Gtk.Align.CENTER, justify=Gtk.Justification.CENTER)
        detail.get_style_context().add_class("print-info")
        detail.set_markup(
            f"<b>{net['signal_level']}%</b>  ·  {net['security']}  ·  "
            + _("Ch") + f" {net['channel']}{saved}"
        )

        imgsize = int(self._screen.height * 0.4)
        icon = Gtk.Button(hexpand=True, vexpand=True)
        icon.get_style_context().add_class("frame-item")
        icon.set_image(self._gtk.Image(self.signal_icon_name(net['signal_level']), imgsize, imgsize))
        icon.set_always_show_image(True)
        icon.connect("clicked", self.network_actions, net['BSSID'])

        self.card_holder.pack_start(icon, True, True, 0)
        self.card_holder.pack_start(name, False, False, 0)
        self.card_holder.pack_start(detail, False, False, 0)
        self.card_holder.show_all()

    def nav_up(self, widget=None):
        if self.items:
            self.index = (self.index - 1) % len(self.items)
            self.show_current()

    def nav_down(self, widget=None):
        if self.items:
            self.index = (self.index + 1) % len(self.items)
            self.show_current()

    def network_actions(self, widget, bssid):
        net = next((n for n in self.items if n['BSSID'] == bssid), None)
        if net is None:
            return
        ssid = net['SSID']
        connected = bssid == self.sdbus_nm.get_connected_bssid()
        buttons = []
        if connected:
            buttons.append({"name": _("Disconnect"), "response": Gtk.ResponseType.APPLY, "style": 'dialog-info'})
        else:
            buttons.append({"name": _("Connect"), "response": Gtk.ResponseType.OK, "style": 'dialog-primary'})
        if net['known']:
            buttons.append({"name": _("Forget"), "response": Gtk.ResponseType.REJECT, "style": 'dialog-warning'})
        buttons.append({"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL, "style": 'dialog-secondary'})

        label = Gtk.Label(hexpand=True, vexpand=True, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR,
                          justify=Gtk.Justification.CENTER)
        label.set_markup(
            f"<big><b>{net['SSID']}</b></big>\n"
            f"{net['security']}\n"
            f"{net['signal_level']}%  ·  " + _("Ch") + f" {net['channel']}\n"
            f"<small>{net['BSSID']}</small>"
        )
        self._gtk.Dialog(net['SSID'], buttons, label, self.network_response, ssid)

    def network_response(self, dialog, response_id, ssid):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.CANCEL:
            return
        if response_id == Gtk.ResponseType.OK:
            self.connect_network(None, ssid)
        elif response_id == Gtk.ResponseType.APPLY:
            logging.info(f"Disconnecting {ssid}")
            self.sdbus_nm.disconnect_network()
            self.reload_networks()
        elif response_id == Gtk.ResponseType.REJECT:
            logging.info(f"Deleting {ssid}")
            self.sdbus_nm.delete_network(ssid)
            self.reload_networks()

    # ---- backend (preserved from stock) ----

    def add_new_network(self, widget, ssid):
        self._screen.remove_keyboard()
        psk = self.labels['network_psk'].get_text()
        identity = self.labels['network_identity'].get_text()
        eap_method = self.get_dropdown_value(self.labels['network_eap_method'])
        phase2 = self.get_dropdown_value(self.labels['network_phase2'])
        logging.debug(f"{phase2=}")
        logging.debug(f"{eap_method=}")
        result = self.sdbus_nm.add_network(ssid, psk, eap_method, identity, phase2)
        if "error" in result:
            self._screen.show_popup_message(result["message"])
            if result["error"] == "psk_invalid":
                return
        else:
            self.connect_network(widget, ssid, showadd=False)
        self.close_add_network()

    def get_dropdown_value(self, dropdown, default=None):
        tree_iter = dropdown.get_active_iter()
        model = dropdown.get_model()
        result = model[tree_iter][0]
        return result if result != "disabled" else None

    def back(self):
        if self.show_add:
            self.close_add_network()
            return True
        return False

    def close_add_network(self):
        if not self.show_add:
            return

        for child in self.content.get_children():
            self.content.remove(child)
        self.content.add(self.labels['main_box'])
        self.content.show()
        for i in ['add_network', 'network_psk', 'network_identity']:
            if i in self.labels:
                del self.labels[i]
        self.show_add = False

    def connect_network(self, widget, ssid, showadd=True):
        self.deactivate()
        if showadd and not self.sdbus_nm.is_known(ssid):
            sec_type = self.sdbus_nm.get_security_type(ssid)
            if sec_type == "Open" or "OWE" in sec_type:
                logging.debug("Network is Open do not show psk")
                result = self.sdbus_nm.add_network(ssid, '')
                if "error" in result:
                    self._screen.show_popup_message(result["message"])
            else:
                self.show_add_network(widget, ssid)
            self.activate()
            return
        self.sdbus_nm.connect(ssid)
        self.reload_networks()

    def on_popup_shown(self, combo_box, params):
        if combo_box.get_property("popup-shown"):
            logging.debug("Dropdown popup show")
            self.last_drop_time = datetime.now()
        else:
            elapsed = (datetime.now() - self.last_drop_time).total_seconds()
            if elapsed < 0.2:
                logging.debug(f"Dropdown closed too fast ({elapsed}s)")
                GLib.timeout_add(50, combo_box.popup)
                return
            logging.debug("Dropdown popup close")

    def show_add_network(self, widget, ssid):
        if self.show_add:
            return

        for child in self.content.get_children():
            self.content.remove(child)

        if "add_network" in self.labels:
            del self.labels['add_network']

        eap_method = Gtk.ComboBoxText(hexpand=True)
        eap_method.connect("notify::popup-shown", self.on_popup_shown)
        for method in ("peap", "ttls", "pwd", "leap", "md5"):
            eap_method.append(method, method.upper())
        self.labels['network_eap_method'] = eap_method
        eap_method.set_active(0)

        phase2 = Gtk.ComboBoxText(hexpand=True)
        phase2.connect("notify::popup-shown", self.on_popup_shown)
        for method in ("mschapv2", "gtc", "pap", "chap", "mschap", "disabled"):
            phase2.append(method, method.upper())
        self.labels['network_phase2'] = phase2
        phase2.set_active(0)

        auth_selection_box = Gtk.Box(no_show_all=True)
        auth_selection_box.add(self.labels['network_eap_method'])
        auth_selection_box.add(self.labels['network_phase2'])

        self.labels['network_identity'] = Gtk.Entry(hexpand=True, no_show_all=True)
        self.labels['network_identity'].connect("focus-in-event", self._screen.show_keyboard)

        self.labels['network_psk'] = Gtk.Entry(hexpand=True)
        self.labels['network_psk'].connect("activate", self.add_new_network, ssid)
        self.labels['network_psk'].connect("focus-in-event", self._screen.show_keyboard)

        save = self._gtk.Button("sd", _("Save"), "color3")
        save.set_hexpand(False)
        save.connect("clicked", self.add_new_network, ssid)

        user_label = Gtk.Label(label=_("User"), hexpand=False, no_show_all=True)
        auth_grid = Gtk.Grid()
        auth_grid.attach(user_label, 0, 0, 1, 1)
        auth_grid.attach(self.labels['network_identity'], 1, 0, 1, 1)
        auth_grid.attach(Gtk.Label(label=_("Password"), hexpand=False), 0, 1, 1, 1)
        auth_grid.attach(self.labels['network_psk'], 1, 1, 1, 1)
        auth_grid.attach(save, 2, 0, 1, 2)

        if "802.1x" in self.sdbus_nm.get_security_type(ssid):
            user_label.show()
            self.labels['network_eap_method'].show()
            self.labels['network_phase2'].show()
            self.labels['network_identity'].show()
            auth_selection_box.show()

        self.labels['add_network'] = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=5, valign=Gtk.Align.CENTER,
            hexpand=True, vexpand=True
        )
        self.labels['add_network'].add(Gtk.Label(label=_("Connecting to %s") % ssid))
        self.labels['add_network'].add(auth_selection_box)
        self.labels['add_network'].add(auth_grid)
        scroll = self._gtk.ScrolledWindow()
        scroll.add(self.labels['add_network'])
        self.content.add(scroll)
        self.labels['network_psk'].grab_focus_without_selecting()
        self.content.show_all()
        self.show_add = True

    def update_single_network_info(self):
        self.labels['networkinfo'].set_markup(
            f'<b>{self.interface}</b>\n\n'
            + '<b>' + _("Hostname") + f':</b> {os.uname().nodename}\n'
            f'<b>IPv4:</b> {self.sdbus_nm.get_ip_address()}\n'
        )
        self.labels['networkinfo'].show_all()
        return True

    def reload_networks(self, widget=None):
        self.deactivate()
        if self.sdbus_nm is not None and self.sdbus_nm.wifi:
            if widget:
                self._gtk.Button_busy(widget, True)
            self.sdbus_nm.rescan()
            self.refresh_networks()
        self.activate()

    def activate(self):
        if self.sdbus_nm is None:
            return
        if self.update_timeout is None:
            if self.sdbus_nm.wifi:
                self.sdbus_nm.enable_monitoring(True)
                if self.reload_button.get_sensitive():
                    self._gtk.Button_busy(self.reload_button, True)
                    self.sdbus_nm.rescan()
                self.refresh_networks()
                self.update_timeout = GLib.timeout_add_seconds(5, self.refresh_networks)
            else:
                self.update_single_network_info()
                self.update_timeout = GLib.timeout_add_seconds(5, self.update_single_network_info)

    def deactivate(self):
        if self.sdbus_nm is None:
            return
        if self.update_timeout is not None:
            GLib.source_remove(self.update_timeout)
            self.update_timeout = None
        if self.sdbus_nm.wifi:
            self.sdbus_nm.enable_monitoring(False)

    def toggle_wifi(self, switch, gparams):
        enable = switch.get_active()
        logging.info(f"WiFi {enable}")
        self.sdbus_nm.toggle_wifi(enable)
        if enable:
            self.reload_button.show()
            self.reload_networks()
        else:
            self.reload_button.hide()
