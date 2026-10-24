#!/usr/bin/env python3
"""
check_figure.py — validate a figure file against a journal's figure spec.

Measures what is machine-checkable — physical width vs the journal column spec,
vector-vs-raster, resolution (dpi), grayscale-vs-color — and reports PASS/WARN/FAIL.
Things it cannot measure from pixels (panel labels, legibility at print size, chart-type
anti-patterns, plain-language axis titles, grayscale-survivability) are listed as a
VISION checklist to run by eye against the `notes` in the journal's profile.

Usage:
  python3 check_figure.py figure.pdf  --journal ASR
  python3 check_figure.py figure.png  --journal PNAS --width single   # single|full|any

Handles: .pdf .eps .svg (vector), .png .jpg .tif (raster). Uses Pillow + pypdf + stdlib.
"""
import argparse, os, re, sys, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from profiles import ProfileError, resolve
CM = 2.54

REPORT = {"PASS": 0, "WARN": 0, "FAIL": 0}
def emit(level, check, msg):
    REPORT[level] += 1
    icon = {"PASS": "✓", "WARN": "▲", "FAIL": "✗"}[level]
    print(f"  {icon} [{level}] {check}: {msg}")


def load_spec(journal):
    """Return the resolved figure profile, or exit with the resolver's message."""
    try:
        return resolve(journal, "figures")
    except ProfileError as e:
        print(f"check_figure.py: {e}", file=sys.stderr)
        sys.exit(2)


LABELS = {"single_col": "single", "full_width": "full", "one_and_half_col": "1.5col"}
UNITS = {"_in": 1.0, "_cm": 1 / CM, "_mm": 1 / 25.4}


def allowed_widths_in(spec):
    """Return dict label->inches of acceptable figure widths from the spec.

    Any width key ending in _in, _cm, or _mm counts, e.g., single_col_mm: 89 or
    double_col_mm: 121. Heights (max_height_*) are not widths.
    """
    w = spec.get("width", {}) or {}
    out = {}
    for k, v in w.items():
        unit = k[-3:]
        if unit not in UNITS or k.startswith("max_height") or not isinstance(v, (int, float)):
            continue
        base = k[:-3]
        out[LABELS.get(base, base)] = v * UNITS[unit]
    return out


