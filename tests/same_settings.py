#!/usr/bin/env python3
"""same_settings.py — check that R and Python see the same journal settings.

Usage: same_settings.py <python resolver json> <r_resolve.R json>
jsonlite writes a one-element vector as a scalar, so one-element lists count as
equal to their element. Numbers are compared as floats.
"""
import json, sys

def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return norm(x[0]) if len(x) == 1 else [norm(v) for v in x]
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    return x

py, r = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
same = py["id"] == r["id"] and norm(py["settings"]) == norm(r["settings"])
if not same:
    print("id:", py["id"], r["id"])
    for k in sorted(set(py["settings"]) | set(r["settings"])):
        if norm(py["settings"].get(k)) != norm(r["settings"].get(k)):
            print("differs:", k, py["settings"].get(k), r["settings"].get(k))
sys.exit(0 if same else 1)
