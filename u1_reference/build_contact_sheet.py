#!/usr/bin/env python3
"""Compile the U1 touchscreen UX reference images into one self-contained HTML
contact sheet (images embedded as data URIs). Run: python3 build_contact_sheet.py"""
import base64, io, os
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "contact_sheet.html")

def data_uri(rel, maxw, q=80):
    im = Image.open(os.path.join(ROOT, rel)).convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.size

# (file, maxwidth, name, tag, note, kind)  kind: '', 'warn', 'live', 'wide'
SECTIONS = [
 ("Idle & menu", "Snapmaker's own wiki captures — the resting UX and menu tree.", [
    ("01.png", 520, "Home — idle", "wiki · 480×320", "status bar · left icon column · tool row · blue Start card", ""),
    ("09.png", 520, "Home — Start focus", "wiki · 480×320", "one primary action, always a blue pill", ""),
    ("02.png", 520, "Settings", "wiki · 480×320", "flat list root · right chevrons · values right-aligned", ""),
    ("03.png", 520, "Maintenance", "wiki · 480×320", "second level · one action per row", ""),
    ("04.png", 520, "Toolhead Info", "wiki · 480×320", "per-tool values, right-aligned before the chevron", ""),
    ("10.png", 520, "Filament Setup", "wiki · 480×320", "thumbnail · weight/material rows · tool-assign circles · Next", ""),
    ("06.png", 520, "Nozzle-mismatch modal", "wiki · 480×320", "centered card · dimmed backdrop · Cancel / Edit Now", "warn"),
    ("05.png", 520, "Nozzle detail", "wiki · 480×320", "config sub-page", ""),
 ]),
 ("Print & job", "The live-print screen — absent from the wiki, recovered from YouTube.", [
    ("job_and_wizard/ZOOM_job_screen.jpg", 900, "Print / job — live", "yt wnwvCy8JNgo · t249 · zoom", "thumbnail · big % · 3-temp row · bottom bar: light · tune · pause · stop", "live"),
    ("job_and_wizard/ZOOM_job_screen2.jpg", 900, "Print / job — live", "yt wnwvCy8JNgo · t255 · zoom", "status card + one action row — not a dense widget grid", "live"),
    ("job_and_wizard/job_0pct_b_t249.jpg", 620, "Job screen — in situ", "yt wnwvCy8JNgo · t249", "3 frames captured; screen sits lower-right of the panel", "live"),
 ]),
 ("Filament flow", "Per-tool filament: load/unload, and the type + colour pickers.", [
    ("filament_and_job/filament_menu_t607.jpg", 620, "Filament", "yt MyiGT9QkeBU · t607", "tool row 1·2·3·4 · Loading Mode / Unloading Mode", "live"),
    ("filament_and_job/filament_details_t612.jpg", 620, "Filament Details", "yt MyiGT9QkeBU · t612", "Type / Colour rows · back · Save pill", "live"),
    ("filament_and_job/ZOOM_filament_type.jpg", 620, "Type picker", "yt MyiGT9QkeBU · t620 · zoom", "preset grid — Snapmaker · Polymaker · PLA variants · PETG · selected tile blue", "live"),
    ("filament_and_job/ZOOM_filament_color.jpg", 620, "Colour picker", "yt MyiGT9QkeBU · t630 · zoom", "swatch grid", "live"),
 ]),
 ("Guided wizards", "Calibration as a step-counted wizard: one thing on screen at a time.", [
    ("job_and_wizard/ZOOM_cal_homing.jpg", 900, "Calibration — Homing", "yt wnwvCy8JNgo · t147 · zoom", "title with step counter (1/3) · centered spinner · one status word", "live"),
    ("job_and_wizard/cal_homing_t147.jpg", 620, "Device Calibration (1/3)", "yt wnwvCy8JNgo · t147", "Homing… — minimal, centered", "live"),
    ("job_and_wizard/cal_wiping_t207.jpg", 620, "Calibration — Wiping Nozzle", "yt wnwvCy8JNgo · t207", "same wizard shell, next step", "live"),
 ]),
 ("Setup flow", "First-run onboarding — linear pages, back / Next / help, single-action errors.", [
    ("job_and_wizard/account_qr_t93.jpg", 620, "Account — QR onboarding", "yt wnwvCy8JNgo · t93", "scan with the Snapmaker app · Set Up Later", ""),
    ("job_and_wizard/language_t132.jpg", 620, "Language select", "yt wnwvCy8JNgo · t132", "radio list · Next pill", ""),
    ("job_and_wizard/terms_qr_t135.jpg", 620, "Terms", "yt wnwvCy8JNgo · t135", "QR + Agree checkbox gate", ""),
    ("job_and_wizard/wifi_t138.jpg", 620, "Wi-Fi", "yt wnwvCy8JNgo · t138", "signal-bar list", ""),
    ("job_and_wizard/error_dialog_t117.jpg", 620, "Error — System Failed to Start", "yt wnwvCy8JNgo · t117", "centered card · orange glyph · error code · single OK", "warn"),
    ("job_and_wizard/toolhead_guide_t96.jpg", 620, "Toolhead guide", "yt wnwvCy8JNgo · t96", "procedural help — a how-to video plays inside the screen", ""),
 ]),
 ("In the wild", "The real panel, photographed — sanity check on colour and scale.", [
    ("mirror_display.jpg", 900, "Real U1 screen", "github · ESP32 mirror", "closed raster UI streamed as PNG over HTTP — nothing to fork", ""),
 ]),
]

