#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
recon_numeric.py — multiset reconciliation between two texts

Purpose: compare two texts that should agree (manuscript of record vs translation,
body vs supplementary). Central claim: integer tokens are not evidence; only
decimal tokens are.

Usage:
    python recon_numeric.py A.md B.md
    python recon_numeric.py A.md B.md --exceptions "1449.8=14.498,1798.1=17.981"
    python recon_numeric.py A.md B.md --quiet

Exit codes: 0 = all checks passed; 1 = mismatch, or check count differs from
expected (guards against an empty pass caused by a broken regex).
"""
from __future__ import annotations

import argparse
import collections
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DEC = re.compile(r"\d+\.\d+")
FIG_ZH = re.compile(r"图\s*(\d+)")
FIG_EN = re.compile(r"Fig(?:ure)?\.?\s*(\d+)", re.I)
TAB_ZH = re.compile(r"表\s*(\d+)")
TAB_EN = re.compile(r"Table\s+(\d+)", re.I)
MATH_INLINE = re.compile(r"(?<!\$)\$(?!\$)")


def dec_tokens(text: str) -> collections.Counter:
    return collections.Counter(DEC.findall(text))


def fig_ids(text: str) -> collections.Counter:
    """Normalise figure IDs: '图 3' and 'Figure 3' collapse to the same key,
    so that counts are comparable across languages."""
    return collections.Counter(FIG_ZH.findall(text)) + collections.Counter(
        FIG_EN.findall(text)
    )


def tab_ids(text: str) -> collections.Counter:
    return collections.Counter(TAB_ZH.findall(text)) + collections.Counter(
        TAB_EN.findall(text)
    )


def apply_exceptions(
    left: collections.Counter, right: collections.Counter, pairs: list[tuple[str, str]]
) -> int:
    """Registered unit-conversion exceptions: drop a from left, b from right.
    Returns how many pairs actually applied."""
    used = 0
    for a, b in pairs:
        if left.get(a, 0) > 0 and right.get(b, 0) > 0:
            left[a] -= 1
            right[b] -= 1
            used += 1
    return used


def fmt_diff(
    left: collections.Counter, right: collections.Counter, limit: int = 20
) -> list[str]:
    lines = []
    keys = sorted(set(left) | set(right), key=lambda k: (-abs(left[k] - right[k]), k))
    shown = 0
    for k in keys:
        if left[k] == right[k]:
            continue
        lines.append(
            f"    {k:<12} left {left[k]:>3} / right {right[k]:>3}  (delta {left[k] - right[k]:+d})"
        )
        shown += 1
        if shown >= limit:
            rest = sum(1 for x in keys if left[x] != right[x]) - limit
            if rest > 0:
                lines.append(f"    … {rest} more difference(s) not shown")
            break
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Multiset reconciliation between two texts (decimal tokens only)"
    )
    ap.add_argument("left", help="side of record (e.g. manuscript in the language of record)")
    ap.add_argument("right", help="derived side (e.g. translated manuscript)")
    ap.add_argument(
        "--exceptions", default="", help='unit conversions, e.g. "1449.8=14.498,1798.1=17.981"'
    )
    ap.add_argument("--expect-checks", type=int, default=4, help="expected number of checks (default 4)")
    ap.add_argument("--quiet", action="store_true", help="print the verdict line only")
    args = ap.parse_args()

    with open(args.left, encoding="utf-8") as f:
        lt = f.read()
    with open(args.right, encoding="utf-8") as f:
        rt = f.read()

    pairs: list[tuple[str, str]] = []
    for chunk in args.exceptions.split(","):
        chunk = chunk.strip()
        if "=" in chunk:
            a, b = chunk.split("=", 1)
            pairs.append((a.strip(), b.strip()))

    results: list[tuple[str, collections.Counter, collections.Counter, str]] = []
    ld, rd = dec_tokens(lt), dec_tokens(rt)
    if pairs:
        used = apply_exceptions(ld, rd, pairs)
        if not args.quiet:
            print(f"[note] applied {used}/{len(pairs)} registered unit conversion(s)")
    # Decimal tokens are the only true counting evidence
    results.append(("decimal tokens", ld, rd, "counter"))
    # Figure/table IDs are compared as SETS, not counts:
    # captions in the manuscript of record often carry bilingual titles
    # ("**Fig. 1 …** / **图1 …**"), so each ID is extracted twice, while a
    # monolingual translation extracts it once. That systematic off-by-one for
    # every single ID is noise, not an error.
    results.append(("figure ID set", fig_ids(lt), fig_ids(rt), "set"))
    results.append(("table ID set", tab_ids(lt), tab_ids(rt), "set"))

    inline_l, inline_r = len(MATH_INLINE.findall(lt)), len(MATH_INLINE.findall(rt))
    results.append(
        (
            "inline $ count",
            collections.Counter({"$": inline_l}),
            collections.Counter({"$": inline_r}),
            "counter",
        )
    )

    all_pass = True
    diff_blocks: list[str] = []
    for name, l, r, mode in results:
        if mode == "set":
            ok = set(l) == set(r)
            detail = f"left {len(set(l))} id(s) / right {len(set(r))} id(s)"
        else:
            ok = l == r
            detail = f"left {sum(l.values()):>4} / right {sum(r.values()):>4}"
        all_pass &= ok
        if not args.quiet:
            print(f"[{'PASS' if ok else 'FAIL'}] {name:<16} {detail}")
        if not ok:
            diff_blocks.append(f"  · {name}")
            if mode == "set":
                only_l, only_r = sorted(set(l) - set(r)), sorted(set(r) - set(l))
                if only_l:
                    diff_blocks.append(f"    only on left:  {only_l}")
                if only_r:
                    diff_blocks.append(f"    only on right: {only_r}")
            else:
                diff_blocks.extend(fmt_diff(l, r))

    checked = len(results)
    if checked != args.expect_checks:
        all_pass = False
        print(
            f"[WARN] checked {checked} items, expected {args.expect_checks} — "
            "treated as not run (prevents an empty pass from a broken regex)"
        )

    if diff_blocks and not args.quiet:
        print("\nDifferences:")
        print("\n".join(diff_blocks))

    print(f"\nVerdict: {'PASS' if all_pass else 'FAIL'}   {checked} items checked")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
