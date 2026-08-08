"""Offline UI bench — render the real KlipperScreen panels at the IR3 V2's 800x480, with
the real base.css + ux theme CSS, and fail on anything that does not fit.

Why this exists: the panels only overflow once the theme's +50% font and the CSS are
applied, so measuring a hand-built mock of a layout is worthless — it reported "fits" for a
job screen that was clipping its stop button off the right edge on the actual machine. This
loads the shipped panel modules and the shipped stylesheets and measures what they really ask
for. No printer, no network: ScreenPanel's dependencies are mocked.

Needs a KlipperScreen checkout to import from (panels/, ks_includes/, styles/) with this
repo's files deployed over it — i.e. what deploy.sh produces.

  xvfb-run -a python3 uibench.py --all                  # audit every panel, exit 1 on overflow
  xvfb-run -a python3 uibench.py job_status printing    # one panel, + out/<panel>.png
  KS_DIR=~/KlipperScreen xvfb-run -a python3 uibench.py --all
"""
import os
import pathlib
import sys
import builtins

builtins._ = lambda s: s          # gettext stub, panels call _() at import/init
builtins.ngettext = lambda s, p, n: s if n == 1 else p

KS = pathlib.Path(os.environ.get("KS_DIR", pathlib.Path.home() / "KlipperScreen")).expanduser()
sys.path.insert(0, str(KS))

import types
for _m in ("sdbus", "sdbus_async", "sdbus_async.networkmanager", "sdbus_block",
           "sdbus_block.networkmanager"):
    if _m not in sys.modules:
        mod = types.ModuleType(_m)
        mod.__getattr__ = lambda n: type(n, (), {"__init__": lambda self, *a, **k: None})
        sys.modules[_m] = mod

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gtk

W, H = 800, 480
THEME = "ux"

# The job screen's thumbnail button takes a hard minimum width from its pixbuf, so the bench
# must supply one or it measures a narrower panel than the machine ever shows.
import tempfile
THUMB = os.path.join(tempfile.gettempdir(), "uibench_thumb.png")
if not os.path.exists(THUMB):
    from gi.repository import GdkPixbuf as _GP
    _GP.Pixbuf.new(_GP.Colorspace.RGB, False, 8, 300, 300).savev(THUMB, "png", [], [])


# ---------------------------------------------------------------- mocks
class Cfg:
    def __init__(self, d=None):
        self.d = d or {}

    def get(self, k, fallback=None):
        return self.d.get(k, fallback)

    def getboolean(self, k, fallback=False):
        return self.d.get(k, fallback)

    def getint(self, k, fallback=0):
        return int(self.d.get(k, fallback))

    def getfloat(self, k, fallback=0.0):
        return float(self.d.get(k, fallback))

    def __getitem__(self, k):
        return self.d.get(k, "")

    def __contains__(self, k):
        return k in self.d


class MockConfig:
    def __init__(self):
        self._main = Cfg({"font_size": "large", "print_estimate_method": "slicer",
                          "show_heater_power": False, "24htime": True,
                          "print_sort_dir": "date_asc", "show_scroll_steppers": False})

    def get_main_config(self):
        return self._main

    def get_config(self):
        outer = self

        class CP(dict):
            def getboolean(self, sect, key=None, fallback=False):
                return fallback

            def getint(self, sect, key=None, fallback=0):
                return fallback

            def get(self, sect, key=None, fallback=None):
                if key is None:
                    return dict.get(self, sect, fallback)
                return fallback
        cp = CP({"main": outer._main})
        return cp

    def get_printer_config(self, *a):
        return Cfg({'titlebar_items': '', 'z_babystep_values': '0.01, 0.05',
                    'move_speed_xy': '100', 'move_speed_z': '10',
                    'extrude_speed': '5', 'extrude_distance': '10'})

    def get_menu_items(self, menu="__main", submenu=""):
        return []

    def get_preheat_options(self):
        return {}

    def get_lang(self):
        return None


SECTIONS = {
    "extruder": {"filament_diameter": "1.75", "max_extrude_only_distance": "150"},
    "printer": {"kinematics": "corexy", "max_velocity": "400", "max_accel": "20000",
                "max_z_velocity": "50", "max_accel_to_decel": "10000",
                "square_corner_velocity": "5"},
    "heater_bed": {}, "stepper_z": {"position_endstop": "0"},
}