WIDE = ("12.png", 1200, "Home → Settings → Device Calibration",
        "wiki · offset_calibration strip",
        "iOS-style toggles (blue = on) + Start pill top-right — the calibration entry path")

def card(rel, maxw, name, tag, note, kind):
    uri, (w, h) = data_uri(rel, maxw)
    badge = {"warn":'<span class="k k-warn">modal</span>',
             "live":'<span class="k k-live">captured</span>'}.get(kind, "")
    return f'''<figure class="card">
  <div class="shot" style="aspect-ratio:{w}/{h}"><img loading="lazy" src="{uri}" alt="{name}"></div>
  <figcaption>
    <div class="cap-top"><h3>{name}</h3>{badge}</div>
    <p class="tag">{tag}</p>
    <p class="note">{note}</p>
  </figcaption>
</figure>'''

def wide_card():
    rel, maxw, name, tag, note = WIDE
    uri, (w, h) = data_uri(rel, maxw)
    return f'''<figure class="card card-wide">
  <div class="shot" style="aspect-ratio:{w}/{h}"><img loading="lazy" src="{uri}" alt="{name}"></div>
  <figcaption>
    <div class="cap-top"><h3>{name}</h3><span class="k">wide</span></div>
    <p class="tag">{tag}</p><p class="note">{note}</p>
  </figcaption>
</figure>'''

n_screens = sum(len(items) for _, _, items in SECTIONS) + 1
body = []
for i, (title, blurb, items) in enumerate(SECTIONS):
    cards = "\n".join(card(*it) for it in items)
    extra = ""
    if title == "Idle & menu":
        extra = "\n" + wide_card()
    body.append(f'''<section class="grp">
  <header class="grp-h">
    <p class="eyebrow">{title}</p>
    <p class="grp-blurb">{blurb}</p>
    <span class="count">{len(items)+(1 if extra else 0)}</span>
  </header>
  <div class="grid">
{cards}{extra}
  </div>
</section>''')

SWATCHES = [("#0c0d0f","canvas"),("#17191c","card"),("#202327","raised"),
            ("#e9ebee","ink"),("#8b9199","muted"),("#2f6fff","accent")]
sw = "".join(f'<div class="sw"><span style="background:{h}"></span><code>{h}</code><em>{n}</em></div>'
             for h, n in SWATCHES)

