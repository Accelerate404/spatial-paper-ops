# 01 · Data and Reproducibility

## 1. The single truth channel

A paper project permits exactly one numeric channel:

```
experiment code (models/exp_*) → excel_io.save_*() → data/audit.xlsx → figures (read-only) and body text (read-only)
```

**Forbidden patterns — each of these has caused a real defect:**

- ❌ Copying numbers from console output, logs, or a notebook cell into the manuscript.
- ❌ Filling gaps inside a plotting function with `np.random`, `np.linspace`, or a default fallback. A plot function accepts data; it never invents it.
- ❌ Hand-editing a cell in the workbook. Change the generating code and re-run the write step.
- ❌ Any number in the manuscript that cannot be resolved to `sheet + row/column`.

**Writing new data**: route it through the single writer (`save_supplement_sheets` or equivalent). The day a second writer appears is the day definitions start to fork.

## 2. How to organise the audit workbook

- **Identical sheet names with different definitions must be labelled side by side.** Historical definitions cannot be deleted (old drafts would become irreproducible), but the data README must state explicitly that two definitions coexist.
- One sentence per sheet in `data/README.md`: its definition and its producer (which function, which batch).
- Sheets whose definition has been superseded get a `_deprecated_` prefix or a `legacy` marker — **but do not delete them**.
- A key-summary sheet holds only the headline values the body text cites; detail lives elsewhere.

## 3. Three checks on any definition change (the most frequent source of incidents)

You changed the definition of a resilience index, the zonal classification, or the base year. **Editing the code is not enough.**

| Check | How | False-negative trap |
|---|---|---|
| ① Residual scan | Grep the whole manuscript for the old value; scan ranges separately | Ranges often omit `%` or units, so grepping `66.1` misses `66.1–70` |
| ② Snapshot diff | Line-by-line diff against a frozen snapshot (read it, do not just compare checksums) | A checksum comparison misses "formatting changed, values fine" and "values wrong, byte count identical" |
| ③ Generator literals | Read the generating function's source for hard-coded constants | Annotations printed on a figure are often f-strings in the source, not values in the workbook |

A definition change is closed only after all three. Skipping ③ produces the classic symptom: the workbook is fully correct and the numbers printed on the figure are still the old ones.

## 4. Caches and invalidation

- Expensive recomputation produces cached artefacts (`output/derived/*.pkl`). There must be **exactly one loader** (e.g. `get_main_chain()`), and it must carry a data-version stamp.
- Three symptoms of a stale cache: figures disagree with the workbook; the multi-period panel has the wrong number of periods; the rolling warm-start origin does not match the previous period's end state.
- Criterion: the manifest records the source workbook's mtime or size hash. A cache older than the workbook must be recomputed.
- **Deleting a cache is the last resort**: confirm the recomputation cost first (a long run at N=1000 × G=500 can be hours).

## 5. Register the sign convention

The same ablation effect may be written with opposite subtractions in two tables. **Put the convention in the table header when the table is created:**

- Detail table: `full constraints − without X` (negative = the mechanism lowers that metric)
- Summary table: `without X − full` (+19.2 pp)

Confirm the convention from the header before cross-referencing, never from memory of an ID. Incidents have occurred where an ID was cited correctly but now referred to a different table — **IDs get reused, headers do not**.

## 6. The reproducibility triad

1. **Fixed seeds.** All random sources (NSGA-II initial population, crossover and mutation, multi-start optimisation) derive from a single seed declared in config. Do not scatter `seed=42` through functions.
2. **Parallelism must not change numbers.** Block-level parallelism is only safe when tasks share no mutable state. Verify with `np.allclose` or checksum equality between serial and parallel runs — not with "it looks the same".
3. **Assertion gates.** The main chain ends with hard assertions on 3–8 headline results (knee point, key shares, centroid shift).

```python
# Where expected values come from: the audit workbook, never hard-coded in the script
EXPECT = read_anchors_from_excel()
assert abs(knee_f1 - EXPECT["knee_f1"]) < 1e-4
```

Hard-coding an expected value means the code and the manuscript can be wrong together and the assertion still passes. **An assertion that is not independent is not an assertion.**

## 7. Suggested verification entry points

| Entry point | Purpose | Typical assertion count |
|---|---|---|
| `cli/run_main.py` | Main chain producing published results | 3–8 anchors |
| `cli/run_all.py` | Full baseline pipeline | 20–30 |
| `cli/risk.py` | Index provenance (source-level decomposition) | 5–10 |
| `cli/check_paper_figs.py` | Figure/text, line endings, syntax | exit code |
| `cli/check_code_health.py` | Duplicate figure writers, save channels | exit code |
| `cli/measure_sections.py` | Per-section word counts | report table |

**Any change to `code/**/*.py` requires re-running the gates.** This is the only mechanism that catches "a figure broke during a refactor".

## 8. Distrust sub-agent output

Sub-agents fabricate references, smuggle in unverified numbers, and present inference as fact. Therefore:

- Any number from a sub-agent → multiset reconciliation before it enters the manuscript.
- Any reference from a sub-agent → verify against the source (at minimum title, year, journal).
- Any "already modified" claim → grep the actual file contents in the main channel.
