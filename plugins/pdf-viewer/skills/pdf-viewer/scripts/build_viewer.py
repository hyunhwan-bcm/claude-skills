#!/usr/bin/env python3
"""Build a PDF viewer page for a claude.ai Artifact from one or more PDFs.

Writes OUT/<name>.html (the page) and copies each PDF into OUT/, then prints the Artifact publish
parameters: file_path and the files map that publishes the PDFs next to the page.

Usage:
  build_viewer.py --out DIR --title "Talk Name" --pdf "Slides=deck.pdf" [--pdf "With notes=deck-notes.pdf"]
                  [--heading "Talk Name"] [--subtitle "One line under the heading"] [--accent "#007948"]

The first --pdf is shown first; with two or more, the page shows a switch between them.
Standard library only.
"""

import argparse
import colorsys
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "viewer.html")
MAX_FILE = 15 * 1024 * 1024      # Artifact limit for one binary file
MAX_PUBLISH = 64 * 1024 * 1024   # Artifact limit for one publish


def hex_rgb(h):
    h = h.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        sys.exit(f"--accent must be a hex colour like #007948, got {h!r}")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_hex(c):
    return "#" + "".join(f"{round(max(0, min(1, x)) * 255):02X}" for x in c)


def mix(a, b, t):
    return tuple(x * (1 - t) + y * t for x, y in zip(a, b))


def luminance(c):
    def ch(x):
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def palette(accent_hex):
    """Accent colours for light and dark themes, from one hex value."""
    a = hex_rgb(accent_hex)
    white, light_bg, dark_bg = (1, 1, 1), hex_rgb("#F8F7F3"), hex_rgb("#111315")
    h, l, s = colorsys.rgb_to_hls(*a)
    dark = colorsys.hls_to_rgb(h, max(l, 0.62), min(1, s * 0.85))   # lighter for dark backgrounds
    ink = (1, 1, 1) if luminance(a) < 0.35 else hex_rgb("#111315")
    dark_ink = hex_rgb("#08090A") if luminance(dark) > 0.3 else (1, 1, 1)
    return {
        "__ACCENT__": rgb_hex(a),
        "__ACCENT_INK__": rgb_hex(ink),
        "__ACCENT_SOFT__": rgb_hex(mix(a, white, 0.84)),
        "__ACCENT_DARK__": rgb_hex(dark),
        "__ACCENT_DARK_INK__": rgb_hex(dark_ink),
        "__ACCENT_DARK_SOFT__": rgb_hex(mix(dark, dark_bg, 0.78)),
    }


def slug(s):
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-").lower()
    return s or "document"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="folder to write the page and the PDFs into")
    ap.add_argument("--title", required=True, help="the page's name (browser tab and gallery): two to four words")
    ap.add_argument("--heading", help="large text at the top left (default: the title)")
    ap.add_argument("--subtitle", default="", help="one line beside the heading")
    ap.add_argument("--pdf", action="append", required=True, metavar="LABEL=PATH",
                    help="a version to show, e.g. 'Slides=deck.pdf'; repeat for more versions")
    ap.add_argument("--accent", default="#007948", help="accent colour, hex (default #007948)")
    ap.add_argument("--name", help="file name of the page, without .html (default: from the title)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    docs, files, total, used = [], {}, 0, set()
    for spec in args.pdf:
        if "=" not in spec:
            sys.exit(f"--pdf needs LABEL=PATH, got {spec!r}")
        label, path = spec.split("=", 1)
        label, path = label.strip(), os.path.expanduser(path.strip())
        if not os.path.isfile(path):
            sys.exit(f"no such file: {path}")
        with open(path, "rb") as f:
            if f.read(5) != b"%PDF-":
                sys.exit(f"not a PDF: {path}")
        size = os.path.getsize(path)
        if size > MAX_FILE:
            sys.exit(f"{path} is {size / 1e6:.1f} MB; an Artifact file can be at most 15 MB. "
                     "Shrink it first (for example: gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o small.pdf big.pdf).")
        total += size
        name = slug(os.path.splitext(os.path.basename(path))[0]) + ".pdf"
        while name in used:
            name = name[:-4] + "-2.pdf"
        used.add(name)
        dest = os.path.join(args.out, name)
        if os.path.abspath(dest) != os.path.abspath(path):
            shutil.copyfile(path, dest)
        docs.append({"label": label, "file": name})
        files[name] = os.path.abspath(dest)
    if total > MAX_PUBLISH:
        sys.exit(f"the PDFs add up to {total / 1e6:.1f} MB; one publish can carry at most 64 MB")

    with open(TEMPLATE, encoding="utf-8") as f:
        page = f.read()
    heading = args.heading or args.title
    swaps = {
        "__TITLE__": html.escape(args.title),
        "__HEADING__": html.escape(heading),
        "__SUBTITLE__": html.escape(args.subtitle),
        "__DOCS__": json.dumps(docs, ensure_ascii=False).replace("</", "<\\/"),
    }
    swaps.update(palette(args.accent))
    for k, v in swaps.items():
        page = page.replace(k, v)
    left = re.findall(r"__[A-Z_]+__", page)
    if left:
        sys.exit(f"template placeholders left unfilled: {sorted(set(left))}")

    page_path = os.path.abspath(os.path.join(args.out, (args.name or slug(args.title)) + ".html"))
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page)

    print(json.dumps({
        "file_path": page_path,
        "files": files,
        "total_mb": round(total / 1e6, 1),
        "next": "Publish with the Artifact tool: file_path and files as above, plus icon on the first publish. "
                "To update later, rebuild into the same --out folder and publish the same file_path again.",
    }, indent=2))


if __name__ == "__main__":
    main()
