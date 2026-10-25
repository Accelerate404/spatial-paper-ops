#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
safe_replace.py — assertion-guarded find/replace for manuscript revision

Each feature addresses a real incident:
  1. When the replacement contains the original, testing count(OLD)==0 always
     fails   → criterion becomes count(OLD)==count(NEW)
  2. Multi-line replacements in a CRLF file scramble line endings
                                                        → original EOL preserved
  3. A wrong edit cannot be undone                     → automatic snapshot
  4. Two edits in one file overwrite each other        → one at a time, asserted

Usage:
    python safe_replace.py draft.md --old "constraint boundary" --new "spatial constraint boundary" --dry-run
    python safe_replace.py draft.md --old "Fig15" --new "Fig03" --expect 4
    python safe_replace.py draft.md --old "A" --new "B" --backup-dir data/_backup

Exit codes: 0 = replaced and verified; 1 = assertion failed (nothing written).
"""
from __future__ import annotations

import argparse
import datetime
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Assertion-guarded find/replace with line-ending preservation"
    )
    ap.add_argument("path")
    ap.add_argument("--old", required=True, help="original string")
    ap.add_argument("--new", required=True, help="replacement string")
    ap.add_argument(
        "--expect", type=int, default=None, help="expected replacement count (default: occurrences of --old)"
    )
    ap.add_argument("--backup-dir", default=None, help="snapshot directory (default: ./_backup next to the file)")
    ap.add_argument("--dry-run", action="store_true", help="print only, write nothing")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        print(f"[FAIL] file not found: {args.path}")
        return 1
    if args.old == args.new:
        print("[FAIL] --old and --new are identical, nothing to do")
        return 1

    with open(args.path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    eol = "\r\n" if crlf > bare_lf else "\n"

    n_old_before = text.count(args.old)
    n_new_before = text.count(args.new)

    if n_old_before == 0:
        print(f"[FAIL] --old occurs 0 times, nothing to replace: {args.old!r}")
        print("       Read the target paragraph first: punctuation, spacing and")
        print("       curly-vs-straight quotes are the usual causes of a miss.")
        return 1

    expect = args.expect if args.expect is not None else n_old_before
    if args.expect is not None and args.expect != n_old_before:
        print(
            f"[FAIL] --old occurs {n_old_before} time(s), not the declared {args.expect}; refusing to run"
        )
        return 1

    new_text = text.replace(args.old, args.new)
    n_old_after = new_text.count(args.old)
    n_new_after = new_text.count(args.new)

    # Bidirectional assertion: when NEW contains OLD, the criterion is count
    # equality, not the old string reaching zero.
    nested = args.old in args.new
    problems = []
    if nested:
        if n_new_after != n_new_before + expect:
            problems.append(
                f"added {n_new_after - n_new_before} occurrence(s), expected {expect} "
                "(nested replacement: the old string reaching zero is not the criterion)"
            )
    else:
        if n_old_after != 0:
            problems.append(f"{n_old_after} occurrence(s) of the old string remain")
        if n_new_after != n_new_before + expect:
            problems.append(f"added {n_new_after - n_new_before} occurrence(s), expected {expect}")

    eol_label = "CRLF" if eol == "\r\n" else "LF"
    print(f"File: {args.path}   line endings: {eol_label}")
    print(
        f"old: {n_old_before} occurrence(s) -> new: net +{n_new_after - n_new_before}"
        + (" (nested replacement)" if nested else "")
    )
    if problems:
        print("[FAIL] assertion not satisfied, nothing written:")
        for p in problems:
            print("  ·", p)
        return 1

    if args.dry_run:
        print("[DRY-RUN] assertion satisfied, nothing written")
        return 0

    bdir = args.backup_dir or os.path.join(
        os.path.dirname(os.path.abspath(args.path)), "_backup"
    )
    os.makedirs(bdir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    bak = os.path.join(bdir, f"{os.path.basename(args.path)}.{stamp}.bak")
    shutil.copy2(args.path, bak)

    if eol == "\r\n":
        new_text = new_text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(args.path, "wb") as f:
        f.write(new_text.encode("utf-8"))

    # Post-write verification, in case encoding or line-ending handling drifted
    with open(args.path, "rb") as f:
        after = f.read().decode("utf-8")
    if after.count(args.new) < n_new_after:
        print(f"[FAIL] post-write verification failed; snapshot kept at {bak}")
        return 1

    print(f"[OK] written. Snapshot: {bak}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
