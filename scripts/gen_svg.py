#!/usr/bin/env python3
"""TRS Obsidian Red — Kvantum SVG generator.

Generates TRSObsidianRed.svg from scratch (original, programmatic artwork).
Edit the PALETTE / element definitions below and re-run:

    python3 gen_svg.py > ../kvantum/TRSObsidianRed/TRSObsidianRed.svg

Element naming follows the Kvantum element API:
  <name>-<state>            : interior (single stretched rect)
  <name>-<state>-<piece>    : frame pieces (top/bottom/left/right + 4 corners)
"""

# ----------------------------------------------------------------------------
# PALETTE — change colors here
# ----------------------------------------------------------------------------
BG_VIEW      = "#0B0B0B"   # editable areas / views
BG_WINDOW    = "#151515"   # window & menu background
BG_SURFACE   = "#1B1B1B"   # tooltip
BG_BUTTON    = "#1E1E1E"   # buttons
BG_BUTTON_H  = "#272727"   # button hover
BG_BUTTON_P  = "#121212"   # button pressed
BG_INPUT     = "#0F0F0F"   # line edits
BORDER       = "#373737"   # standard border
BORDER_SOFT  = "#2E2E2E"   # subtle border
BORDER_H     = "#4A4A4A"   # hovered border
ACCENT       = "#C1121F"   # main red
ACCENT_H     = "#D72332"   # hover red
ACCENT_DIM   = "#6E0E15"   # dark red (toggled menu item)
ACCENT_PRESS = "#8E1119"   # pressed red
TOGGLE_BG    = "#38151A"   # toggled button fill (red-tinted dark)
HOVER_ROW    = "#212121"   # itemview hover
GROOVE       = "#2E2E2E"   # slider groove
THUMB        = "#4A4A4A"   # scrollbar thumb
THUMB_H      = "#9E2A33"   # scrollbar thumb hover (near-red)
THUMB_P      = ACCENT      # scrollbar thumb pressed
TXT          = "#C8C8C8"   # arrow/indicator stroke
TXT_HI       = "#FFFFFF"
TXT_DIS      = "#5A5A5A"
CHECK_BG     = "#101010"
CHECK_BORDER = "#5A5A5A"

RADIUS = 6                 # main corner radius (buttons, inputs, menus, tabs)
KESKIN = True              # True: dik köşeler ve kare tutamaçlar (TRS Keskin
                           # diliyle uyumlu); False: özgün yuvarlak görünüm.
                           # Çerçeve boyları (RADIUS) kvconfig ile eşleştiği
                           # için değişmez, yalnızca köşenin çizimi değişir.
UC = "butt" if KESKIN else "round"     # çizgi ucu
EK = "miter" if KESKIN else "round"    # çizgi birleşimi

CELL = 48
COLS = 16

items = []   # (id, inner-svg)
defs  = []


def add(eid, inner):
    items.append((eid, inner))


def rect(x, y, w, h, fill, opacity=None, rx=None):
    o = f' fill-opacity="{opacity}"' if opacity is not None else ""
    r = f' rx="{rx}" ry="{rx}"' if rx is not None and not KESKIN else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{o}{r}/>'


def corner_paths(f, bw, fill, border, capsule=False):
    """Top-left corner geometry in an f×f box (radius == f)."""
    p = []
    if KESKIN:   # dik köşe: kenarlık L biçiminde, dolgu kare
        if capsule:
            return rect(0, 0, f, f, fill)
        if border:
            p.append(rect(0, 0, f, bw, border))
            p.append(rect(0, bw, bw, f - bw, border))
        if fill:
            p.append(rect(bw, bw, f - bw, f - bw, fill))
        return "".join(p)
    if capsule:  # borderless, fully filled quarter-disc
        p.append(f'<path d="M0,{f} A{f},{f} 0 0 1 {f},0 L{f},{f} Z" fill="{fill}"/>')
        return "".join(p)
    fi = f - bw
    if border:
        p.append(f'<path d="M0,{f} A{f},{f} 0 0 1 {f},0 L{f},{bw} '
                 f'A{fi},{fi} 0 0 0 {bw},{f} Z" fill="{border}"/>')
    if fill:
        p.append(f'<path d="M{bw},{f} A{fi},{fi} 0 0 1 {f},{bw} L{f},{f} Z" fill="{fill}"/>')
    return "".join(p)