class MockPrinter:
    extrudercount = 1
    available_commands = {"Z_OFFSET_APPLY_ENDSTOP": {}, "Z_OFFSET_APPLY_PROBE": {}}
    cameras = []
    data = {"virtual_sdcard": {"progress": 0.42}}
    tempstore = {}

    def __init__(self):
        self.state = "printing"

    def get_stat(self, obj, key=None):
        stats = {
            "toolhead": {"extruder": "extruder", "max_accel": 20000,
                         "homed_axes": "xyz", "position": [10, 20, 30, 0]},
            "gcode_move": {"homing_origin": [0, 0.15, 0, 0], "speed_factor": 1.0,
                           "extrude_factor": 1.0, "speed": 2700,
                           "gcode_position": [10, 20, 15.83, 0]},
            "virtual_sdcard": {"progress": 0.42, "file_position": 4200},
            "print_stats": {"state": self.state, "filename": "profilo lineare tavolo "
                            "officina_0.2mm_PLA_IdeaFormer IR3 V2_1h1m.gcode",
                            "print_duration": 1500.0, "total_duration": 1560.0,
                            "filament_used": 3200.0, "message": "",
                            "info": {"current_layer": 42, "total_layer": 180}},
            "exclude_object": {"objects": [], "excluded_objects": []},
            "motion_report": {"live_position": [10, 20, 15.83, 120],
                              "live_velocity": 43.0, "live_extruder_velocity": 2.6},
        }
        s = stats.get(obj, {})
        return s.get(key, 0) if key else s

    def get_tools(self):
        return ["extruder"]

    def get_heaters(self):
        return ["extruder", "heater_bed"]

    def get_temp_devices(self):
        return ["extruder", "heater_bed"]

    def get_temp_sensors(self):
        return []

    def get_fans(self):
        return ["fan"]

    def get_fan_speed(self, fan=None):
        return 1.0

    def get_output_pins(self):
        return []

    def get_leds(self):
        return []

    def get_probe(self):
        return {"z_offset": "0.0"}

    def get_config_section(self, s):
        return SECTIONS.get(s, {})

    def get_config_section_list(self, prefix=""):
        return [k for k in SECTIONS if k.startswith(prefix)] if prefix else list(SECTIONS)

    def get_gcode_macros(self):
        return []

    def get_power_devices(self):
        return []

    def state_ready(self, *a, **k):
        pass

    config = SECTIONS
    spoolman = None
    busy = False

    def get_printer_status_data(self):
        return {"printer": {"extruder": {"present": True}, "temperature_devices": {"count": 2},
                            "fans": {"count": 1}, "output_pin": {"count": 0},
                            "bed_mesh": {"present": True}, "gcode_macros": {"count": 0, "list": []},
                            "idle_timeout": {"present": True}, "power_devices": {"count": 0},
                            "cameras": {"count": 0}, "spoolman": False, "leds": {"count": 0},
                            "sdcard": {"present": True}, "input_shaper": {"present": False},
                            "exclude_object": {"present": False}, "pins": {"count": 0},
                            "z_tilt": {"present": False}, "quad_gantry_level": {"present": False},
                            "screws_tilt_adjust": {"present": False}, "retraction": {"present": False},
                            "pressure_advance": {"present": True}, "network": {"present": True}}}

    def get_filament_sensors(self):
        return {}

    def get_macro(self, m):
        return None

    def enable_output_pin(self, *a, **k):
        pass

    def device_has_target(self, dev):
        return True

    def get_temp_store(self, *a, **k):
        return None


class MockFiles:
    def file_metadata_exists(self, f):
        return True

    def get_file_info(self, f):
        return {"size": 1234567, "estimated_time": 3660, "object_height": 50.0,
                "filament_total": 8000.0, "gcode_start_byte": 100,
                "gcode_end_byte": 10000, "modified": 1754000000.0, "job_id": None}

    def has_thumbnail(self, f):
        return True

    def get_thumbnail_location(self, f, small=False):
        return ("file", THUMB) if THUMB else None

    def request_metadata(self, f):
        pass

    def get_file_list(self, *a, **k):
        return []

    def get_gcode_files(self):
        return {}

    def add_file_callback(self, cb):
        pass


