#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_figures.py — figure gate

Purpose: before submission, verify that body figures are complete, correctly
named, of the right pixel width and dpi, free of 0-byte write residue, and that
no figure name has two producers.

Zero third-party dependencies: PNG IHDR and pHYs chunks are parsed by hand.

Usage:
    python check_figures.py output/figures
    python check_figures.py output/figures --expect 7 --width 2244 --dpi 300
    python check_figures.py output/figures --code-dir code        # also scan producers
    python check_figures.py output/figures --pattern "Fig\\d{2}_"

Exit codes: 0 = all checks passed; 1 = hard failure.
"""
from __future__ import annotations

import argparse
import os
import re
import struct
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_info(path: str) -> tuple[int | None, int | None, int | None]:
    """Return (width, height, dpi). Reads the header only, stops at IDAT."""
    with open(path, "rb") as f:
        head = f.read(256 * 1024)
    if not head.startswith(PNG_SIG):
        return None, None, None
    pos, w, h, dpi = 8, None, None, None
    while pos + 8 <= len(head):
        (length,) = struct.unpack(">I", head[pos : pos + 4])
        ctype = head[pos + 4 : pos + 8]
        if ctype == b"IHDR":
            w, h = struct.unpack(">II", head[pos + 8 : pos + 16])
        elif ctype == b"pHYs" and length >= 9:
            px, _py, unit = struct.unpack(">IIB", head[pos + 8 : pos + 17])
            if unit == 1:
                dpi = int(round(px * 0.0254))
        elif ctype == b"IDAT":
            break
        pos += 12 + length
    return w, h, dpi


def find_producers(code_dir: str) -> dict[str, list[str]]:
    """Scan top-level defs. A name appearing in more than one file is a duplicate
    producer and a hard failure: it can silently overwrite a final figure."""
    defs: dict[str, list[str]] = defaultdict(list)
    pat = re.compile(r"^\s*def\s+(plot_\w+|fig\w+_\w+)\s*\(", re.M)
    for root, _dirs, files in os.walk(code_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    for name in pat.findall(f.read()):
                        defs[name].append(os.path.relpath(p, code_dir))
            except OSError:
                continue
    return {k: v for k, v in defs.items() if len(set(v)) > 1}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Figure gate: count / naming / size / dpi / residue / duplicate producers"
    )
    ap.add_argument("fig_dir", help="body figure directory (this level only, not recursive)")
    ap.add_argument("--pattern", default=r"^Fig\d{2}_", help="naming regex (default: FigNN_ prefix)")
    ap.add_argument("--expect", type=int, default=7, help="expected body figure count")
    ap.add_argument("--width", type=int, default=2244, help="expected pixel width (190 mm @ 300 dpi)")
    ap.add_argument("--width-tol", type=int, default=2, help="width tolerance in px")
    ap.add_argument("--dpi", type=int, default=300, help="minimum dpi")
    ap.add_argument("--code-dir", default=None, help="code directory, for duplicate-producer detection")
    ap.add_argument("--require-pdf", action="store_true", help="require a vector PDF per PNG")
    args = ap.parse_args()

    if not os.path.isdir(args.fig_dir):
        print(f"[FAIL] directory not found: {args.fig_dir}")
        return 1

    name_pat = re.compile(args.pattern)
    all_files = [
        f for f in os.listdir(args.fig_dir) if os.path.isfile(os.path.join(args.fig_dir, f))
    ]
    # When savefig has its target handle held (editor preview, sync client, preview
    # panel) matplotlib leaves a 0-byte ".<real name>.<random>.png|.pdf" placeholder.
    # Content is always empty: pure residue.
    strays = [
        f for f in all_files if f.startswith(".") and re.search(r"\.(png|pdf)\.", f, re.I)
    ]
    pngs = sorted(
        f for f in all_files if f.lower().endswith(".png") and not f.startswith(".")
    )

    fails: list[str] = []
    rows: list[tuple[str, str, str, str]] = []

    for fn in pngs:
        p = os.path.join(args.fig_dir, fn)
        w, h, dpi = png_info(p)
        issues = []
        if not name_pat.search(fn):
            issues.append("naming")
        if w is None:
            issues.append("not a valid PNG")
        else:
            if abs(w - args.width) > args.width_tol:
                issues.append(f"width {w} != {args.width}")
            if dpi is None:
                issues.append("no pHYs (dpi undeclared)")
            elif dpi < args.dpi:
                issues.append(f"dpi {dpi} < {args.dpi}")
        if args.require_pdf and not os.path.exists(p[:-4] + ".pdf"):
            issues.append("missing PDF")
        rows.append(
            (fn, f"{w}x{h}" if w else "?", str(dpi or "-"), "PASS" if not issues else "; ".join(issues))
        )
        if issues:
            fails.append(f"{fn}: {', '.join(issues)}")

    # Count guard: must equal the expected value exactly, and must not be satisfied
    # by counting every file in the directory.
    if len(pngs) != args.expect:
        fails.append(
            f"body figure count {len(pngs)} != expected {args.expect} "
            "(the root level must hold body figures only)"
        )

    if strays:
        shown = ", ".join(strays[:5]) + (" …" if len(strays) > 5 else "")
        fails.append(
            f"{len(strays)} write residue file(s) — 0-byte placeholders left by a held "
            f"savefig handle; move to quarantine: {shown}"
        )

    dup = find_producers(args.code_dir) if args.code_dir else {}
    if dup:
        for name, files in sorted(dup.items()):
            fails.append(
                f"duplicate producer def {name}() in {', '.join(sorted(set(files)))}"
            )

    print(f"Directory: {args.fig_dir}")
    print(f"{'file':<44}{'size':<14}{'dpi':<6}verdict")
    print("-" * 78)
    for fn, wh, dpi, verdict in rows:
        print(f"{fn[:42]:<44}{wh:<14}{dpi:<6}{verdict}")

    print("-" * 78)
    if dup:
        print(f"[duplicate producers] {len(dup)} group(s)")
    if fails:
        print(f"\n{len(fails)} hard failure(s):")
        for x in fails:
            print("  ·", x)
    summary = f"{len(pngs)} figure(s) + count guard"
    if args.code_dir:
        summary += f" + {len(dup)} duplicate-producer group(s)"
    print(f"\nVerdict: {'PASS' if not fails else 'FAIL'}   checked {summary}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