CORNER_TX = {
    "topleft": "",
    "topright": "matrix(-1,0,0,1,{f},0)",
    "bottomleft": "matrix(1,0,0,-1,0,{f})",
    "bottomright": "matrix(-1,0,0,-1,{f},{f})",
}


def side_piece(which, f, bw, fill, border, L=16, capsule=False):
    p = []
    if capsule:
        return rect(0, 0, L if which in ("top", "bottom") else f,
                    f if which in ("top", "bottom") else L, fill)
    if which == "top":
        if border: p.append(rect(0, 0, L, bw, border))
        if fill:   p.append(rect(0, bw, L, f - bw, fill))
    elif which == "bottom":
        if fill:   p.append(rect(0, 0, L, f - bw, fill))
        if border: p.append(rect(0, f - bw, L, bw, border))
    elif which == "left":
        if border: p.append(rect(0, 0, bw, L, border))
        if fill:   p.append(rect(bw, 0, f - bw, L, fill))
    elif which == "right":
        if fill:   p.append(rect(0, 0, f - bw, L, fill))
        if border: p.append(rect(f - bw, 0, bw, L, border))
    return "".join(p)


def frame_set(name, f, bw, fill, border, capsule=False):
    """8 frame pieces for element+state `name` (e.g. button-normal)."""
    tl = corner_paths(f, bw, fill, border, capsule)
    for c, tx in CORNER_TX.items():
        t = tx.format(f=f)
        g = f'<g transform="{t}">{tl}</g>' if t else tl
        add(f"{name}-{c}", g)
    for s in ("top", "bottom", "left", "right"):
        add(f"{name}-{s}", side_piece(s, f, bw, fill, border, capsule=capsule))


def interior(name, fill, opacity=None):
    add(name, rect(0, 0, 24, 24, fill, opacity))


def boxed(name, f, bw, fill, border, capsule=False, opacity=None):
    interior(name, fill if fill else "#000000", opacity if fill else 0)
    frame_set(name, f, bw, fill, border, capsule)


# ----------------------------------------------------------------------------
# Buttons
# ----------------------------------------------------------------------------
boxed("button-normal",  RADIUS, 1, BG_BUTTON,   BORDER)
boxed("button-focused", RADIUS, 1, BG_BUTTON_H, BORDER_H)
boxed("button-pressed", RADIUS, 1, BG_BUTTON_P, BORDER)
boxed("button-toggled", RADIUS, 1, TOGGLE_BG,   ACCENT)
add("button-default-indicator", "")

# Tool buttons: flat when idle
interior("tbutton-normal", BG_BUTTON, 0)
frame_set("tbutton-normal", RADIUS, 1, None, None)
boxed("tbutton-focused", RADIUS, 1, BG_BUTTON_H, "#3A3A3A")
boxed("tbutton-pressed", RADIUS, 1, BG_BUTTON_P, BORDER)
boxed("tbutton-toggled", RADIUS, 1, TOGGLE_BG,   ACCENT)

# ----------------------------------------------------------------------------
# Inputs
# ----------------------------------------------------------------------------
boxed("lineedit-normal",  RADIUS, 1, BG_INPUT, "#3A3A3A")
boxed("lineedit-focused", RADIUS, 1, BG_INPUT, ACCENT)
boxed("lineedit-pressed", RADIUS, 1, BG_INPUT, ACCENT_PRESS)

# ----------------------------------------------------------------------------
# Menu, menu items, menubar
# ----------------------------------------------------------------------------
boxed("menu-normal", RADIUS, 1, BG_WINDOW, "#3A3A3A")
boxed("menuitem-pressed", 4, 0, ACCENT, None, capsule=True)   # hover/selected
boxed("menuitem-toggled", 4, 0, ACCENT_DIM, None, capsule=True)
interior("menubaritem-normal", BG_WINDOW, 0)
frame_set("menubaritem-normal", 4, 0, None, None)
boxed("menubaritem-focused", 4, 0, HOVER_ROW, None, capsule=True)
boxed("menubaritem-pressed", 4, 0, ACCENT, None, capsule=True)
boxed("menubaritem-toggled", 4, 0, ACCENT, None, capsule=True)