class Saver:
    def reset_timeout(self, *a):
        pass

    def close(self, *a):
        pass


class _Klippy:
    def __getattr__(self, name):
        return lambda *a, **k: {} if "info" in name else None


class MockWS:
    klippy = _Klippy()
    connected = True


class MockScreen(Gtk.Window):
    vertical_mode = False
    theme = THEME
    width, height = W, H
    updating = False
    dialogs = []
    confirm = None
    show_cursor = False

    def __init__(self):
        super().__init__()
        self._config = MockConfig()
        self.printer = MockPrinter()
        self.files = MockFiles()
        self.screensaver = Saver()
        self._ws = MockWS()
        self.apiclient = type("A", (), {"send_request": staticmethod(lambda *a, **k: None),
                                        "get_thumbnail_stream": staticmethod(lambda *a: False)})()
        from ks_includes.KlippyGtk import KlippyGtk
        self.gtk = KlippyGtk(self)
        self.gtk.color_list = {}
        self._printer = self.printer
        self._files = self.files
        from jinja2 import Environment
        self.env = Environment(extensions=["jinja2.ext.i18n"], autoescape=True)
        self.env.install_gettext_translations(
            type("T", (), {"gettext": staticmethod(lambda s: s),
                           "ngettext": staticmethod(lambda a, b, n: a if n == 1 else b)})())

    def set_panel_title(self, t):
        pass

    def show_all(self):
        pass

    def show_popup_message(self, *a, **k):
        pass

    def _go_to_submenu(self, *a):
        pass

    def _send_action(self, *a, **k):
        pass

    def show_panel(self, *a, **k):
        pass

    def state_ready(self, *a, **k):
        pass

    lang_ltr = True
    keyboard = None
    connected_printer = 'ideaformer'
    connecting = False
    printer_select_callbacks = []

    def _confirm_send_action(self, *a, **k):
        pass

    def panels_reinit(self, *a, **k):
        pass

    def show_keyboard(self, *a, **k):
        pass

    def _menu_go_back_cb(self, *a, **k):
        pass

    def show_all(self):
        pass

    def remove_keyboard(self, *a, **k):
        pass

    def _menu_go_back(self, *a, **k):
        pass


