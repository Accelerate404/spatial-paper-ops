# 04 · Reconciliation and Gates

What breaks before submission is rarely the content; it is the **counts**. This section is entirely about counting methods.

## 1. Multiset reconciliation (the core method)

For any two texts that should agree (language-of-record vs translation, body vs supplementary), extract the numbers into **multisets** (duplicates preserved) and compare:

```python
import re, collections
def tokens(text):
    # decimals only — integer noise is too high (see below)
    return collections.Counter(re.findall(r'\d+\.\d+', text))
```

| Item | Criterion |
|---|---|
| Numbers | Decimal-token multisets are identical |
| Figure IDs | **ID sets** are equal (counts are not compared) |
| Table IDs | **ID sets** are equal (counts are not compared) |
| References | Entry count equals the number of unique citation keys in the text (closure) |
| Equations | `$` count is even; `$$` block counts match |

### Why figure and table IDs are compared as sets, not counts

When the manuscript of record carries bilingual captions (`**Fig. 1 …** / **图1 …**`), each ID is extracted twice, while a monolingual translation extracts it once. The count therefore differs by one for **every** ID, systematically.

A difference that is a constant offset across all items is the signature of an **extraction artefact, not a content error**. What matters is whether the ID sets match: no missing numbers, no skipped numbers, no different ranges on the two sides.

General principle: **when the difference between two sides shows a uniform constant offset, suspect the extraction rule before suspecting the content.**

### Why integers are not evidence at all

Three sources of noise make integer reconciliation produce mostly false alarms:

1. **IDs**: `Fig. 1`, `Table 2` — these numbers are not data.
2. **Duplicated bilingual captions**: the year appears once per language.
3. **Spelled-out small numbers**: `nine cities`, `six-cell`, `three folds` — the digit token disappears on the English side.

Empirical result: zero differences among decimal tokens, dozens among integers, all of them noise. **Judge decimals only.**

Register genuine exceptions: unit conversions change magnitudes (`1449.8 万人` → `14.498 million`). Log such pairs in the glossary as the only permitted conversions; any other numeric change is an anomaly.

## 2. Word-count definitions

One manuscript has at least five word counts. Always state which one you mean:

| Definition | Meaning |
|---|---|
| Body prose only | Body text with headings, captions, tables, and references removed |
| Body + captions | The count most journals use |
| Full text with references | The number the submission system displays |
| Per-section counts | For locating which section overruns |
| CJK character count | Language-specific; comparable only within that language |

**Rules:**

- Always report the definition: `"8,344 words (body prose, excluding captions, tables, references)"`.
- Self-check against the journal limit using the **strictest** definition.
- When over the limit, first decide whether it is translation inflation or content volume. A 14,000-character Chinese manuscript becomes roughly 10,000–11,000 English words at normal ratios; **language tightening can recover only 10–15%**. If that is not enough, content must be cut — polishing cannot close the gap.
- Do not claim compliance before content compression has actually happened.

## 3. Reference closure

**Criterion**: entry count equals the number of unique citation keys appearing in the text. Check both directions:

- cited but not listed → dangling citation (severe)
- listed but not cited → redundant (acceptable, but confirm)

**Automation traps:**

- Matching on "surname + year" hides same-author-same-year pairs (`Liu & He 2026a` / `2026b`) — suffixes are mandatory.
- If the entry regex only accepts single parentheses `(YYYY)`, date-style entries (`2026-10`) drop out of reconciliation **without raising an error**. Silent omission is far more dangerous than a false positive, so the script must print "entries parsed" and you must compare it to the total.

**Reference counts may legitimately differ across language versions.** If the English submission version is trimmed independently to meet a length limit, record it in the collaboration notes: "manuscript of record keeps N entries; the English version keeps M". Closure then applies to one version only — otherwise the next reconciliation run reports a false alarm.

## 4. The four submission boundaries

Submission is not "zip the project folder". It is four distinct scopes:

| Scope | Contents | Note |
|---|---|---|
| ① Manuscript package | Main file (md/docx) + body figures | Body figures only; no archive figures |
| ② Supplementary package | Supplementary text + supplementary figures | Its own numbering scheme |
| ③ Availability package | `code/` (with `requirements.txt`) + `data/` (without backups) | Backs the Data-availability statement |
| ④ Never shared | `workspace/`, `discuss/`, `refs/`, derived caches | Contains supervisor drafts and internal records |

Consequence: `requirements.txt` lives **inside `code/` only**; no loose files at the project root.

## 5. Pre-submission checklist

**Machine-checkable (script it; exit code is the verdict)**

- [ ] Body figure count equals the declared count (no missing, no extras)
- [ ] Every figure meets width / dpi / minimum type size
- [ ] Line endings match `.gitattributes` for every file type
- [ ] No bold in body text (except table titles, figure titles, keywords)
- [ ] No colons in headings
- [ ] Tables are three-line (no vertical rules)
- [ ] `$` are paired; `$$` block counts match
- [ ] Decimal-token multiset matches the source of truth
- [ ] Reference closure holds in both directions
- [ ] Per-section word counts within limits (definition stated)
- [ ] Figure and table numbering is continuous — no gaps, no duplicates
- [ ] Abstract within the journal's word limit
- [ ] Each highlight within the character limit
- [ ] Keyword count within the limit, and keywords echo the body text

**Human-judgement (scripts cannot catch these)**

- [ ] Every number resolves to `sheet + row/column`
- [ ] Abstract contains no model jargon and no single-period values
- [ ] Introduction has no method-detail self-reference
- [ ] Terminology has zero conflicts with the glossary
- [ ] In-figure values, caption, and body text agree in all three places
- [ ] Every `as in §X` pointer in the supplementary material still resolves (changing a section number means grepping the supplementary file)
- [ ] Author details, funding number, e-mails, CRediT statement are final
- [ ] Cover letter numbers match the current manuscript (the most frequently forgotten file)

## 6. Design principles for gate scripts

1. **Exit code is the verdict.** `0` pass, non-zero fail. Do not make a human read a log to decide.
2. **Layer with `--strict`**: hard failures by default, softer channel checks only under `--strict`.
3. **Never skip silently.** A guard such as `if len(x) == 7:` makes the check **not run** when the length is unexpected, while still appearing to pass. Replace it with an assertion or an explicit error.
4. **Never wrap `raise` inside `except`.** That is self-defeating defence: it swallows the script's own "reconciliation mismatch" error and turns the check into decoration. To find this class of defect, search for `raise` inside `try` blocks.
5. **Print "items checked"** and compare it to the expected total, so a broken regex cannot produce an empty pass.
6. **Anchors in config, not in scripts.** Figure counts, pixel widths, dpi, line-ending conventions, and truth pairs live in `gate.toml`. Scripts only parse and decide. Switching projects switches the config; if you have to edit a script for each paper, the criteria have already forked.
7. **Reject unknown config keys.** A misspelled key silently disables one check, which is worse than having no gate. Configuration errors (exit code 2) must be strictly distinct from check failures (exit code 1): the former means the gate never ran.
8. **Waivers require an expiry date.** For a known issue you will not fix now, register `reason + until` rather than relaxing a threshold; expiry restores failure automatically. While a waiver is active, the raw output is still printed in full, so new problems cannot ride along on an old waiver.