HTML = f'''<title>Snapmaker U1 — touchscreen UX reference</title>
<style>
:root{{
  --bg:#0c0d0f; --card:#17191c; --raised:#202327; --line:#2b2f34;
  --ink:#e9ebee; --muted:#8b9199; --accent:#2f6fff; --accent-ink:#cddcff;
  --warn:#f5a623; --live:#37c871;
  --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}}
@media (prefers-color-scheme:light){{:root{{
  --bg:#eef0f3; --card:#fff; --raised:#f3f5f8; --line:#dce0e6;
  --ink:#14171b; --muted:#5c636d; --accent:#1f5fff; --accent-ink:#0a2a6b;
}}}}
:root[data-theme="dark"]{{--bg:#0c0d0f;--card:#17191c;--raised:#202327;--line:#2b2f34;--ink:#e9ebee;--muted:#8b9199;--accent:#2f6fff;--accent-ink:#cddcff;}}
:root[data-theme="light"]{{--bg:#eef0f3;--card:#fff;--raised:#f3f5f8;--line:#dce0e6;--ink:#14171b;--muted:#5c636d;--accent:#1f5fff;--accent-ink:#0a2a6b;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.5;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1180px;margin:0 auto;padding:clamp(20px,4vw,52px)}}
header.top{{border-bottom:1px solid var(--line);padding-bottom:26px;margin-bottom:40px}}
.kicker{{font-family:var(--mono);font-size:12px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin:0 0 10px}}
h1{{font-size:clamp(26px,4vw,40px);line-height:1.08;margin:0 0 12px;font-weight:680;
  letter-spacing:-.02em;text-wrap:balance;max-width:20ch}}
.lede{{color:var(--muted);max-width:66ch;margin:0 0 20px;font-size:16px}}
.meta{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{font-family:var(--mono);font-size:12px;color:var(--ink);background:var(--raised);
  border:1px solid var(--line);border-radius:999px;padding:5px 11px}}
.chip b{{color:var(--accent);font-weight:600}}
.grp{{margin:0 0 46px}}
.grp-h{{display:grid;grid-template-columns:auto 1fr auto;align-items:baseline;gap:14px;
  margin:0 0 18px;padding-bottom:10px;border-bottom:1px solid var(--line)}}
.eyebrow{{font-size:19px;font-weight:640;margin:0;letter-spacing:-.01em}}
.grp-blurb{{color:var(--muted);font-size:13.5px;margin:0}}
.count{{font-family:var(--mono);font-size:12px;color:var(--muted);
  border:1px solid var(--line);border-radius:6px;padding:2px 8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:16px}}
.card{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;
  overflow:hidden;display:flex;flex-direction:column;transition:border-color .15s,transform .15s}}
.card:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.card-wide{{grid-column:1/-1}}
.shot{{background:#000;border-bottom:1px solid var(--line);width:100%;overflow:hidden;
  display:flex;align-items:center;justify-content:center}}
.shot img{{width:100%;height:100%;object-fit:cover;display:block}}
figcaption{{padding:12px 14px 14px;display:flex;flex-direction:column;gap:6px}}
.cap-top{{display:flex;align-items:center;gap:8px;justify-content:space-between}}
h3{{font-size:14.5px;margin:0;font-weight:600;letter-spacing:-.01em}}
.tag{{font-family:var(--mono);font-size:11.5px;color:var(--accent-ink);margin:0;opacity:.85}}
.note{{font-size:12.5px;color:var(--muted);margin:0;line-height:1.45}}
.k{{font-family:var(--mono);font-size:10px;letter-spacing:.05em;text-transform:uppercase;
  padding:2px 7px;border-radius:5px;background:var(--raised);color:var(--muted);border:1px solid var(--line);white-space:nowrap}}
.k-warn{{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,var(--line))}}
.k-live{{color:var(--live);border-color:color-mix(in srgb,var(--live) 40%,var(--line))}}
.tokens{{margin-top:8px;background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:20px 22px}}
.tokens h2{{font-size:16px;margin:0 0 4px;font-weight:640}}
.tokens p{{color:var(--muted);font-size:13px;margin:0 0 16px;max-width:70ch}}
.sws{{display:flex;flex-wrap:wrap;gap:12px}}
.sw{{display:flex;flex-direction:column;gap:4px;align-items:flex-start}}
.sw span{{width:60px;height:34px;border-radius:7px;border:1px solid var(--line);display:block}}
.sw code{{font-family:var(--mono);font-size:11px;color:var(--ink)}}
.sw em{{font-family:var(--mono);font-size:10px;color:var(--muted);font-style:normal;text-transform:uppercase;letter-spacing:.05em}}
footer{{margin-top:34px;color:var(--muted);font-size:12px;font-family:var(--mono);
  border-top:1px solid var(--line);padding-top:16px;line-height:1.7}}
footer a{{color:var(--accent)}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="wrap">
  <header class="top">
    <p class="kicker">IdeaFormer IR3 V2 · KlipperScreen port target</p>
    <h1>Snapmaker U1 — touchscreen UX reference</h1>
    <p class="lede">The U1's local screen is a closed module — not part of the open-sourced
      Klipper/Moonraker/Fluidd. So the UX has to be <em>rebuilt</em>, not forked. This is the full
      visual evidence set: idle &amp; menus from Snapmaker's wiki, and the print/job + wizard
      screens recovered frame-by-frame from a YouTube first-print review.</p>
    <div class="meta">
      <span class="chip">native res <b>480×320</b></span>
      <span class="chip"><b>{n_screens}</b> screens</span>
      <span class="chip">2 sources · wiki + yt</span>
      <span class="chip">single accent <b>#2f6fff</b></span>
    </div>
  </header>
{''.join(body)}
  <section class="tokens">
    <h2>Extracted design tokens</h2>
    <p>Dark canvas, one blue accent reserved for the single primary action, cool-grey neutrals,
      ~14px radii, big flat touch targets. Everything else is quiet.</p>
    <div class="sws">{sw}</div>
  </section>
  <footer>
    idle/menus: wiki.snapmaker.com &nbsp;·&nbsp; print/job + wizards: youtube <a href="https://youtu.be/wnwvCy8JNgo">wnwvCy8JNgo</a> &nbsp;·&nbsp; real panel: github suchmememanyskill/ESP32-Snapmaker-U1-display-mirror<br>
    source set + notes: klipperscreen-nativeui/u1_reference/ · REFERENCE.md
  </footer>
</div>
'''

with open(OUT, "w") as f:
    f.write(HTML)
print("wrote", OUT, f"({len(HTML)//1024} KB), {n_screens} screens")