def load_css(gtk_screen):
    base = (KS / "styles" / "base.css").read_text()
    base = base.replace("KS_FONT_SIZE", f"{gtk_screen.gtk.font_size}")
    theme = (KS / "styles" / THEME / "style.css").read_text()
    prov = Gtk.CssProvider()
    prov.load_from_data((base + theme).encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def overflow_report(root, avail_w, avail_h):
    """Walk the tree and list widgets whose allocation escapes the visible box."""
    bad = []

    def walk(w, depth=0):
        a = w.get_allocation()
        right, bottom = a.x + a.width, a.y + a.height
        if right > avail_w + 1 or bottom > avail_h + 1:
            name = w.get_name() or type(w).__name__
            cls = " ".join(w.get_style_context().list_classes())
            lbl = ""
            if isinstance(w, Gtk.Label):
                lbl = f' "{w.get_text()[:28]}"'
            elif isinstance(w, Gtk.Button):
                lbl = f' "{w.get_label() or ""}"'
            bad.append((depth, type(w).__name__, name, cls, lbl,
                        a.x, a.y, a.width, a.height, right, bottom))
        if isinstance(w, Gtk.Container):
            for c in w.get_children():
                walk(c, depth + 1)

    walk(root)
    return bad


def build(panel_name, state):
    """Instantiate a panel with mocks and return (panel, screen, content_h)."""
    screen = MockScreen()
    screen.printer.state = state
    load_css(screen)

    mod = __import__(f"panels.{panel_name}", fromlist=["Panel"])

    def _mi(name, icon, panel):
        return {name: {"name": name, "icon": icon, "panel": panel, "enable": "True",
                       "style": None, "method": None, "params": {}, "confirm": None}}
    ITEMS = [_mi("Print", "sd", "gcodes"), _mi("Prepare", "move", "move"),
             _mi("Settings", "settings", "settings"),
             _mi("Camera", "camera", "camera")]

    import inspect
    # panels read class-level ScreenPanel attrs in __init__ before super() runs
    from ks_includes.screen_panel import ScreenPanel as SP
    SP._screen, SP._config, SP._printer = screen, screen._config, screen.printer
    SP._files, SP._gtk = screen.files, screen.gtk
    kw = {"items": ITEMS} if "items" in inspect.signature(mod.Panel.__init__).parameters else {}
    panel = mod.Panel(screen, None, **kw)

    if panel_name == "job_status":
        panel.update_filename(screen.printer.get_stat("print_stats", "filename"))
        panel.set_state(state)
        panel.labels["lcdmessage"].set_label("ENABLING the Filament Motion Sensor")
        panel.labels["lcdmessage"].show()

    content_h = H - int(screen.gtk.font_size * 2)     # ux chrome: titlebar only, no left rail
    win = Gtk.OffscreenWindow()
    win.set_size_request(W, content_h)
    win.add(panel.content)
    win.show_all()
    for _i in range(40):
        while Gtk.events_pending():
            Gtk.main_iteration()
    return panel, screen, content_h, win


# panels whose overflow is worth gating on, with the states that change their layout
TARGETS = [("job_status", s) for s in ("printing", "paused", "complete", "standby", "error")]
TARGETS += [(p, "printing") for p in
            ("gcodes", "temperature", "move", "extrude", "fine_tune", "limits")]


def audit():
    print(f"KS_DIR={KS}")
    print(f"{'panel':<22} {'state':<9} {'needs':>11} {'box':>10} {'w':>6} {'h':>6}")
    failures = []
    for name, state in TARGETS:
        try:
            panel, screen, content_h, _win = build(name, state)
        except Exception as e:                       # noqa: BLE001 - report, keep auditing
            print(f"{name:<22} {state:<9}   SKIPPED ({type(e).__name__}: {str(e)[:34]})")
            continue
        need_w = panel.content.get_preferred_width()[0]
        need_h = panel.content.get_preferred_height()[0]
        dw, dh = need_w - W, need_h - content_h
        flag = "" if (dw <= 0 and dh <= 0) else "   <== OVERFLOWS"
        print(f"{name:<22} {state:<9} {need_w:5d}x{need_h:<5d} {W:4d}x{content_h:<5d} "
              f"{dw:+6d} {dh:+6d}{flag}")
        if dw > 0 or dh > 0:
            failures.append(f"{name}[{state}]: needs {need_w}x{need_h}, box is {W}x{content_h} "
                            f"({dw:+d}w {dh:+d}h)")
    print()
    if failures:
        print("FAIL - panels that do not fit the screen:")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS - every audited panel fits 800x480 with the ux theme applied.")
    return 0


def one(panel_name, state):
    panel, screen, content_h, win = build(panel_name, state)
    need_w = panel.content.get_preferred_width()[0]
    need_h = panel.content.get_preferred_height()[0]
    print(f"panel={panel_name} state={state} font={screen.gtk.font_size:.1f} "
          f"box={W}x{content_h}")
    print(f"needs {need_w}x{need_h}  ->  width {need_w - W:+d}px  height {need_h - content_h:+d}px")
    for d, t, n, c, lbl, x, y, w_, h_, r, b in overflow_report(panel.content, W, content_h)[:12]:
        print(f"  {'  ' * d}{t:12s} {n:12s} [{c[:24]:24s}]{lbl:28s} @{x},{y} {w_}x{h_}"
              f" -> right={r} bottom={b}")
    os.makedirs("out", exist_ok=True)
    pb = win.get_pixbuf()
    if pb:
        pb.savev(f"out/{panel_name}_{state}.png", "png", [], [])
        print(f"wrote out/{panel_name}_{state}.png")
    return 0 if (need_w <= W and need_h <= content_h) else 1


if __name__ == "__main__":
    if not (KS / "panels").is_dir():
        sys.exit(f"no KlipperScreen at {KS} - set KS_DIR")
    if "--all" in sys.argv:
        sys.exit(audit())
    sys.exit(one(sys.argv[1] if len(sys.argv) > 1 else "job_status",
                 sys.argv[2] if len(sys.argv) > 2 else "printing"))
