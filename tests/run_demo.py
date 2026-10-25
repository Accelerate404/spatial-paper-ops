#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_demo.py — end-to-end demonstration on synthetic data

Builds a throwaway project in a temporary directory (fake figures, fake
manuscripts, fake config), then runs the full gate twice: once on a clean
project, once with deliberately planted defects. Nothing outside the temporary
directory is read or written.

Usage:
    python tests/run_demo.py
    python tests/run_demo.py --keep     # keep the temp directory for inspection

Exit code: 0 if the demo behaved as documented, 1 otherwise.
"""
from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import tempfile
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
GATE = os.path.join(ASSETS, "gate.py")


def make_png(path: str, width: int = 2244, height: int = 900, dpi: int = 300) -> None:
    """Write a minimal but valid RGB PNG, standard library only.

    Exercises the same IHDR/pHYs parsing that check_figures.py performs, so the
    demo verifies the parser rather than bypassing it.
    """

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + typ
            + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + b"\xff\xff\xff" * width
    idat = zlib.compress(row * height, 6)
    ppu = int(round(dpi / 0.0254))
    phys = struct.pack(">IIB", ppu, ppu, 1)
    with open(path, "wb") as f:
        f.write(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"pHYs", phys)
            + chunk(b"IDAT", idat)
            + chunk(b"IEND", b"")
        )


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_valid(root: str) -> None:
    figs = os.path.join(root, "output", "figures")
    os.makedirs(figs, exist_ok=True)
    for i in range(1, 4):
        make_png(os.path.join(figs, f"Fig0{i}_Demo_Panel.png"))

    write(
        os.path.join(root, "manuscript_zh.md"),
        "# 示例稿件\n\n"
        "## 研究区与数据\n\n"
        "研究区面积为 5.6 万 km²，2023 年末常住人口约 8600 万，"
        "地区生产总值占全国的 11.1%，配置重心西移 15.5 km，经济占比 70.2%（图1；表1）。\n\n"
        "**（表1）示例三线表**\n\n"
        "| 分区 | 城市数 | 投入占比 |\n| --- | --- | --- |\n| 核心 | 4 | 36.5 |\n"
        "| 中间 | 4 | 37.5 |\n| 外围 | 3 | 26.1 |\n",
    )
    write(
        os.path.join(root, "manuscript_en.md"),
        "# Demo manuscript\n\n"
        "## Study area and data\n\n"
        "The study area covers 5.6 thousand km2 with a resident population of about "
        "86 million, contributing 11.1% of national GDP; the allocation centroid "
        "shifted 15.5 km westward with a 70.2% economic share (Figure 1; Table 1).\n\n"
        "**Table 1 Demo three-line table**\n\n"
        "| zone | cities | investment share |\n| --- | --- | --- |\n| core | 4 | 36.5 |\n"
        "| intermediate | 4 | 37.5 |\n| peripheral | 3 | 26.1 |\n",
    )
    write(
        os.path.join(root, "gate.toml"),
        "[defaults.figures]\n"
        'fig_dir = "output/figures"\n'
        "expect = 3\n"
        "width = 2244\n"
        "dpi = 300\n\n"
        "[defaults.text]\n"
        'md_eol = "lf"\n'
        'py_eol = "lf"\n\n'
        "[[recon]]\n"
        'name = "record vs translation"\n'
        'left = "manuscript_zh.md"\n'
        'right = "manuscript_en.md"\n\n'
        "[[figures]]\n"
        'name = "demo figures"\n\n'
        "[[text]]\n"
        'name = "manuscript of record"\n'
        'paths = ["manuscript_zh.md"]\n',
    )


def plant_defects(root: str) -> None:
    """Plant one defect per layer, each independently detectable."""
    figs = os.path.join(root, "output", "figures")
    # L3: 0-byte write residue, as left behind by a held savefig handle
    open(os.path.join(figs, ".Fig01_Demo_Panel.png.ab12cd.png"), "wb").close()
    # L4: a colon in a heading, and inline bold in body text
    p = os.path.join(root, "manuscript_zh.md")
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n## 结果：空间格局\n\n这里出现了**行内加粗**，按照规范属于违规。\n")
    # L5: a decimal value that drifted by 0.1 on the derived side
    p = os.path.join(root, "manuscript_en.md")
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n## Results\n\nThe centroid shifted 15.4 km, not the same number.\n")


def run(cmd: list[str], cwd: str) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser(description="End-to-end demo on synthetic data")
    ap.add_argument("--keep", action="store_true", help="keep the temporary project directory")
    args = ap.parse_args()

    root = tempfile.mkdtemp(prefix="spo_demo_")
    ok = True
    try:
        print(f"Temporary project: {root}\n")

        build_valid(root)
        code, out = run([sys.executable, GATE, "--config", "gate.toml"], root)
        print("--- Scenario 1: clean project (expect PASS, exit 0) ---")
        print(out.strip().splitlines()[-1] if out.strip() else "(no output)")
        print(f"exit code: {code}\n")
        if code != 0:
            ok = False

        plant_defects(root)
        code, out = run([sys.executable, GATE, "--config", "gate.toml"], root)
        print("--- Scenario 2: defect planted in each layer (expect FAIL, exit 1) ---")
        print(out.strip().splitlines()[-1] if out.strip() else "(no output)")
        print(f"exit code: {code}\n")
        if code != 1:
            ok = False

        print("--- Scenario 3: misspelled config key (expect exit 2) ---")
        with open(os.path.join(root, "gate.toml"), "a", encoding="utf-8", newline="\n") as f:
            f.write('\nexpectt = 99\n')
        code, out = run([sys.executable, GATE, "--config", "gate.toml"], root)
        first_fail = next((l for l in out.splitlines() if "unknown" in l), "")
        print(first_fail.strip() or out.strip().splitlines()[-1])
        print(f"exit code: {code}\n")
        if code != 2:
            ok = False

        print("=" * 60)
        print("Demo result:", "as documented" if ok else "UNEXPECTED — check the scripts")
    finally:
        if args.keep:
            print(f"\nKept: {root}")
        else:
            import shutil

            shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
