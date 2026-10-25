#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gate.py — gate orchestrator (generic engine)

Design notes:
  · Generic engine, declared anchors. Project anchors (figure count, pixel width,
    dpi, line endings, truth pairs) live in TOML. Switching projects means
    switching the config file, never editing this script.
  · A misspelled config key must fail loudly. Unknown keys exit with code 2 and
    are never ignored — one misspelled `expect` silently disables one check,
    which is worse than having no gate.
  · The sub-scripts remain independently runnable; this file only orchestrates
    and aggregates, it does not duplicate their criteria.

Usage:
    python gate.py                            # looks for ./gate.toml
    python gate.py --config path/to/gate.toml
    python gate.py --only figures,text        # run a subset
    python gate.py --list                     # show what would run
    python gate.py --dry-run                  # print commands, run nothing

Exit codes: 0 = all passed; 1 = check failed; 2 = configuration error.
Requires Python 3.11+ (tomllib).
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

FIG_KEYS = {"name", "fig_dir", "expect", "width", "width_tol", "dpi", "code_dir", "require_pdf"}
TEXT_KEYS = {"name", "paths", "md_eol", "py_eol", "strict", "recursive"}
RECON_KEYS = {"name", "left", "right", "exceptions", "expect_checks"}
WAIVER_KEYS = {"target", "reason", "until", "note"}
TOP_KEYS = {"defaults", "recon", "figures", "text", "waiver"}
DEFAULTS_SUB = {"figures", "text"}

DEFAULT_FIG = {
    "fig_dir": "output/figures",
    "expect": 7,
    "width": 2244,
    "width_tol": 2,
    "dpi": 300,
    "require_pdf": False,
    "code_dir": None,
}
DEFAULT_TEXT = {"md_eol": "lf", "py_eol": "lf", "strict": False}


def load_config(path: str) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError:
        sys.exit(
            "[FAIL] Python 3.11+ required (tomllib). Current: %s" % sys.version.split()[0]
        )
    with open(path, "rb") as f:
        return tomllib.load(f)


def validate(cfg: dict) -> list[str]:
    """Return every configuration error; an empty list means valid.
    A misspelled key must never be silently ignored."""
    errs: list[str] = []
    for k in cfg:
        if k not in TOP_KEYS:
            errs.append(f"unknown top-level key [{k}], allowed: {sorted(TOP_KEYS)}")

    d = cfg.get("defaults", {})
    for k in d:
        if k not in DEFAULTS_SUB:
            errs.append(f"unknown [defaults.{k}], allowed: {sorted(DEFAULTS_SUB)}")
    for sub, allowed in (("figures", FIG_KEYS), ("text", TEXT_KEYS)):
        for k in d.get(sub, {}):
            if k not in allowed:
                errs.append(f"unknown key defaults.{sub}.{k}, allowed: {sorted(allowed)}")

    for i, blk in enumerate(cfg.get("figures", [])):
        for k in blk:
            if k not in FIG_KEYS:
                errs.append(f"figures[{i}] unknown key {k}, allowed: {sorted(FIG_KEYS)}")
    for i, blk in enumerate(cfg.get("text", [])):
        for k in blk:
            if k not in TEXT_KEYS:
                errs.append(f"text[{i}] unknown key {k}, allowed: {sorted(TEXT_KEYS)}")
        if "paths" not in blk:
            errs.append(f"text[{i}] missing paths")
    for i, blk in enumerate(cfg.get("recon", [])):
        for k in blk:
            if k not in RECON_KEYS:
                errs.append(f"recon[{i}] unknown key {k}, allowed: {sorted(RECON_KEYS)}")
        for need in ("left", "right"):
            if need not in blk:
                errs.append(f"recon[{i}] missing {need}")
    if not (cfg.get("recon") or cfg.get("figures") or cfg.get("text")):
        errs.append("no check block configured (recon/figures/text all empty)")

    for i, w in enumerate(cfg.get("waiver", [])):
        for k in w:
            if k not in WAIVER_KEYS:
                errs.append(f"waiver[{i}] unknown key {k}, allowed: {sorted(WAIVER_KEYS)}")
        if w.get("target") not in {"recon", "figures", "text"}:
            errs.append(f"waiver[{i}].target must be one of recon/figures/text")
        # A waiver must state a reason and an expiry: an open-ended waiver is a
        # permanently disabled check in disguise.
        if not w.get("reason"):
            errs.append(f"waiver[{i}] missing reason (why is this waived?)")
        if not w.get("until"):
            errs.append(
                f"waiver[{i}] missing until (an expiry date is required; expiry restores failure)"
            )
        else:
            try:
                datetime.date.fromisoformat(str(w["until"]))
            except ValueError:
                errs.append(f"waiver[{i}].until is not YYYY-MM-DD: {w['until']}")
    return errs


