# klipperscreen-ux-ir3v2

A **U1-idiom KlipperScreen** for the IdeaFormer IR3 V2 belt printer: the flat, dark,
single-accent touchscreen UX of the Snapmaker U1, reconstructed as **original panel reflows
+ a theme** on top of the JansenCXM KlipperScreen fork. Similar in spirit, not identical —
no vendor code or branding. The U1 on-screen UI is a closed module (only Klipper/Moonraker/
Fluidd were open-sourced), so this is a clone of the *idea*, reverse-designed from public
captures, not a fork.

## What it changes (all verified live on the IR3 V2)

| Screen | File | U1 reflow |
|--------|------|-----------|
| **Home** | `panel_main_menu.py` → `panels/main_menu.py` | left icon column (settings→full menu / files / filament), single honest tool chip (single-extruder), message + blue **Start** card. Full `__main` menu stays reachable behind the gear as a native panel (native back). |
| **Job** | `panel_job_status.py` → `panels/job_status.py` | progress ring recolored to the single blue accent (`#2f6fff`) over the existing U1-shaped layout (central %, model thumbnail, temp readouts, control bar). |
| **Print / Files** | *(stock `gcodes.py` + theme)* | already a U1 print-select grid: model thumbnails + name + time. No code change needed. |
| **Everything** | `styles/ux/` | dark flat cards, one blue accent, iOS-style blue toggles. |

## Install (device)
```bash
# theme
bash styles/ux/install.sh ~/KlipperScreen ~/printer_data/config/KlipperScreen.conf
# panel reflows (back up stock first)
cp ~/KlipperScreen/panels/main_menu.py{,.stock}
cp ~/KlipperScreen/panels/job_status.py{,.stock}
cp panel_main_menu.py  ~/KlipperScreen/panels/main_menu.py
cp panel_job_status.py ~/KlipperScreen/panels/job_status.py
sudo systemctl restart KlipperScreen
```

## Preserved on the IR3 V2
Only the panel *layout* changes. All IR3 V2 config and macros are kept: `theme = ux`,
`font_size = large`, timezone, language, the `[displayed_macros Printer]` set, the
`[graph Printer]` toggles, and the custom `[menu __main infinity_flow]` panel + `infinity_flow.py`.

## Revert
Restore `panels/main_menu.py.stock` / `panels/job_status.py.stock`, set `theme = material-light`
in `KlipperScreen.conf`, restart. Full pre-change device snapshot in `backups/`.

## Legal
Private repo. Vendor reference captures (Snapmaker wiki / YouTube frames) live only under
`u1_reference/` and are **gitignored** — never redistributed. Only original theme/panel code
is committed.
