# Pipeline Explorer Rewrite — Hyper-Specific Implementation Spec

## Goal

Rewrite `agent/pipeline-explorer.html` to faithfully adopt **every** interactive feature from `roadmap/WIP/agent-pipeline/intel-report-workflow-v2.html`, while keeping all 19 production pipeline steps with their real `module`, `fn`, `timeout`, `service`, `scoring`, and `checks` data.

## Files

| File | Role | Size |
|---|---|---|
| `roadmap/WIP/agent-pipeline/intel-report-workflow-v2.html` | **Source of truth** for style/format/approach | 2402 lines, ~125KB |
| `agent/pipeline-explorer.html` | **Target** — rewrite this file | Currently 1187 lines, ~80KB |

## Reference Code (pre-extracted to `agent/tmp/`)

| File | What it contains |
|---|---|
| `tmp/v2-css-additions.css` | All CSS classes missing from pipeline-explorer (diagram nodes, zoom, floating panel, edge tooltip, validation loop, editable prompts) |
| `tmp/v2-html-additions.html` | HTML elements to add (3-view toggle, SVG container, zoom controls, floating detail, edge tooltip) |
| `tmp/v2-constants-and-derived.js` | `NODE_POSITIONS`, `VALIDATION_LOOPS`, `PHASE_ROMAN`, `PARALLEL_GROUPS`, `INPUT_SOURCES`, `COMPUTED_EDGES` |
| `tmp/v2-helpers-and-inputs.js` | `getTypes`, `primaryType`, `hasType`, `typeBadges`, `renderInputChips` (with edge hover), `renderFeedsInto` (with validation loops), `navToStep` |
| `tmp/v2-edge-system.js` | `showEdgeTooltip`, `hideEdgeTooltip`, `highlightEdge`, `unhighlightEdge`, `selectEdgeNode` |
| `tmp/v2-diagram-view.js` | `renderDiagram`, `selectDiagramNode`, `showDiagramDetail`, `closeDiagramDetail`, `zoomDiagram`, `applyZoom` |
| `tmp/v2-markdown-generation.js` | `generateStepMarkdown` (~130 lines per step), `generateAllMarkdown` (with TOC) |

---

## What to KEEP from current pipeline-explorer.html

### 1. All 19 STEPS with production data fields

Every step keeps its existing fields: `id`, `num`, `phase`, `name`, `type`, `meta`, `conditionalRun`, `inputs`, `outputs`, `tools`, `module`, `fn`, `timeout`, `service`, `detail`, `qualityRules`, `edgeCases`, `outputSchema`.

Special step-specific fields to preserve:
- **s4**: `scoring: { type_match:25, signal_count:20, recency:20, urgency:15, dollar:10, keyword:10 }`
- **s14**: `checks: [8 check strings]`

Step IDs (in STEPS array order): `s0, s1, s2, s3a, s3b, s3c, s4, s5, s8, s6, s9, s7, s10, s11, s12, s13, s14, s15, s16`