def measure(path):
    """Return dict: kind(vector/raster), width_in, dpi, has_raster, grayscale, palette_note."""
    ext = os.path.splitext(path)[1].lower()
    info = {"ext": ext, "kind": None, "width_in": None, "dpi": None,
            "has_raster": None, "grayscale": None, "note": ""}
    if ext == ".pdf":
        info["kind"] = "vector"
        try:
            from pypdf import PdfReader
            r = PdfReader(path); pg = r.pages[0]
            box = pg.mediabox
            info["width_in"] = round(float(box.width) / 72.0, 2)
            xo = pg.get("/Resources", {}).get("/XObject", {})
            try:
                imgs = [k for k in xo.keys() if xo[k].get("/Subtype") == "/Image"]
                info["has_raster"] = len(imgs) > 0
            except Exception:
                info["has_raster"] = None
        except Exception as e:
            info["note"] = f"pdf read error: {e}"
    elif ext == ".svg":
        info["kind"] = "vector"
        try:
            root = ET.parse(path).getroot()
            w = root.get("width", "")
            m = re.match(r"([\d.]+)\s*(mm|cm|in|pt|px)?", w or "")
            if m:
                val = float(m.group(1)); unit = m.group(2) or "px"
                conv = {"mm": 1/25.4, "cm": 1/CM, "in": 1, "pt": 1/72, "px": 1/96}[unit]
                info["width_in"] = round(val * conv, 2)
        except Exception as e:
            info["note"] = f"svg parse error: {e}"
    elif ext == ".eps":
        info["kind"] = "vector"
        try:
            txt = open(path, "rb").read(4000).decode("latin-1", "replace")
            m = re.search(r"%%BoundingBox:\s*\d+\s+\d+\s+(\d+)\s+(\d+)", txt)
            if m:
                info["width_in"] = round(int(m.group(1)) / 72.0, 2)
        except Exception as e:
            info["note"] = f"eps parse error: {e}"
    elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        info["kind"] = "raster"
        try:
            from PIL import Image
            im = Image.open(path)
            px_w = im.size[0]
            dpi = im.info.get("dpi", (None,))[0]
            info["dpi"] = round(dpi) if dpi else None
            if dpi:
                info["width_in"] = round(px_w / dpi, 2)
            else:
                info["note"] = f"{px_w}px wide, no DPI metadata (physical size unknown)"
            # grayscale = (almost) no chromatic pixels — judge by saturation, not by the
            # white background (a sparse color scatter is mostly white but NOT grayscale).
            small = im.convert("RGB").resize((100, 100))
            px = list(small.getdata())
            chroma = sum(1 for r, g, b in px if (max(r, g, b) - min(r, g, b)) > 40)
            frac = chroma / len(px)
            info["grayscale"] = frac < 0.004
            info["note"] += f" | chromatic pixels {frac*100:.1f}%"
            has_red = any(r > 140 and g < 100 and b < 100 for r, g, b in px)
            has_green = any(g > 120 and r < 100 and b < 100 for r, g, b in px)
            if has_red and has_green:
                info["note"] += " | red AND green present — check red-green colorblind safety"
        except Exception as e:
            info["note"] = f"image read error: {e}"
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--journal", default="ASR")
    ap.add_argument("--width", default="any",
                    help="single | full | any, or another width the profile names, e.g., double_col")
    args = ap.parse_args()
    if not os.path.isfile(args.path):
        print(f"check_figure.py: no such file: {args.path}", file=sys.stderr)
        sys.exit(2)
    R = load_spec(args.journal)
    spec, journal = R["settings"], R["id"]
    print(f"\nChecking {args.path}  against  {journal} figure spec\n" + "-" * 56)
    m = measure(args.path)
    if m["note"].startswith(("pdf read error", "svg parse error", "eps parse error", "image read error")):
        print(f"check_figure.py: could not read {args.path}: {m['note']}", file=sys.stderr)
        sys.exit(2)

    # format / vector
    if m["kind"] == "vector":
        emit("PASS", "format", f"Vector ({m['ext']}) — good for line art/charts.")
        if m["has_raster"]:
            emit("WARN", "embedded-raster", "PDF embeds raster image(s); for pure line art keep it vector.")
    elif m["kind"] == "raster":
        if spec.get("vector_preferred", True):
            emit("WARN", "format", f"Raster ({m['ext']}). Journals prefer VECTOR (PDF/EPS/SVG) for charts/line art; raster is fine for photos/maps.")
        dmin = (spec.get("raster", {}) or {}).get("dpi_min_line_art", 600)
        if m["dpi"]:
            emit("PASS" if m["dpi"] >= dmin else "WARN", "resolution",
                 f"{m['dpi']} dpi (line-art min {dmin}).")
        else:
            emit("WARN", "resolution", "No DPI metadata — cannot verify resolution or physical size. Re-export with dpi set.")
    else:
        emit("WARN", "format", f"Unrecognized/unsupported file type: {m['ext']}")

    # width vs column spec
    aw = allowed_widths_in(spec)
    if m["width_in"] and aw:
        tol = 0.18
        hits = [f"{k}~{v:.2f}in" for k, v in aw.items() if abs(m["width_in"] - v) <= v * tol]
        if args.width != "any" and args.width not in aw:
            print(f"check_figure.py: {journal} has no '{args.width}' width; it has {', '.join(aw)}", file=sys.stderr)
            sys.exit(2)
        target = aw.get(args.width) if args.width != "any" else None
        if target and abs(m["width_in"] - target) > target * tol:
            emit("WARN", "width", f"Width {m['width_in']}in != requested {args.width} column ({target:.2f}in).")
        elif hits:
            emit("PASS", "width", f"Width {m['width_in']}in matches {', '.join(hits)}.")
        else:
            opts = ", ".join(f"{k} {v:.2f}in" for k, v in aw.items())
            emit("WARN", "width", f"Width {m['width_in']}in matches no column spec (allowed: {opts}). Resize to a column width.")
    elif aw and not m["width_in"]:
        emit("WARN", "width", "Could not determine physical width — verify it fits a column spec by hand.")

    # color / grayscale
    if m["kind"] == "raster":
        pol = (spec.get("color", {}) or {}).get("policy", "grayscale_preferred")
        if m["grayscale"]:
            emit("PASS", "color", "Grayscale — safe for B/W printing.")
        else:
            lvl = "WARN" if pol == "grayscale_preferred" else "PASS"
            emit(lvl, "color", f"Color figure. {journal} policy: {pol}. Ensure series stay distinct in grayscale (dash/marker/shade, not hue alone).")
    if m["note"].strip():
        print(f"    · {m['note'].strip()}")

    # things only a human/VLM can judge
    print("-" * 56)
    print(f"  VISION checklist (judge by eye vs the `notes` in references/journals/{journal}.yaml):")
    cap = (spec.get("caption", {}) or {}).get("position", "below")
    fmt = (spec.get("caption", {}) or {}).get("format", "Figure {n}.")
    print(f"    [ ] Caption {cap.upper()} the figure, format '{fmt}'")
    print("    [ ] Series distinguishable in grayscale (dash + marker + shade, not hue alone)")
    print("    [ ] Plain-language axis titles; minimal/no gridlines")
    print("    [ ] Uncertainty as CI band/whisker (NOT dynamite bars); no 3D/pie/dual-axis")
    print("    [ ] Multi-panel labels present + consistent; text legible at print size")
    print("-" * 56)
    print(f"  {REPORT['FAIL']} FAIL  {REPORT['WARN']} WARN  {REPORT['PASS']} PASS")
    print(f"  Profile: {journal} figures, evidence {R['status']}, checked {R['checked'] or 'never'}, {R['ready']}")
    for w in R["warnings"]:
        print(f"  Note: {w}")
    sys.exit(1 if REPORT["FAIL"] else 0)


if __name__ == "__main__":
    main()
