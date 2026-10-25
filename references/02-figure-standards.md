# 02 · Figure Standards

Goal: figures that can go straight into a two-column Elsevier layout, and that reproduce **byte-identical** on every re-run.

## 1. Fix dimensions and type sizes before drawing anything

| Item | Suggested value | Rationale |
|---|---|---|
| Single-column width | 90 mm | Half of a two-column layout |
| Full-width | 190 mm | Two-column span; 190 mm @ 300 dpi ≈ 2244 px |
| Body type | 7 pt (minimum in-figure annotation 6.5 pt) | Lower bound of print legibility |
| Axis labels / titles | 8–9 pt | Distinguishable without shouting |
| Typeface | Arial / Helvetica | No substitution risk across platforms |
| Output | PNG (300 dpi) + PDF (vector) | Vector for production, raster for review |

**Do the page-geometry arithmetic.** If the text block of an A4 page with 2.5 cm margins is 159.8 mm, a figure designed at 190 mm is inserted at 84% scale, and a 6.5 pt annotation becomes an effective 5.5 pt. **This is the root cause of "it looked fine on screen but is unreadable in Word"** — not a resolution problem. Either redesign the width or widen the margins in the docx template.

When converting via pandoc, the reference docx must declare `pgSz`/`pgMar` explicitly; otherwise Word falls back to Letter and the whole document reflows.

## 2. One save point

**Every `fig.savefig` call must live in exactly one function** (e.g. `viz/_figio._savefig`). It is responsible for:

1. applying the style (including `bbox_inches='tight'`),
2. routing to a directory by output name (body / supplementary / archive / manual),
3. writing PNG (+PDF),
4. updating the manifest (dimensions, bbox mode, rect count, timestamp).

**Failure mode**: a direct `fig.savefig(...)` in business code bypasses the style entry point, so `bbox='tight'` is never set, the figure is saved at the declared canvas size without cropping, and the left edge is clipped. **Criterion**: read `bbox_mode` from the manifest — it should be `tight` for every figure. This is a field you can check, not a judgement about "empty-looking whitespace".

## 3. Every figure must call the style entry point itself

The style function holds `savefig.bbox='tight'`, the font family, spine weights, and tick directions. **It does not take effect merely because `rcParams` was set globally somewhere else** — matplotlib falls back to the non-tight branch on some code paths.

Rule: each figure object calls it once before saving. Never rely on the caller's context.

## 4. Colour by role, not by figure

Maintain a **role palette** instead of choosing colours per figure:

| Role | Source | Example |
|---|---|---|
| Zones / regions | Fixed tri-colour constant `ZONE3` | core / intermediate / peripheral |
| Magnitude (0 → high) | Sequential cmap `CMAP_SEQ_DEEP` | investment intensity, density |
| Signed values (− → +) | Diverging cmap `CMAP_DIV` | change, shift |
| Callout / anomaly | Single accent colour | highlighted cities, out-of-range points |
| Text colour | `ink_on(bg)` computed from background | black on light, white on dark |

**The criterion is the palette definition file, not the rendered image.** Retired producers often carry two stale palettes; re-mounting one silently overwrites colours — the figure "just looks a bit different", which is very hard to notice.

**Hard-coded white text on a light background** is the most frequent defect. Text colour recognises only two sources: the return value of `ink_on()`, or a sampled pixel.

## 5. Naming and routing

- Body figures are named **`FigNN_SemanticName`** (English, zero-padded, no CJK), and producers write the final name directly. Do not introduce a "Chinese name → Fig name" mapping table: a mapping table is a second source of truth.
- The root of the figure directory holds body figures only. Archive figures (`Archive_*`), retired outputs, and hand-made figures go into `legacy/` or `manual/`.
- All language versions **share the same figure files**. Per-language figure directories are a double-maintenance trap: once introduced, the sides inevitably drift.
- Keep the routing table (`FIG_ROUTING`) in config; `_savefig` selects the directory by name. **Without a routing table, output lands in the wrong directory**, and a shadowed final figure is among the hardest incidents to diagnose.

## 6. Map compliance (mandatory for Chinese study areas)

- Basemaps come only from the **Ministry of Natural Resources standard map service** or provincial standard maps. Boundaries are **modified zero times** — no cropping, no simplification, no redrawing.
- The approval number (审图号) must be stated, together with a note that the basemap is unmodified.
- Include a scale bar; the South China Sea inset must not cover the nine-dash line.
- In EPS standard maps the last character of `picId` (`a` ↔ `b`) selects different scale versions — do not mix them.
- **Coordinate-system trap**: the EPS standard map uses CorelDRAW page coordinates while business shapefiles are usually EPSG:3857. There is no common datum, so a forced fit leaves a residual of a few percent of province width. **Such a figure must not ship.** Producing it requires a full georeferencing step; until then, express the information another way. An absent panel is better than a panel that is "roughly right".

## 7. Criteria for figure changes

| Question | Valid evidence | Invalid evidence |
|---|---|---|
| Did content change? | Per-figure PNG pixel diff / manifest `kept_n` | PDF checksum (vector metadata changes) |
| Did layout change? | Panel count, panel order, whether the colourbar occupies a grid cell | "It looks cramped" |
| Is type size compliant? | pt values in the manifest | Eyeballing |
| Is the count right? | `N_FIG == declared` assertion | Counting files in a directory (subdirectories leak in) |

**Colourbars never sit inside a map and never occupy their own grid cell.** One quantity is presented in exactly one place (never repeated across body and supplementary).

## 8. Layout details learned the hard way

- For equal-aspect map panels, **never use `set_anchor('N')`**; use `set_position` with equal height and a common baseline, and apply it *before* label avoidance.
- `set_aspect('equal')` shrinks the axes box, so the declared box must be solved back from the data aspect ratio; otherwise you get padding or clipping.
- When raster basemaps overlay vectors, colour matching cannot unify them (different media). Switch to all-vector or all-raster.
- No-data areas use **solid grey**, never `facecolor='none'` (the basemap shows through and readers interpret it as a low value).
- Strict N×M grids (2×2 and similar) should not be padded with filler panels; leave a gap instead.