def build_jobs(cfg: dict, only: set[str]) -> list[tuple[str, str, str, list[str]]]:
    """Return [(group kind, label, script, argv)]. Every argument is derived from config."""
    jobs = []
    for blk in cfg.get("recon", []):
        if "recon" not in only:
            continue
        args = [blk["left"], blk["right"]]
        if blk.get("exceptions"):
            args += ["--exceptions", ",".join(blk["exceptions"])]
        if blk.get("expect_checks"):
            args += ["--expect-checks", str(blk["expect_checks"])]
        args += ["--quiet"]
        jobs.append(("recon", f"recon · {blk.get('name', 'reconcile')}", "recon_numeric.py", args))

    figdef = {**DEFAULT_FIG, **cfg.get("defaults", {}).get("figures", {})}
    for blk in cfg.get("figures", []):
        if "figures" not in only:
            continue
        c = {**figdef, **blk}
        args = [
            c["fig_dir"],
            "--expect", str(c["expect"]),
            "--width", str(c["width"]),
            "--width-tol", str(c["width_tol"]),
            "--dpi", str(c["dpi"]),
        ]
        if c.get("code_dir"):
            args += ["--code-dir", c["code_dir"]]
        if c.get("require_pdf"):
            args.append("--require-pdf")
        jobs.append(("figures", f"figures · {blk.get('name', 'figures')}", "check_figures.py", args))

    txtdef = {**DEFAULT_TEXT, **cfg.get("defaults", {}).get("text", {})}
    for blk in cfg.get("text", []):
        if "text" not in only:
            continue
        c = {**txtdef, **blk}
        args = list(c["paths"]) + ["--md-eol", c["md_eol"], "--py-eol", c["py_eol"]]
        if c.get("strict"):
            args.append("--strict")
        if c.get("recursive"):
            args.append("--recursive")
        jobs.append(("text", f"text · {blk.get('name', 'text')}", "check_text.py", args))
    return jobs


def find_waiver(cfg: dict, kind: str, today: datetime.date) -> tuple[dict | None, list[dict]]:
    """Return (active waiver, expired waivers). Expiry restores failure: a waiver
    is never permanent."""
    active: dict | None = None
    expired: list[dict] = []
    for w in cfg.get("waiver", []):
        if w.get("target") != kind:
            continue
        try:
            until = datetime.date.fromisoformat(str(w["until"]))
        except ValueError:
            continue
        if until >= today and active is None:
            active = w
        elif until < today:
            expired.append(w)
    return active, expired


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Gate orchestrator: generic engine + declarative config"
    )
    ap.add_argument("--config", default="gate.toml", help="config path (default: ./gate.toml)")
    ap.add_argument("--only", default="recon,figures,text", help="comma-separated groups to run")
    ap.add_argument("--list", action="store_true", help="list what would run, execute nothing")
    ap.add_argument("--dry-run", action="store_true", help="print commands, execute nothing")
    args = ap.parse_args()

    if not os.path.isfile(args.config):
        print(f"[FAIL] config not found: {args.config}")
        print("       Start from the template: cp assets/gate.example.toml ./gate.toml")
        return 2

    cfg = load_config(args.config)
    errs = validate(cfg)
    if errs:
        print("[FAIL] configuration error (no check was run):")
        for e in errs:
            print("  ·", e)
        return 2

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    jobs = build_jobs(cfg, only)
    if not jobs:
        print(f"[FAIL] --only {sorted(only)} matched no check block")
        return 2

    today = datetime.date.today()

    if args.list:
        for i, (kind, label, script, argv) in enumerate(jobs, 1):
            w, _exp = find_waiver(cfg, kind, today)
            tag = f"  [waived until {w['until']}]" if w else ""
            print(f"{i}. {label}  ->  {script} {' '.join(argv)}{tag}")
        print(f"\n{len(jobs)} job(s)")
        return 0

    print(f"Config: {args.config}   groups: {len(jobs)}\n" + "=" * 78)
    failed: list[tuple[str, int, list[str]]] = []
    waived: list[tuple[str, str]] = []
    passed = 0

    for kind, label, script, argv in jobs:
        cmd = [sys.executable, os.path.join(HERE, script), *argv]
        print(f"\n> {label}")
        print("  $ " + " ".join(cmd))
        if args.dry_run:
            continue
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        out = (proc.stdout or "").strip()
        if out:
            print("\n".join("  " + ln for ln in out.splitlines()))

        if proc.returncode == 0:
            passed += 1
            continue

        w, expired = find_waiver(cfg, kind, today)
        if w:
            waived.append((label, f"{w['reason']}; until {w['until']}"))
            # A waiver is not silence: the raw output is still printed in full,
            # and confirmation is requested that the failing item is still the
            # registered one.
            print(f"  ! waived — {w['reason']} (until {w['until']})")
            print(
                "    Raw output above. If the failing item is no longer the registered one, "
                "a new problem has appeared: remove the waiver."
            )
        else:
            tail = (proc.stderr or "").strip().splitlines()[-3:]
            failed.append((label, proc.returncode, tail))
            for e in expired:
                print(f"  ! waiver expired on {e['until']}; restored to failure: {e['reason']}")

    print("\n" + "=" * 78)
    if args.dry_run:
        print(f"DRY-RUN: {len(jobs)} job(s) pending, nothing executed")
        return 0
    if failed:
        print(
            f"VERDICT: FAIL   failed {len(failed)} / waived {len(waived)} / passed {passed} "
            f"(of {len(jobs)} group(s))"
        )
        for label, code, tail in failed:
            print(f"  · {label} (exit code {code})")
            for t in tail:
                print(f"      {t}")
        return 1
    if waived:
        print(
            f"VERDICT: PASS (with waivers)   waived {len(waived)} / passed {passed} "
            f"(of {len(jobs)} group(s))"
        )
        for label, why in waived:
            print(f"  ~ {label} — {why}")
        return 0
    print(f"VERDICT: PASS   all {len(jobs)} group(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
