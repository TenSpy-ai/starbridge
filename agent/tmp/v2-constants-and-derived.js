// ═══════════════════════════════════════════════════════
// CONSTANTS & DERIVED DATA from v2
// Port these verbatim into pipeline-explorer.html
// ═══════════════════════════════════════════════════════

// NOTE: PHASE_LABELS should use pipeline-explorer's version (has roman numerals)
// The production PHASE_LABELS:
const PHASE_LABELS = {
  source:   'I — Source',
  input:    'II — Input Validation',
  analyze:  'III — Target Analysis',
  discover: 'IV — Signal Discovery',
  select:   'V — Buyer Selection',
  generate: 'VI — Enrich & Generate',
  assemble: 'VII — Assemble & Validate'
};

// NODE_POSITIONS: absolute x,y for each step in the SVG diagram view
// These are IDENTICAL to v2 since step IDs match
const NODE_POSITIONS = {
  s0:  { x: 490, y: 60 },
  s1:  { x: 490, y: 320 },
  s2:  { x: 490, y: 580 },
  s3a: { x: 170, y: 850 },
  s3b: { x: 490, y: 850 },
  s3c: { x: 810, y: 850 },
  s4:  { x: 490, y: 1100 },
  s5:  { x: 490, y: 1280 },
  s6:  { x: 60,  y: 1540 },
  s7:  { x: 280, y: 1540 },
  s8:  { x: 500, y: 1540 },
  s11: { x: 720, y: 1540 },
  s12: { x: 940, y: 1540 },
  s9:  { x: 60,  y: 1710 },
  s10: { x: 280, y: 1710 },
  s13: { x: 490, y: 1970 },
  s14: { x: 490, y: 2150 },
  s15: { x: 490, y: 2330 },
  s16: { x: 490, y: 2510 },
};
const NODE_W = 160;

// SYSTEM_INPUTS: variables that come from outside the pipeline
const SYSTEM_INPUTS = { 'CURRENT_DATE': null };

// INPUT_SOURCES: maps each variable name → producing step ID
// Built from step.outputs so it can never go out of sync
const INPUT_SOURCES = (function() {
  var map = {};
  STEPS.forEach(function(s) {
    s.outputs.forEach(function(v) { map[v] = s.id; });
  });
  STEPS.forEach(function(s) {
    s.inputs.forEach(function(v) {
      if (v.indexOf('.') !== -1 && !map[v]) {
        var base = v.split('.')[0];
        if (map[base]) map[v] = map[base];
      }
    });
  });
  Object.keys(SYSTEM_INPUTS).forEach(function(k) { map[k] = SYSTEM_INPUTS[k]; });
  return map;
})();

// COMPUTED_EDGES: Map of "sourceId->targetId" → { source, target, variables[] }
const COMPUTED_EDGES = (function() {
  var edges = {};
  STEPS.forEach(function(targetStep) {
    targetStep.inputs.forEach(function(varName) {
      var base = varName.split('.')[0];
      var sourceId = INPUT_SOURCES[varName] || INPUT_SOURCES[base];
      if (!sourceId) return;
      var key = sourceId + '->' + targetStep.id;
      if (!edges[key]) edges[key] = { source: sourceId, target: targetStep.id, variables: [] };
      edges[key].variables.push(varName);
    });
  });
  return edges;
})();

// VALIDATION_LOOPS: bidirectional retry edges (pink dotted arrows)
const VALIDATION_LOOPS = [
  { from: 's14', to: 's11', label: 'If <b>SECTION_CTA</b> fails quality check → regenerate with stronger personalization (max 1 retry)' }
];

// PHASE_ROMAN: maps phase name → roman numeral (derived from STEPS order)
const PHASE_ROMAN = (function() {
  var romans = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
  var map = {}, count = 0;
  STEPS.forEach(function(s) {
    if (!map[s.phase]) map[s.phase] = romans[count++];
  });
  return map;
})();

// PARALLEL_GROUPS: maps step ID → group letter for consecutive parallel steps
const PARALLEL_GROUPS = (function() {
  var map = {}, code = 64, inGroup = false;
  STEPS.forEach(function(s) {
    if (s.parallel) {
      if (!inGroup) { code++; inGroup = true; }
      map[s.id] = String.fromCharCode(code);
    } else {
      inGroup = false;
    }
  });
  return map;
})();

// STEPS_MAP: index by id
const STEPS_MAP = {};
STEPS.forEach(s => { STEPS_MAP[s.id] = s; });
