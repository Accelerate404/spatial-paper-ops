# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-10-25

Initial public release.

### Added

- `SKILL.md`: six-layer workflow (data / experiment / figures / text / reconciliation / gate), layered diagnosis order, twelve hard criteria, delivery conventions.
- `references/01-data-and-reproducibility.md`: single truth channel, three checks on definition changes, cache invalidation, assertion gates, reproducibility triad.
- `references/02-figure-standards.md`: dimensions and type sizes, single save point, role-based colour, figure routing, map compliance, pixel-level comparison.
- `references/03-writing-discipline.md`: three prohibitions, three line rules, orphan-sentence threshold, section transitions, terminology locking, Elsevier layout rules.
- `references/04-reconciliation-and-gates.md`: multiset reconciliation, five word-count definitions, reference closure, submission package boundaries, gate design principles.
- `references/05-pitfall-ledger.md`: 31 incidents, each with symptom, root cause, and criterion.
- `assets/recon_numeric.py`: decimal-token multiset reconciliation, figure/table ID **set** comparison, math-delimiter pairing, registered unit-conversion exceptions.
- `assets/check_figures.py`: figure-count guard, naming conformance, pixel width, dpi (parses PNG `IHDR`/`pHYs` directly), 0-byte write-residue detection, duplicate-producer detection.
- `assets/check_text.py`: line endings, heading colons, `$` pairing, curly quotes, inline bold (semantic whitelist), orphan-sentence candidates.
- `assets/safe_replace.py`: replacement-count assertions, bidirectional verification, line-ending preservation, automatic snapshots, dry-run mode.
- `assets/gate.py`: declarative orchestrator with three-way exit codes, unknown-key rejection, and expiring waivers.
- `tests/run_demo.py`: synthetic end-to-end demonstration.
- `tests/test_gates.py`: self-tests covering exit-code semantics and waiver expiry.

### Design notes

- Figure and table IDs are compared as **sets, not counts**: manuscripts whose captions carry bilingual titles count each ID twice, producing a systematic off-by-one that is noise, not error.
- Waivers require both `reason` and `until`; expiry restores failure automatically. Relaxing a threshold to obtain a green light is explicitly rejected as a design pattern.
- Configuration errors exit with code `2` and are kept strictly distinct from check failures (`1`), because a misconfigured gate has not actually run.

[Unreleased]: https://github.com/Accelerate404/spatial-paper-ops/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Accelerate404/spatial-paper-ops/releases/tag/v0.1.0
