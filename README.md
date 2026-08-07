# klipperscreen-ux-ir3v2

A **U1-idiom KlipperScreen** for the IdeaFormer IR3 V2 belt printer: the flat, dark,
single-accent touchscreen UX of the Snapmaker U1, reconstructed as **original panel reflows
+ a theme** on top of the JansenCXM KlipperScreen fork. Similar in spirit, not identical —
no vendor code or branding. The U1 on-screen UI is a closed module (only Klipper/Moonraker/
Fluidd were open-sourced), so this is a clone of the *idea*, reverse-designed from public
captures, not a fork.

## What ships

Every file below replaces one in the KlipperScreen tree. `deploy.sh` puts each in place and
keeps a `.stock` copy of the original.

| Screen | Repo file | Installs as | Reflow |
|---|---|---|---|
| **Chrome** | `panel_base.py` | `panels/base_panel.py` | no left rail — nav top-left, emergency/shortcuts top-right, content spans the full width |
| **Home** | `panel_main_menu.py` | `panels/main_menu.py` | home *is* the top of the menu tree; a thin `menu` subclass so tiles render identically everywhere |
| **Menus** | `panel_menu.py` | `panels/menu.py` | paged big flat tiles, drill-down with native back, no empty cells |
| **Print / Files** | `panel_gcodes.py` | `panels/gcodes.py` | one-per-page pager: full-width thumbnail, name beneath, buttons far right, newest-first, trimmed file dialog |
| **Job** | `panel_job_status.py` | `panels/job_status.py` | blue `#2f6fff` progress ring; icon-only control bar — more · tune · pause · stop |
| **Temperature** | `panel_temperature.py` | `panels/temperature.py` | heaters as big flat cards, graph kept |
| **Move** | `panel_move.py` | `panels/move.py` | flat controls, slimmer distance toggles |
| **Extrude** | `panel_extrude.py` | `panels/extrude.py` | flat controls, slim speed toggles so the sensor row fits |
| **Fine tuning** | `panel_fine_tune.py` | `panels/fine_tune.py` | belt-axis babystepping (see below) |
| **Network** | `panel_network.py` | `panels/network.py` | pager idiom |
| **Limits** | `panel_limits.py` | `panels/limits.py` | pager idiom |
| **Type scale** | `ks_includes/KlippyGtk.py` | `ks_includes/KlippyGtk.py` | `font_ratio` `[40,27]` → `[27,18]`: ~50% larger global font for touch |
| **Menu tree** | `config/main_menu.conf` | `config/main_menu.conf` | nested Print / Prepare / Settings / Infinity Flow tree |
| **Everything** | `styles/ux/` | `styles/ux/` | dark flat cards, one blue accent, iOS-style blue toggles |

## Belt-axis babystepping

On the IR3 V2 the operator's "Z offset" — nozzle-to-belt standoff — is the machine's **Y**
gcode offset. The printer's own `printer.cfg` babysteps through `Y_Offset_UP`/`Y_Offset_DOWN`
(`SET_GCODE_OFFSET Y_ADJUST`), and the belt fork's stock panel does the same. `panel_fine_tune.py`
keeps the buttons labelled `Z+`/`Z-` (the operator's mental model) but sends `Y_ADJUST`.
**Do not "correct" this to `Z_ADJUST`** — on this corexy belt machine that tilts the gantry
along the incline instead of changing the first-layer standoff.

## Install (device)

```bash
bash deploy.sh ~/KlipperScreen ~/printer_data/config/KlipperScreen.conf
```

Idempotent: the first run saves each stock file as `<name>.stock` and later runs never
overwrite those, so revert always lands on the true original. It sets `theme = ux` surgically
in the auto-generated `[main]` block and restarts KlipperScreen.

Theme only, without the panel reflows:

```bash
bash styles/ux/install.sh ~/KlipperScreen ~/printer_data/config/KlipperScreen.conf
```

## Preserved on the IR3 V2

Only layout changes. All device config and macros are kept: timezone, `font_size = large`,
language, `print_estimate_method`, the `[displayed_macros Printer]` set, the `[graph Printer]`
toggles, and the custom `[menu __main infinity_flow]` panel + `infinity_flow.py`.

## Test

```bash
xvfb-run -a python3 test_control_bar.py
```

Measures the job-status control bar with real GTK geometry at the panel's font metrics and
fails if any of the four print actions would fall outside the content box. As row 3 of the
job grid the bar needed 429px of the IR3 V2's 425px content height and its bottom was cut
off; packed in its own box it needs 391px, with the bar fully inside at y=370..425.

Panels under 480px tall still overflow — the 5-row info grid alone exceeds the content box
there, independent of the bar. Not addressed; the IR3 V2 is 800x480.

## Revert

```bash
cd ~/KlipperScreen && for f in $(find . -name '*.stock'); do cp "$f" "${f%.stock}"; done
```

Then set `theme = material-light` in `KlipperScreen.conf` (the prior value) and restart.
Full pre-change device snapshot: `backups/ir3v2_klipperscreen_20260803.tar.gz`.

## Legal

Vendor reference captures (Snapmaker wiki / YouTube frames) live only under `u1_reference/`
and are **gitignored** — never committed, never redistributed; only `REFERENCE.md` and the
mock-up scripts are tracked. All theme and panel code here is original work.
