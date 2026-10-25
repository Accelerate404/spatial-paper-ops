#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_text.py — text-layer gate

Purpose: verify machine-decidable writing prohibitions and line-ending
consistency before submission. It targets the class of defect that scripts can
catch and eyes routinely miss.

Usage:
    python check_text.py manuscript.md
    python check_text.py manuscript.md --strict        # inline bold becomes hard failure
    python check_text.py manuscript.md --md-eol lf --py-eol crlf
    python check_text.py manuscript_dir --recursive

Exit codes: 0 = no hard failures; 1 = hard failure present (advisories do not count).
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)
CURLY = re.compile(r"[\u201c\u201d\u2018\u2019]")
BOLD = re.compile(r"\*\*(.+?)\*\*")
SENT_SPLIT = re.compile(r"[。！？；]")
CJK = re.compile(r"[\u4e00-\u9fff]")

# Bold whitelist: table titles, figure titles, keywords and field labels are
# structural elements and may be bold.
BOLD_OK = re.compile(r"^(表|图|Table|Figure|Keywords|关键词|Note|注[:：])")
# A whole-line bold run is a title/field line, i.e. structural. Only bold embedded
# inside a sentence counts as a violation.
WHOLE_BOLD = re.compile(r"^\s*\*\*.+\*\*\s*$")
# Caption line: starts with ** and is followed by a figure/table ID, optionally
# wrapped in brackets. Whole line exempt.
CAPTION = re.compile(r"^\s*\*\*[（(\[【]?\s*(图|表|Fig|Table|Tab)")
# Field-label line: **label**: … (common in declaration sections and captions).
FIELD_LABEL = re.compile(r"^\s*\*\*[^*]+\*\*\s*[：:]")
# The orphan rule applies to long paragraphs only; short blocks (headings, lists,
# captions) are out of scope.
MIN_PARA_CJK = 80
# Sentence length is measured after removing whitespace and punctuation. Counting
# CJK only would badly under-measure mixed Chinese/English sentences.
PUNCT = re.compile(r"[\s，。、；：！？（）()《》〈〉“”‘’\"'—…％%·,.;:!?/\\-]")


def detect_eol(raw: bytes) -> tuple[str, int, int]:
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and lf:
        return "mixed", crlf, lf
    return ("crlf" if crlf else "lf"), crlf, lf


def check_text_rules(text: str, strict: bool) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    lines = text.splitlines()

    # 1) no colons in headings
    for m in HEADING.finditer(text):
        title = m.group(2)
        if re.search(r"[：:]", title):
            fails.append(f"heading contains a colon: {title.strip()[:60]}")

    # 2) inline $ must be paired
    for i, ln in enumerate(lines, 1):
        stripped = ln.replace("$$", "")
        if stripped.count("$") % 2:
            fails.append(f"L{i} unpaired inline $: {ln.strip()[:60]}")

    # 3) curly quotes (straight ASCII quotes are required)
    for i, ln in enumerate(lines, 1):
        if CURLY.search(ln):
            fails.append(f"L{i} curly quote: {ln.strip()[:50]}")
            break

    # 4) bold in body text, outside the structural whitelist
    hits = []
    for i, ln in enumerate(lines, 1):
        if (
            HEADING.match(ln)
            or ln.lstrip().startswith("|")
            or WHOLE_BOLD.match(ln)
            or CAPTION.match(ln)
            or FIELD_LABEL.match(ln)
        ):
            continue
        for m in BOLD.finditer(ln):
            if not BOLD_OK.match(m.group(1).strip()):
                hits.append((i, m.group(1).strip()[:40]))
    if hits:
        msg = f"inline bold in body text: {len(hits)} occurrence(s), first at L{hits[0][0]}: {hits[0][1]}"
        (fails if strict else warns).append(msg)

    # 5) orphan sentences: non-initial sentence of <=15 CJK characters inside a
    #    long paragraph (CJK >= MIN_PARA_CJK)
    para, start = [], 1
    orphans = []
    for i, ln in enumerate(lines + [""], 1):
        if (
            ln.strip()
            and not HEADING.match(ln)
            and not CAPTION.match(ln)
            and not ln.lstrip().startswith(("|", "-", ">"))
        ):
            if not para:
                start = i
            para.append(ln.strip())
        else:
            if para:
                body = "".join(para)
                if len(CJK.findall(body)) >= MIN_PARA_CJK:
                    sents = [s for s in SENT_SPLIT.split(body) if s.strip()]
                    for s in sents[1:]:
                        n = len(PUNCT.sub("", s))
                        if 0 < n <= 15 and len(CJK.findall(s)) >= 2:
                            orphans.append((start, s.strip()[:30], n))
            para = []
    if orphans:
        warns.append(
            f"orphan-sentence candidates: {len(orphans)}, first at L{orphans[0][0]} "
            f"「{orphans[0][1]}」({orphans[0][2]} chars)"
        )

    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Text gate: line endings / heading colons / $ pairing / curly quotes / inline bold / orphans"
    )
    ap.add_argument("paths", nargs="+", help="files or directories")
    ap.add_argument("--recursive", action="store_true", help="recurse into directories")
    ap.add_argument("--md-eol", default="lf", choices=["lf", "crlf", "any"])
    ap.add_argument("--py-eol", default="lf", choices=["lf", "crlf", "any"])
    ap.add_argument("--strict", action="store_true", help="treat inline bold as a hard failure")
    args = ap.parse_args()

    files: list[str] = []
    for p in args.paths:
        if os.path.isdir(p):
            walker = os.walk(p) if args.recursive else [(p, [], os.listdir(p))]
            for root, _d, fns in walker:
                files += [os.path.join(root, f) for f in fns if f.endswith((".md", ".py"))]
        else:
            files.append(p)

    total_fail = total_warn = 0
    checked = 0
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        want = args.md_eol if ext == ".md" else args.py_eol if ext == ".py" else "any"
        with open(path, "rb") as f:
            raw = f.read()
        eol, crlf, lf = detect_eol(raw)
        fails, warns = [], []
        if want != "any" and eol != want:
            fails.append(f"line endings {eol} != declared {want} (CRLF {crlf} / bare LF {lf})")
        if ext == ".md":
            with open(path, encoding="utf-8", errors="replace") as f:
                f2, w2 = check_text_rules(f.read(), args.strict)
            fails += f2
            warns += w2
        checked += 1
        total_fail += len(fails)
        total_warn += len(warns)
        if fails or warns:
            print(f"\n{path}")
            for x in fails:
                print("  [FAIL]", x)
            for x in warns:
                print("  [WARN]", x)

    print(
        f"\nVerdict: {'PASS' if total_fail == 0 else 'FAIL'}   {checked} file(s) checked, "
        f"{total_fail} hard failure(s), {total_warn} advisory"
    )
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
