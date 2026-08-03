# Snapmaker U1 touchscreen — visual reference set

Genuine U1 screen captures at native **480×320** (the U1 screen resolution), pulled from
Snapmaker's own wiki. Source of truth for reconstructing the U1 UX on KlipperScreen.
The screen UI itself is **not** open source (only Klipper/Moonraker/Fluidd were released;
the local HMI is a closed "independently developed module"), so these images are what we
reverse-design from — there is no code to fork.

## Files

| file | screen | source page |
|------|--------|-------------|
| 01.png | **Home** (idle) — status bar, left icon column, tool row, Start card | hot_end_guide |
| 02.png | **Settings** list | hot_end_guide |
| 03.png | **Maintenance** list | hot_end_guide |
| 04.png | **Toolhead Info** (per-tool nozzle Ø) | hot_end_guide |
| 05.png | Settings/nozzle detail | hot_end_guide |
| 06.png | **Modal dialog** (nozzle-mismatch warning, Cancel / Edit Now) | hot_end_guide |
| 07–08.png | Filament/nozzle config steps | hot_end_guide |
| 09.png | **Home** with Start highlighted | hot_end_guide |
| 10.png | **Filament Setup** — gcode thumbnail, weight/material rows, tool-assign, Next | hot_end_guide |
| 11.png | filament config step | hot_end_guide |
| 12.png | **wide strip**: Home → Settings → Device Calibration (toggles + Start) | Core_Components_Maintenance_Guide (offset_calibration.png) |
| mirror_display.jpg | real U1 screen photographed in the wild (ESP32 mirror project) | github suchmememanyskill |

Image host pattern: `https://wiki.snapmaker.com/<filename>` (filenames are Chinese, e.g.
`热端固件配置-1en.png` = "hot-end firmware config"). offset_calibration.png lives at root too.

## Extracted design language (for the KlipperScreen theme)

- **Canvas**: near-black `#0d0e10`; cards `#1e2024`, raised rows `#2a2d31`; corner radius ~14px.
- **Text**: white primary, `#8a9099` secondary; right-aligned values in list rows.
- **Accent**: single blue primary `~#2f6fff` used ONLY for the one primary action (Start/Next), always a **pill**.
- **Status bar** (home): nozzle-temp + tool dropdown ‹chevron›, bed-heat icon+°C, chamber icon+°C, camera, cloud, wifi — small mono icons, evenly spaced.
- **Home layout**: left column = 3 stacked rounded-square icon buttons (settings / print / unload); right = tool-filament row (PLA 1·2·3·4 as colored numbered circles) over a message/Start card.
- **Lists**: full-width cards, one action per row, right chevron `›`, value text before the chevron. iOS-style **toggle** switches for on/off (blue = on).
- **Modals**: centered rounded card, dimmed backdrop, two flat text buttons split by a divider.
- **Wizards**: title + `?` help glyph top-center, `‹` back left, primary (`Next`/`Start`) as blue pill top-right.
- NOTE: yellow highlight rectangles/arrows in these images are **wiki annotations**, not UI.

The whole thing is a **reskin + menu reflow** — no new printer capability. Big flat targets,
one accent, flatter/shallower menu tree than stock KlipperScreen.

## Print/job + wizard screens (from YouTube — wiki set is idle-only)

Frames grabbed from the "SnapMaker U1 Setup and First print review"
(youtube `wnwvCy8JNgo`, 360p) — the wiki has no printing/calibration screens.
Files in `job_and_wizard/`. `ZOOM_*` are cropped+upscaled (readable); the rest are
clean 640×360 full frames at the labelled timestamp (`_t###` = seconds).

**Print / job screen** (`ZOOM_job_screen.jpg`, `job_0pct_*`):
- top-left: **model thumbnail**; center: big **% progress**; right: job/status title
  (`Calibration Bay` / model name) + a sub-status line.
- mid row: **three temp readouts** with mono icons — nozzle→target, bed, chamber.
- bottom: **control bar of 4 flat buttons** — 💡 light · ▦ tune/adjust · **‖ pause** (red) · **▮ stop** (red).
- Same dark canvas + single-accent language as the idle screens. No KlipperScreen-style
  dense grid — it's a status card + one action row.

**Guided calibration wizard** (`ZOOM_cal_homing.jpg`, `cal_homing_t147`, `cal_wiping_t207`):
- title top (`Device Calibration (1/3)` — **step counter**), centered **spinner ring**,
  single status word below (`Homing…`, `Wiping Nozzle…`). One thing on screen at a time.

**Setup wizard** (`account_qr`, `language`, `terms_qr`, `wifi`, `error_dialog`, `toolhead_guide`):
- linear pages, `‹` back + `Next` pill, `?` help; QR-code onboarding (Snapmaker app);
  language list with radio; Terms with QR + Agree checkbox; WiFi signal bars;
  **error dialog** = centered card, orange warning glyph, error code, single `OK`;
  `toolhead_guide` embeds a **how-to video inside the screen** (procedural help).

Implication for the KlipperScreen port: `job_status.py` needs the status-card + 4-button
reflow; calibration/homing should be **wizard panels** (step counter + spinner + one label),
not KlipperScreen's live multi-widget screens. Errors → single-action modal.

## Filament flow (from the multi-color review, yt MyiGT9QkeBU)

Files in `filament_and_job/`. Same dark language, `ZOOM_*` = upscaled crops.
- `filament_menu` (t607): **Filament** — tool row `1·2·3·4 PLA` (numbered colored circles) over
  two wide buttons `Loading Mode` / `Unloading Mode`.
- `filament_details` (t612): `Type` / `Color` rows, right-aligned values, `‹` back + `Save` pill.
- `filament_type_grid` / `ZOOM_filament_type` (t620): **Type picker** — grid of filament presets
  (Snapmaker · Polymaker · Meta PLA · Basic PLA · Support PLA · Generic · PETG HF…), selected tile
  highlighted blue.
- `filament_color_grid` / `ZOOM_filament_color` (t630): **Color picker** — swatch grid.
- `job_confirmed` (t896): the job screen again (`0%` · `spelinca_v22_PLA` · green model · temps ·
  💡/tune/‖/▮ bar) — confirms the print-screen layout.

## NOT FOUND: the on-device file browser (`Files › Local` print-select)

Searched exhaustively (5 review videos frame-by-frame + wiki + Snapmaker support (Cloudflare-gated)
+ manuals.plus + 3dwithus + u1-fluidd + paxx extended-fw + ESP32 mirror repos). The dedicated
**file-browser / job-select** screen appears in **none** of them. Structural reason: the U1's
primary path is slice-in-Orca → send over the network → the on-screen **Filament-Setup confirm**
(`10.png`) → Start; the on-device USB `Files › Local` browser is a secondary path reviewers skip,
and it is not on the wiki/support pages either.

Ways to obtain it if needed later: (a) the extended-firmware **remote_screen** web mirror at
`http://<printer-ip>/screen/` on a real U1 renders every screen incl. the file list; (b) we have
no U1 on hand. For the IR3 V2 port this is a non-blocker — KlipperScreen already ships a file
browser (`panels/gcodes.py`); it just needs the U1 restyle (thumbnail grid + name + time + Start),
which the `10.png` Filament-Setup screen already models.
