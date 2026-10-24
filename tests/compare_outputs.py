#!/usr/bin/env python3
"""compare_outputs.py — compare rendered outputs with tests/baselines.

Usage: compare_outputs.py <baseline dir> <new dir>
Text files must match line for line, except for the differences allowed in
baselines/ALLOWED_DIFFS.md: checker reports may add "Profile:" and "Note:" lines,
and the VISION checklist line now names the profile file. PNG files must match
pixel for pixel. Every baseline file must exist in the new folder.
"""
import os, re, sys
from PIL import Image, ImageChops

base, new = sys.argv[1], sys.argv[2]
ADDED = re.compile(r"^  (Profile|Note): ")
VISION = re.compile(r"^  VISION checklist \(.*\):$")

def lines(path):
    out = []
    for l in open(path, encoding="utf-8").read().splitlines():
        if ADDED.match(l):
            continue
        out.append("  VISION checklist" if VISION.match(l) else l)
    return out

bad = 0
for f in sorted(os.listdir(base)):
    b, n = os.path.join(base, f), os.path.join(new, f)
    if f.endswith((".md", ".docx")):
        continue                       # docx is compared through its .docx.xml copy
    if not os.path.exists(n):
        print("missing:", f); bad += 1; continue
    if f.endswith(".png"):
        x, y = Image.open(b).convert("RGB"), Image.open(n).convert("RGB")
        if x.size != y.size or ImageChops.difference(x, y).getbbox() is not None:
            print("png differs:", f); bad += 1
    elif lines(b) != lines(n):
        print("text differs:", f); bad += 1
print(f"{bad} file(s) differ")
sys.exit(1 if bad else 0)