# menu & tooltip shadows (soft, no neon)
SH = "#000000"
for i, (name, depth_op) in enumerate((("menu-shadow", 0.45), ("tooltip-shadow", 0.35))):
    gid = f"shgrad{i}"
    defs.append(
        f'<linearGradient id="{gid}v" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{SH}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{SH}" stop-opacity="{depth_op}"/></linearGradient>'
        f'<linearGradient id="{gid}h" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{SH}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{SH}" stop-opacity="{depth_op}"/></linearGradient>'
        f'<radialGradient id="{gid}c" cx="1" cy="1" r="1">'
        f'<stop offset="0" stop-color="{SH}" stop-opacity="{depth_op}"/>'
        f'<stop offset="1" stop-color="{SH}" stop-opacity="0"/></radialGradient>')
    F = 8
    add(f"{name}-top",    f'<rect width="16" height="{F}" fill="url(#{gid}v)"/>')
    add(f"{name}-bottom", f'<g transform="matrix(1,0,0,-1,0,{F})">'
                          f'<rect width="16" height="{F}" fill="url(#{gid}v)"/></g>')
    add(f"{name}-left",   f'<rect width="{F}" height="16" fill="url(#{gid}h)"/>')
    add(f"{name}-right",  f'<g transform="matrix(-1,0,0,1,{F},0)">'
                          f'<rect width="{F}" height="16" fill="url(#{gid}h)"/></g>')
    corner = f'<rect width="{F}" height="{F}" fill="url(#{gid}c)"/>'
    add(f"{name}-topleft", corner)
    add(f"{name}-topright",    f'<g transform="matrix(-1,0,0,1,{F},0)">{corner}</g>')
    add(f"{name}-bottomleft",  f'<g transform="matrix(1,0,0,-1,0,{F})">{corner}</g>')
    add(f"{name}-bottomright", f'<g transform="matrix(-1,0,0,-1,{F},{F})">{corner}</g>')

# ----------------------------------------------------------------------------
# Tooltip
# ----------------------------------------------------------------------------
boxed("tooltip-normal", 4, 1, BG_SURFACE, "#3A3A3A")

# ----------------------------------------------------------------------------
# Item views (Dolphin lists, trees, tables)
# ----------------------------------------------------------------------------
boxed("itemview-focused", 4, 0, HOVER_ROW, None, capsule=True)
boxed("itemview-pressed", 4, 0, "#5A0D13", None, capsule=True)
boxed("itemview-toggled", 4, 0, ACCENT, None, capsule=True)

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
boxed("tab-normal",  RADIUS, 1, "#161616", "#303030")
boxed("tab-focused", RADIUS, 1, HOVER_ROW, "#3A3A3A")
# active tab: lighter fill + red top accent line
tl = corner_paths(RADIUS, 2, "#242424", ACCENT)
add("tab-toggled-topleft", tl)
add("tab-toggled-topright", f'<g transform="matrix(-1,0,0,1,{RADIUS},0)">{tl}</g>')
bl = corner_paths(RADIUS, 1, "#242424", "#3A3A3A")
add("tab-toggled-bottomleft",  f'<g transform="matrix(1,0,0,-1,0,{RADIUS})">{bl}</g>')
add("tab-toggled-bottomright", f'<g transform="matrix(-1,0,0,-1,{RADIUS},{RADIUS})">{bl}</g>')
add("tab-toggled-top",    side_piece("top", RADIUS, 2, "#242424", ACCENT))
add("tab-toggled-bottom", side_piece("bottom", RADIUS, 1, "#242424", "#3A3A3A"))
add("tab-toggled-left",   side_piece("left", RADIUS, 1, "#242424", "#3A3A3A"))
add("tab-toggled-right",  side_piece("right", RADIUS, 1, "#242424", "#3A3A3A"))
interior("tab-toggled", "#242424")
boxed("tabframe-normal", RADIUS, 1, "#111111", "#333333")
add("tab-tear", rect(0, 0, 2, 16, BORDER))
for st, col in (("normal", TXT), ("focused", TXT_HI), ("pressed", TXT_HI),
                ("disabled", TXT_DIS)):
    add(f"tab-close-{st}",
        f'<path d="M4,4 L12,12 M12,4 L4,12" stroke="{col}" stroke-width="1.6" '
        f'stroke-linecap="{UC}" fill="none"/>')

