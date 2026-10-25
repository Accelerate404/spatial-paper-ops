# 03 · Writing Discipline

Target: Elsevier / SSCI geography and planning journals. Every rule below was settled after a rejection risk or a self-rejection — these are not style preferences.

## 1. The three prohibitions (highest constraint during revision)

1. **Claims never exceed evidence.** Method names, mechanism assertions, causal wording — all stay within what the design supports. Correlation is not causation; a single-period result does not upgrade to a dynamic conclusion; one city is not a regional law.
2. **A paragraph must be globally coherent, not merely locally.** Before changing a sentence, check its role in the paragraph, the section, the argument. Locally fluent and globally broken is the most insidious rejection reason.
3. **Hedging must not repeatedly undercut the core conclusion.** One "may" is rigour; three "may"s say the author does not believe it. Restrictive language appears only where a boundary genuinely exists.

## 2. The three line rules

**① Colons are permitted in three cases only**; rewrite everything else:

- introducing an equation (`the constraint is given by:`)
- enumerating (`three categories: first…`)
- caption field labels (`Note:`)

**No colons in headings.** `Spatial policy pathways and mechanism ablation` ✅ / `Spatial policy pathways: mechanisms and ablation` ❌

**② No "downward-pointing" structural statements.** `This section will…`, `The following discusses…` — delete. Two functional pointers survive: `see Supplementary Material` and `restrictive interpretation in §X`.

**③ No sentence-final defensive disclaimers.** `…but this does not necessarily mean…` undercuts the sentence itself. **The substantive limit must survive** — merge it into the main clause rather than deleting it.

## 3. The orphan-sentence threshold

**Inside a paragraph, any non-initial sentence of ≤15 CJK characters is an orphan and is prohibited.** There is exactly one remedy: merge it into the preceding sentence with a comma or semicolon.

When splitting a long sentence, re-check the threshold in the same batch. Techniques the user has explicitly rejected (such as "vary the rhythm by splitting long sentences") must not be used, even if a general-purpose polishing tool suggests them.

## 4. Section transitions only at first-level headings

- First-level sections may open with a transition or roadmap.
- **Under a parent heading in the methods chapter, there must be no "overview + roadmap" preamble.** Sub-sections hang directly off the parent.
- **The first sentence under a sub-heading is unrestricted** and may start normally.

Rationale: the methods chapter is the easiest place to write "this section has three parts…" — low information density, high word count.

## 5. Two kinds of self-reference in the introduction

| Permitted | Prohibited |
|---|---|
| Positioning: stating the problem, defining the objectives, declaring the solution protocol (one sentence each) | Method-detail: `this paper adopts…`, `this is the methodological basis for…`, `rolling warm-start` |

Mentioning implementation details such as warm-starting in the introduction pre-empts the results chapter and turns the introduction away from the problem.

## 6. Terminology locking

**Core terminology must not be chosen by the model.** Maintain a glossary with explicit locks:

```
| Term (zh) | Term (en) | Forbidden renderings | Note |
|---|---|---|---|
| 圈层战略 | three-tier zonation | zonation strategy / core–peripheral zonation | the latter is a binary term; conflicts with a three-tier table |
| 有效空间功能性指数 (EFI) | effective spatial functional index | carrying capacity | legacy name retained only at the identifier layer |
```

Supporting rules:

- **Three confusable layers must never be merged**: the policy-text layer (regional planning), the policy-semantic layer (spatial functional positioning), and the encoding layer (zonation strategy). Each has its own definition site and scope of use.
- **Separate the identifier layer from the narrative layer.** Sheet names, function names, and file names may keep legacy terms; narrative prose must use the current term. Revise the narrative layer only.
- **Define each concept once**; reference it elsewhere.
- **Keywords must echo the body text.** A keyword with no corresponding usage, or a high-frequency body term absent from the keywords, is a signal to fix one or the other.
- **Inversion traps**: `boundary constraint` vs `constraint boundary` are different things; the one that counts zero occurrences across the manuscript is the one you want.

## 7. First occurrence of a concept

- First occurrence: full name plus abbreviation; abbreviation only thereafter.
- **Never introduce an unexplained acronym or software name** (CLUE-S, FLUS, PLUS and similar). Reader's perspective: they are not in your sub-field.
- After defining an abbreviation, treat the caption, the table note, and the abstract each as an independent "first occurrence" — the abstract may be read alone.

## 8. Elsevier / LUP layout rules

| Item | Rule |
|---|---|
| Bold in body text | ❌ Prohibited. Bold only for table titles, figure titles, keywords, field labels |
| Colons in headings | ❌ Prohibited |
| Tables | Three-line: top rule, header rule, bottom rule; no vertical rules |
| Quotation marks | ASCII straight quotes (`"` `'`), not curly |
| Em dashes | No sentence-level `——` |
| Abstract | For non-specialists: no model jargon, one proposition per sentence |
| Body | For specialists: methodological and parameter detail belongs here |
| References | `et al.`, never the localised equivalent |
| Subscripts | pandoc recognises `~x~` only; a bare subscript outside `$…$` (`β_i`) prints literally |

Three-line table completion: pandoc frequently drops the header rule when converting markdown to docx; a post-processing script must add it back.

## 9. Revision mechanics

1. **Read the target paragraph before editing.** Editing from memory edits the wrong place.
2. **Whole-paragraph replacement plus bidirectional assertion**: immediately assert the new string exists and the old string is zero where it should be.
3. **Two edits in the same file can overwrite each other** when their `old_string` ranges overlap. Change one place at a time and verify immediately.
4. **When the replacement contains the original, the criterion is count equality** (`count(OLD) == count(NEW)`), not the old string reaching zero.
5. **Snapshot before large edits**: copy into a backup directory with a dated filename.
6. **Any numeric change requires re-running the baseline assertions in the same batch.**

## 10. De-AI-flavouring

Use a dedicated tool, and **disable the rules that collide with journal requirements** first:

- ❌ let it convert quote marks to curly (collides with the straight-quote rule)
- ❌ let it "vary rhythm by splitting long sentences" (collides with the orphan threshold)
- ❌ let it delete hedging (collides with "substantive limits must survive")
- ❌ let it emit meta-output such as AI-likelihood scores or "personality and soul" commentary

Default to a **problem list only**, not direct rewriting. If rewriting is requested, limit the scope and re-run the gates. Do not touch enumeration patterns that have already been approved.