Step types (these differ from v2 — keep pipeline-explorer's types):
- `python`: s0, s4, s13
- `sqlite`: s1, s5, s16
- `llm`: s2, s9, s10, s14
- `api`: s3a, s3b, s3c, s6, s7, s15
- `template`: s8, s11, s12

### 2. PHASES array (7 phases with timing and branching info)

```javascript
const PHASES = [
  { num:'I',   name:'SOURCE',              steps:['s0'],                        timing:'<1ms',    exec:'sequential' },
  { num:'II',  name:'INPUT',               steps:['s1'],                        timing:'~50ms',   exec:'sequential' },
  { num:'III', name:'ANALYZE',             steps:['s2'],                        timing:'5-15s',   exec:'sequential (LLM)' },
  { num:'IV',  name:'DISCOVER',            steps:['s3a','s3b','s3c'],           timing:'3-8s',    exec:'3 parallel', parallel:true },
  { num:'V',   name:'SELECT',              steps:['s4','s5'],                   timing:'<100ms',  exec:'sequential' },
  { num:'VI',  name:'ENRICH & GENERATE',   steps:['s8','s6','s9','s7','s10','s11','s12'], timing:'15-60s', exec:'5 parallel branches',
    branches:[
      { label:'a', steps:['s8'] },
      { label:'b', steps:['s6','s9'] },
      { label:'c', steps:['s7','s10'] },
      { label:'d', steps:['s11'] },
      { label:'e', steps:['s12'] }
    ]
  },
  { num:'VII', name:'ASSEMBLE & VALIDATE', steps:['s13','s14','s15','s16'],     timing:'5-20s',   exec:'sequential' }
];
```

### 3. Canvas view (phase-band layout)

The existing `renderCanvas()` and `renderNode()` functions. This becomes the "Canvas" view in the 3-view system.

Canvas-specific CSS to preserve: `.canvas-wrap`, `.phase-band`, `.phase-band-hdr`, `.phase-num-lbl`, `.phase-name-lbl`, `.phase-timing-lbl`, `.step-row`, `.parallel-container`, `.fork-join`, `.fork-bar`, `.join-bar`, `.node`, `.node-type-*`, `.node-id`, `.node-name`, `.node-svc`, `.data-tag`, `.timeout-tag`, `.show-data`, `.show-timing`, `.branch-group`, `.branch-label`, `.seq-chain`, `.mini-arrow`, `.phase-arrow`, `.state-callout`

### 4. Detail panel — pipeline-specific sections

- **Implementation** section: shows `module`, `fn`, `timeout`, `service` as impl-tags
- **Scoring Weights** section (s4 only): shows scoring bars
- **Validation Checks** section (s14 only): shows numbered check list

### 5. Legend bar

Bottom bar with type dots, stats (4 LLM calls, ~12 API calls, 4 SQLite ops, target runtime: 30-60s).

---

## What to ADD from v2

### 6. CSS Variables — add to `:root`

```css
--pink: #f778ba;
--tool: #1a3a2a; --tool-border: #238636;
```

### 7. All CSS from `tmp/v2-css-additions.css`

Copy verbatim. This adds ~80 CSS rules for:
- Diagram nodes (`.dnode`, `.dnode-*`)
- Diagram grouping (`.dgroup-parallel`, `.dgroup-sequential`)
- Phase section backgrounds (`.dphase-section`)
- Zoom controls (`.zoom-controls`, `.zoom-btn`)
- Floating detail panel (`.diagram-detail-float`)
- Edge tooltip (`.edge-tooltip`)
- Edge highlighting (`.edge-highlighted`)
- Validation loop indicators (`.validation-loop-badge`, `.validation-loop-row`)
- Editable prompts (`.prompt-block .editable`, `.edit-hint`)
- Conditional run branch type (`.conditional-run-branch`)
- Extra badge types (`.badge-tool`, `.badge-validate`, `.badge-source`)
- **Pipeline-specific additions**: `.dnode-api`, `.dnode-python` (not in v2)

### 8. HTML Structure Changes (from `tmp/v2-html-additions.html`)

#### 8a. View toggle: 3 buttons instead of 2

```html
<button class="view-btn active" id="viewList" onclick="setView('list')">List</button>
<button class="view-btn" id="viewCanvas" onclick="setView('canvas')">Canvas</button>
<button class="view-btn" id="viewDiagram" onclick="setView('diagram')">Diagram</button>
```

CSS note: With 3 buttons, the middle button needs `margin-left: -1px` and no border-radius. Add:
```css
.view-btn + .view-btn { margin-left: -1px; }
.view-btn:not(:first-of-type):not(:last-of-type) { border-radius: 0; }
```

#### 8b. Diagram wrap: two sub-containers

```html
<div class="diagram-wrap" id="diagramWrap">
  <div class="canvas-wrap" id="canvasWrap"></div>
  <div class="diagram-canvas" id="diagramCanvas">
    <svg class="diagram-svg" id="diagramSvg"></svg>
    <div class="diagram-nodes" id="diagramNodes"></div>
  </div>
  <div class="diagram-detail-float" id="diagramDetail"></div>
</div>
```

Both `canvasWrap` and `diagramCanvas` start hidden. View switching shows/hides them.

#### 8c. New elements (add before closing `</div>` of `.app`)

- Zoom controls div
- Edge tooltip div
- Prompt bar (use v2's element IDs: `promptOutputBar`, `promptOutput`)
- Markdown modal (use v2's class names: `md-modal-overlay`, `md-modal`, etc.)

### 9. State object — extend

```javascript
const state = {
  selectedStep: null,
  focusPhase: 'all',
  editedPrompts: {},   // NEW: tracks contenteditable prompt edits per step ID
  view: 'list',        // CHANGED: 'list' | 'canvas' | 'diagram' (was 'list' | 'diagram')
  zoom: 1,             // NEW: diagram zoom level
  promptMinimized: false,
  highlightedEdge: null // NEW: currently highlighted edge key
};
```

### 10. Constants (from `tmp/v2-constants-and-derived.js`)

Port verbatim:
- `NODE_POSITIONS` (19 entries — same step IDs as v2)
- `NODE_W = 160`
- `SYSTEM_INPUTS`
- `INPUT_SOURCES` (IIFE — build from STEPS.outputs, handle dot-notation)
- `COMPUTED_EDGES` (IIFE — build from STEPS.inputs + INPUT_SOURCES)
- `VALIDATION_LOOPS` (1 entry: s14↔s11)
- `PHASE_ROMAN` (IIFE — derived from STEPS phase order)
- `PARALLEL_GROUPS` (IIFE — maps step IDs to group letters)

### 11. Helpers (from `tmp/v2-helpers-and-inputs.js`)

**Replace** pipeline-explorer's `typeBadge(type)` with v2's `typeBadges(s)` which supports hybrid types.

**Replace** pipeline-explorer's `renderInputChips()` with v2's version that adds:
- `data-edge` attributes on input groups
- `onmouseenter="highlightEdge()"` / `onmouseleave="unhighlightEdge()"` hover handlers
- Click-to-navigate via `navToStep()`

**Replace** pipeline-explorer's `renderFeedsInto()` with v2's version that adds:
- Validation loop rows (pink dotted border, loop badge)
- `data-edge` + hover handlers on outbound edges
- Click-to-navigate

**Add**: `getTypes(s)`, `primaryType(s)`, `hasType(s, t)` helpers for hybrid type support.

### 12. Edge interaction system (from `tmp/v2-edge-system.js`)

Port verbatim — 6 functions:
- `showEdgeTooltip(event, edgeKey)` — positions tooltip at cursor, shows source→target + variable chips
- `hideEdgeTooltip()` — hides tooltip
- `highlightEdge(edgeKey)` — highlights SVG path + arrow, adds `.edge-highlighted` to matching detail rows
- `unhighlightEdge()` — restores SVG styling, removes highlights
- `selectEdgeNode(edgeKey)` — clicks an edge → selects target step

### 13. Diagram view (from `tmp/v2-diagram-view.js`)

Port verbatim — 6 functions:
- `zoomDiagram(delta)` — zoom in/out or fit-to-view (delta=0)
- `applyZoom()` — applies CSS transform scale to diagram canvas
- `renderDiagram()` — the big one (~200 lines):
  1. Calculate canvas bounds from NODE_POSITIONS
  2. Draw phase section backgrounds (semi-transparent rectangles with labels)
  3. Draw nodes at absolute positions with type-colored borders
  4. Draw parallel group indicators (dashed borders for discovery + generate groups)
  5. Draw sequential sub-chain indicators (dotted orange borders for s6→s9, s7→s10)
  6. Draw SVG edge paths (cubic bezier with arrowhead polygons)
  7. Draw validation loop arrows (pink dotted, bidirectional)
  8. Add invisible hit-target paths for edge hover/click
- `selectDiagramNode(id)` — select + render + show floating detail + update prompt
- `showDiagramDetail(id)` — renders full detail content in floating panel (see section 15)
- `closeDiagramDetail()` — hides floating panel, deselects, re-renders

### 14. View switching — 3 modes

```javascript
function setView(v) {
  state.view = v;
  var app = document.getElementById('app');
  document.getElementById('viewList').classList.toggle('active', v === 'list');
  document.getElementById('viewCanvas').classList.toggle('active', v === 'canvas');
  document.getElementById('viewDiagram').classList.toggle('active', v === 'diagram');
  document.getElementById('zoomControls').style.display = v === 'diagram' ? 'flex' : 'none';

  if (v === 'list') {
    app.classList.remove('diagram-mode');
    closeDiagramDetail();
    renderPipeline();
    if (state.selectedStep) renderDetail(state.selectedStep);
  } else if (v === 'canvas') {
    app.classList.add('diagram-mode');
    document.getElementById('canvasWrap').style.display = 'block';
    document.getElementById('diagramCanvas').style.display = 'none';
    renderCanvas();
  } else { // diagram
    app.classList.add('diagram-mode');
    document.getElementById('canvasWrap').style.display = 'none';
    document.getElementById('diagramCanvas').style.display = 'block';
    renderDiagram();
  }
}
```

`navToStep(id)`:
- In `list` or `canvas` view → `selectStep(id)`
- In `diagram` view → `selectDiagramNode(id)`

`focusPhase(p)`:
- In `list` → `renderPipeline()`
- In `canvas` → `renderCanvas()`
- In `diagram` → `renderDiagram()`

### 15. Detail panel rendering — unified for both panels

Both `renderDetail(id)` (right panel in list view) and `showDiagramDetail(id)` (floating panel) render the **same** sections. Extract the section-building logic into a shared function or just duplicate (v2 duplicates).

Sections to render (in order):

1. **Header**: Step number + name + meta subtitle
2. **Conditional Run**: badge with type-specific color (always/stop/skip/branch)
3. **Implementation** (pipeline-specific): module, fn, timeout, service as impl-tags
4. **Tool Calls**: cyan chips for each tool
5. **Data In**: grouped by source step with edge hover attributes (from `renderInputChips`)
6. **Data Out**: schema rows with green chips (complex schemas get `<pre>` blocks)
7. **Feeds Into**: outbound edges + validation loops (from `renderFeedsInto`)
8. **Prompt/Detail blocks** (v2 hybrid-aware logic):
   - If hybrid type AND has detail → show detail with type-appropriate label/color
   - If hasType('llm') AND has prompt → show **editable** prompt (contenteditable div)
   - If NOT llm AND has prompt → show read-only prompt
   - If NOT hybrid AND has detail → show detail with type-appropriate label
9. **Scoring Weights** (s4 only): scoring bars
10. **Validation Checks** (s14 only): numbered check list
11. **Quality Rules**: red-bordered rule blocks
12. **Errors & Fallbacks**: edge case cards with severity badges

### 16. Editable prompts

For LLM steps with `prompt` field:

```javascript
function onPromptEdit(id) {
  var el = document.getElementById('promptEdit-' + id);
  if (el) { state.editedPrompts[id] = el.innerText; updatePrompt(); }
}
```

HTML in detail panel:
```html
<div class="edit-hint">Click to edit this prompt. Changes update the copy output below.</div>
<div class="prompt-block">
  <div class="editable" contenteditable="true" id="promptEdit-{id}" oninput="onPromptEdit('{id}')">
    {prompt text}
  </div>
</div>
```

Uses `state.editedPrompts[id] || s.prompt` when reading the prompt content.

**Which steps get prompts?** Add `prompt` field to: s2, s9, s10, s14 (all type `'llm'`). Use the prompts from v2 adapted for production context. s8, s11, s12 are templates (no LLM prompt). s6, s7 are API calls (no prompt).

### 17. Rich markdown generation (from `tmp/v2-markdown-generation.js`)

**Replace** pipeline-explorer's `buildAllMarkdown()` (~27 lines) and `updatePrompt()` with v2's versions:

- `generateStepMarkdown(s)` (~130 lines) — produces full per-step spec including:
  - Header with meta
  - Metadata (id, type, execution mode, module, fn, timeout, service)
  - Conditional run
  - Tool calls (backtick-wrapped)
  - Data In grouped by source
  - Data Out with schema
  - Feeds Into with validation loops
  - Prompt/detail sections (code-fenced)
  - Scoring weights (pipeline-specific)
  - Validation checks (pipeline-specific)
  - Quality rules
  - Edge cases

- `generateAllMarkdown()` — full pipeline spec with:
  - Title + date
  - Table of Contents (grouped by phase with roman numerals)
  - Phase headers
  - Full step specs separated by `---`

- `updatePrompt()` — displays `generateStepMarkdown(s)` in the prompt output bar

### 18. Prompt output bar + modal

Use v2's element IDs and class names:
- Bar: `promptOutputBar`, `promptOutput`, `minimizeBtn`, `copyBtn`
- Modal: `mdModalOverlay`, `mdModalContent`, `copyAllBtn`
- Functions: `togglePromptBar()`, `copyPrompt()`, `showAllMarkdown()`, `hideAllMarkdown()`, `copyAllMarkdown()`

### 19. Scroll wheel zoom

```javascript
document.getElementById('diagramWrap').addEventListener('wheel', function(e) {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault();
    var delta = e.deltaY < 0 ? 0.05 : -0.05;
    zoomDiagram(delta);
  }
}, { passive: false });
```

---

## Detailed renderDetail Changes

The current `renderDetail` needs these modifications:

### A. Replace `typeBadge(s.type)` with `typeBadges(s)`

Current (line 798): `typeBadge(s.type)` — assumes string type
New: `typeBadges(s)` — handles array types

### B. Add conditional-run 'branch' type

Current (line 873): only handles 'always', 'stop', 'skip'
New: add `crType === 'branch'` → label "Branches", CSS class `conditional-run-branch`

### C. Add editable prompt handling

Current detail/logic block (lines 930-935): always shows read-only `prompt-block`
New: use v2's hybrid-aware logic:

```javascript
var pt = primaryType(s);
var isHybrid = getTypes(s).length > 1;

if (isHybrid && s.detail) {
  // Show detail with type-appropriate label (Tool Logic, Validation Logic, DB Operations, etc.)
}
if (hasType(s, 'llm') && s.prompt) {
  // Show EDITABLE prompt with contenteditable div
}
if (!hasType(s, 'llm') && s.prompt) {
  // Show read-only prompt
}
if (!isHybrid && s.detail) {
  // Show detail with type-appropriate label
}
```

### D. Add edge hover attributes to input groups

Current `renderInputChips` has no `data-edge` or hover handlers.
New version (from `tmp/v2-helpers-and-inputs.js`) adds these.

### E. Add validation loops to Feeds Into

Current `renderFeedsInto` only shows outbound edges.
New version (from `tmp/v2-helpers-and-inputs.js`) shows validation loops first, then outbound edges.

---

## Step Data Additions

### Add `prompt` field to LLM steps

These 4 steps currently have `type: 'llm'` but no `prompt` field. Copy the corresponding prompts from v2, adjusting for production context:

| Step | v2 step | Prompt source (v2 line numbers) |
|---|---|---|
| s2 | s2 | Lines 426-457 — SLED market analyst prompt |
| s9 | s9 | Lines 823-900 — Featured buyer section prompt |
| s10 | s10 | Lines 925-959 — Secondary buyer cards prompt |
| s14 | s14 | Lines 1109-1122 — Validation prompt |

---

## File Structure (final)

```
<!DOCTYPE html>
<html lang="en">
<head>
<style>
  :root { /* merged variables including --pink, --tool, --tool-border */ }
  /* Current pipeline-explorer CSS (preserved) */
  /* v2 CSS additions (from tmp/v2-css-additions.css) */
  /* Pipeline-specific additions: .dnode-api, .dnode-python */
</style>
</head>
<body>
<div class="app" id="app">
  <!-- Header with 3-view toggle -->
  <!-- Left panel (pipeline list) -->
  <!-- Right panel (detail) -->
  <!-- Diagram wrap (canvas-wrap + diagram-canvas + floating detail) -->
  <!-- Legend bar (preserved) -->
  <!-- Prompt output bar (v2 IDs) -->
  <!-- Markdown modal (v2 classes) -->
  <!-- Zoom controls -->
  <!-- Edge tooltip -->
</div>

<script>
// STATE
const state = { selectedStep:null, focusPhase:'all', editedPrompts:{}, view:'list', zoom:1, promptMinimized:false, highlightedEdge:null };

// STEPS — 19 production steps (preserved with all fields)
const STEPS = [ ... ];

// PHASES — 7 phases (preserved)
const PHASES = [ ... ];

// CONSTANTS
const PHASE_LABELS = { ... };
const NODE_POSITIONS = { ... };        // from v2
const NODE_W = 160;
const SYSTEM_INPUTS = { ... };
const INPUT_SOURCES = (function(){})(); // from v2
const COMPUTED_EDGES = (function(){})();// from v2
const VALIDATION_LOOPS = [ ... ];      // from v2
const PHASE_ROMAN = (function(){})();  // from v2
const PARALLEL_GROUPS = (function(){})(); // from v2
const STEPS_MAP = {};                  // preserved

// HELPERS
// getTypes, primaryType, hasType, typeBadges (from v2)
// escHtml, getSourceLabel, phaseMatch, getOutboundEdges (preserved/adapted)
// renderInputChips (v2 version with edge hover)
// renderFeedsInto (v2 version with validation loops)
// navToStep (v2 version — routes by view)

// EDGE SYSTEM (from v2)
// showEdgeTooltip, hideEdgeTooltip, highlightEdge, unhighlightEdge, selectEdgeNode

// LIST VIEW
// renderPipeline (adapted: typeBadges instead of typeBadge)
// selectStep
// renderDetail (enhanced: hybrid types, editable prompts, edge hover, validation loops)

// CANVAS VIEW (preserved)
// renderCanvas, renderNode

// DIAGRAM VIEW (from v2)
// zoomDiagram, applyZoom, renderDiagram
// selectDiagramNode, showDiagramDetail, closeDiagramDetail

// PROMPT/MARKDOWN
// onPromptEdit (from v2)
// generateStepMarkdown (from v2 + pipeline-specific fields)
// updatePrompt (from v2)
// copyPrompt
// generateAllMarkdown (from v2 + pipeline-specific fields)
// showAllMarkdown, hideAllMarkdown, copyAllMarkdown
// togglePromptBar

// VIEW SWITCHING
// setView (3 modes: list/canvas/diagram)
// focusPhase (routes to correct renderer)

// SCROLL ZOOM (from v2)
// wheel event listener on diagramWrap

// INIT
renderPipeline();
updatePrompt();
</script>
</body>
</html>
```

---

## Verification Checklist

After implementation, verify ALL of these in a browser:

### List View
- [ ] Left panel shows 19 steps grouped by 7 phases with correct badges
- [ ] Phase focus presets (Discovery/Generation/Full Pipeline) dim/show steps
- [ ] Clicking a step shows full detail in right panel
- [ ] Detail panel shows: conditionalRun, implementation tags, tools, data in (grouped by source), data out (schema), feeds into (with validation loops for s11/s14), detail/prompt blocks, scoring (s4), checks (s14), quality rules, edge cases
- [ ] Input groups highlight on hover (edge highlighting works in list view)
- [ ] Clicking source link in Data In navigates to that step
- [ ] Clicking target in Feeds Into navigates to that step
- [ ] LLM steps (s2, s9, s10, s14) show editable prompts — editing updates the prompt bar
- [ ] Prompt bar shows `generateStepMarkdown()` output for selected step
- [ ] Copy Markdown copies to clipboard
- [ ] View All opens modal with full pipeline markdown (with TOC)

### Canvas View
- [ ] Shows phase bands with fork/join indicators
- [ ] Parallel phases show branches correctly (Phase IV: 3 parallel, Phase VI: 5 branches)
- [ ] Clicking a node selects it and shows floating detail panel
- [ ] State callout visible at top

### Diagram View
- [ ] SVG node graph renders all 19 nodes at correct positions
- [ ] Nodes colored by type (purple=llm, cyan=api, blue=template, orange=python, yellow=sqlite)
- [ ] Phase section backgrounds visible with labels
- [ ] Discovery parallel group indicator (dashed border around s3a/s3b/s3c)
- [ ] Generate parallel group indicator (dashed border around s6-s12)
- [ ] Sequential sub-chain indicators (dotted orange around s6→s9, s7→s10)
- [ ] SVG edges (cubic bezier paths) connect steps based on data flow
- [ ] Hovering an SVG edge shows tooltip (source→target + variable chips)
- [ ] Clicking an SVG edge selects the target step
- [ ] Validation loop arrow (pink dotted, bidirectional) between s14 and s11
- [ ] Phase focus presets dim non-matching phases + nodes
- [ ] Clicking a node shows floating detail panel
- [ ] Closing floating panel deselects node
- [ ] Zoom controls: +, −, Fit buttons work
- [ ] Ctrl+scroll wheel zooms in/out
- [ ] Zoom level displayed as percentage

### Cross-View
- [ ] Switching views preserves selected step
- [ ] Prompt bar updates correctly in all views
- [ ] Legend bar visible in all views

---

## Target Metrics

- **Lines**: ~2000-2200
- **File size**: ~115-125KB
- **All 19 production steps preserved** with real module/fn/timeout/service data
- **Every v2 feature present**: SVG diagram, edge interaction, zoom, floating detail, editable prompts, validation loops, rich markdown, hybrid type support