# ----------------------------------------------------------------------------
# Generic frames / group box / header / toolbar / statusbar
# ----------------------------------------------------------------------------
frame_set("common-normal", 1, 1, None, BORDER_SOFT)
frame_set("group-normal", RADIUS, 1, None, BORDER_SOFT)
boxed("header-normal",  2, 1, "#1A1A1A", BORDER_SOFT)
boxed("header-focused", 2, 1, "#222222", BORDER_SOFT)
boxed("header-pressed", 2, 1, "#161616", BORDER_SOFT)
boxed("header-toggled", 2, 1, "#161616", BORDER_SOFT)
add("header-separator", rect(0, 2, 1, 12, "#333333"))
interior("toolbar-normal", BG_WINDOW, 0)
frame_set("toolbar-normal", 2, 0, None, None)
add("toolbar-handle", "".join(rect(3, y, 2, 2, "#4A4A4A") for y in (3, 8, 13)))

# ----------------------------------------------------------------------------
# Progress bar
# ----------------------------------------------------------------------------
boxed("progress-normal", 4, 0, "#232323", None, capsule=True)
boxed("progress-pattern-normal", 4, 0, ACCENT, None, capsule=True)
boxed("progress-pattern-disabled", 4, 0, "#4A4A4A", None, capsule=True)

# ----------------------------------------------------------------------------
# Scrollbars (transient + classic fallback)
# ----------------------------------------------------------------------------
boxed("scrollbargroove-normal", 4, 0, "#1E1E1E", None, capsule=True)
for elem in ("scrollbarslider", "ss"):
    for st, col in (("normal", THUMB), ("focused", THUMB_H), ("pressed", THUMB_P)):
        interior(f"{elem}-{st}", col)
        frame_set(f"{elem}-{st}", 5, 0, col, None, capsule=True)

# ----------------------------------------------------------------------------
# Sliders
# ----------------------------------------------------------------------------
for st, col in (("normal", GROOVE), ("toggled", ACCENT)):
    interior(f"slider-{st}", col)
    frame_set(f"slider-{st}", 2, 0, col, None, capsule=True)
for st, (fill, stroke) in (("normal", (BG_BUTTON, "#909090")),
                           ("focused", (BG_BUTTON, ACCENT)),
                           ("pressed", (ACCENT, ACCENT)),
                           ("disabled", ("#1A1A1A", "#3E3E3E"))):
    knob = (f'<rect x="2.8" y="2.8" width="12.4" height="12.4" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.6"/>') if KESKIN else \
           (f'<circle cx="9" cy="9" r="7.2" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="1.6"/>')
    add(f"slidercursor-{st}", knob)
    add(f"slidercursor-tickless-{st}", knob)

# ----------------------------------------------------------------------------
# Checkboxes & radios
# ----------------------------------------------------------------------------
CHECKMARK = ('<path d="M5.2,9.4 L8,12.2 L12.8,6.2" stroke="#FFFFFF" '
             f'stroke-width="1.9" stroke-linecap="{UC}" stroke-linejoin="{EK}" '
             'fill="none"/>')
TRIBAR = rect(5, 8.1, 8, 1.8, "#FFFFFF", rx=0.9)
def cbox(fill, stroke): return (f'<rect x="1.8" y="1.8" width="14.4" height="14.4" '
                                f'rx="{0 if KESKIN else 4}" ry="{0 if KESKIN else 4}" fill="{fill}" stroke="{stroke}" '
                                f'stroke-width="1.4"/>')
