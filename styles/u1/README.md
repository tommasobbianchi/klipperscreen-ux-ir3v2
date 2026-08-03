# u1 — KlipperScreen theme (IdeaFormer IR3 V2)

A dark, flat, single-accent KlipperScreen theme in the visual idiom of modern tool-changer
touchscreens: near-black canvas, rounded filled cards, one blue accent (`#2f6fff`) for the
primary/active state, iOS-style blue toggles, big touch targets. **Original work** — a GTK-CSS
theme layered on KlipperScreen's `base.css`, not derived from any vendor firmware. "Similar in
spirit, not identical."

## Files
- `style.css` — palette (`@define-color`) + selector overrides (mirrors `material-dark`'s coverage
  so every screen restyles).
- `style.conf` — graph colours.
- `install.sh` — seeds `images/` from the stock `material-dark` theme, overlays these files, and
  flips `theme = u1` **surgically** in `KlipperScreen.conf` (touches nothing else).

## Install (device)
```bash
bash install.sh ~/KlipperScreen ~/printer_data/config/KlipperScreen.conf
sudo systemctl restart KlipperScreen
```

## Preserved on the IR3 V2
Deploy changes only the `theme =` line. All device config is kept: timezone, `font_size = large`,
language, `print_estimate_method`, the `[displayed_macros Printer]` set, the `[graph Printer]`
sensor toggles, and the custom `[menu __main infinity_flow]` panel — all IR3 V2 macros and settings
intact.

## Revert
`theme = material-light` in `KlipperScreen.conf` (the prior value) + restart. Full pre-change
snapshot of `~/KlipperScreen` and `~/printer_data/config` is in `../../backups/`.