add("checkbox-normal",           cbox(CHECK_BG, CHECK_BORDER))
add("checkbox-focused",          cbox(CHECK_BG, ACCENT))
add("checkbox-checked-normal",   cbox(ACCENT, ACCENT) + CHECKMARK)
add("checkbox-checked-focused",  cbox(ACCENT_H, ACCENT_H) + CHECKMARK)
add("checkbox-tristate-normal",  cbox(ACCENT, ACCENT) + TRIBAR)
add("checkbox-tristate-focused", cbox(ACCENT_H, ACCENT_H) + TRIBAR)

def rbox(fill, stroke): return (f'<circle cx="9" cy="9" r="7.2" fill="{fill}" '
                                f'stroke="{stroke}" stroke-width="1.4"/>')
DOT = '<circle cx="9" cy="9" r="3" fill="#FFFFFF"/>'
add("radio-normal",          rbox(CHECK_BG, CHECK_BORDER))
add("radio-focused",         rbox(CHECK_BG, ACCENT))
add("radio-checked-normal",  rbox(ACCENT, ACCENT) + DOT)
add("radio-checked-focused", rbox(ACCENT_H, ACCENT_H) + DOT)

# ----------------------------------------------------------------------------
# Arrows & spin indicators
# ----------------------------------------------------------------------------
CHEV = {
    "down":  "M4.2,6.5 L8,10.3 L11.8,6.5",
    "up":    "M4.2,10.3 L8,6.5 L11.8,10.3",
    "left":  "M10.3,4.2 L6.5,8 L10.3,11.8",
    "right": "M6.5,4.2 L10.3,8 L6.5,11.8",
}
SIGNS = {
    "plus":  "M8,4.5 L8,11.5 M4.5,8 L11.5,8",
    "minus": "M4.5,8 L11.5,8",
}
STATES = (("normal", TXT), ("focused", TXT_HI), ("pressed", TXT_HI),
          ("toggled", TXT_HI), ("disabled", TXT_DIS))
for d, path in {**CHEV, **SIGNS}.items():
    for st, col in STATES:
        add(f"arrow-{d}-{st}",
            f'<path d="{path}" stroke="{col}" stroke-width="1.7" '
            f'stroke-linecap="{UC}" stroke-linejoin="{EK}" fill="none"/>')
# submenu arrows on red hover -> always white
for side in ("left", "right"):
    for st, col in (("normal", TXT), ("focused", TXT_HI), ("pressed", TXT_HI)):
        add(f"menuitem-{side}-{st}",
            f'<path d="{CHEV[side]}" stroke="{col}" stroke-width="1.7" '
            f'stroke-linecap="{UC}" stroke-linejoin="{EK}" fill="none"/>')

# ----------------------------------------------------------------------------
# Focus ring (thin red)
# ----------------------------------------------------------------------------
frame_set("focus", 2, 1, None, ACCENT)

# ----------------------------------------------------------------------------
# Grips & misc
# ----------------------------------------------------------------------------
dots = "".join(rect(x, 7, 2.4, 2.4, "#5A5A5A", rx=1.2) for x in (2, 7, 12))
for st in ("normal", "focused", "pressed"):
    add(f"splitter-grip-{st}", dots)
    add(f"grip-{st}", dots)
for st, col in (("normal", "#4A4A4A"), ("focused", ACCENT)):
    add(f"resize-grip-{st}",
        f'<path d="M12,4 L4,12 M12,8 L8,12" stroke="{col}" stroke-width="1.4" '
        f'stroke-linecap="{UC}" fill="none"/>')

# ----------------------------------------------------------------------------
# Emit
# ----------------------------------------------------------------------------
out = []
rows = (len(items) + COLS - 1) // COLS
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{COLS*CELL}" height="{rows*CELL}">')
out.append("<defs>" + "".join(defs) + "</defs>")
for i, (eid, inner) in enumerate(items):
    x, y = (i % COLS) * CELL, (i // COLS) * CELL
    out.append(f'<g id="{eid}" transform="translate({x},{y})">{inner}</g>')
out.append("</svg>")
print("\n".join(out))
