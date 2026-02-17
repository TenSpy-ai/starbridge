// ═══════════════════════════════════════════════════════
// HELPERS + INPUT CHIPS + FEEDS INTO from v2
// These REPLACE the simpler versions in pipeline-explorer
// ═══════════════════════════════════════════════════════

// --- Type helpers (v2 supports hybrid types like ['validate', 'llm']) ---
function getTypes(s) { return Array.isArray(s.type) ? s.type : [s.type]; }
function primaryType(s) { return getTypes(s)[0]; }
function hasType(s, t) { return getTypes(s).includes(t); }
function typeBadges(s) {
  return getTypes(s).map(t => '<span class="step-badge badge-' + t + '">' + t + '</span>').join(' ');
}

// --- renderInputChips: with edge hover + highlight attributes ---
function renderInputChips(inputs, targetStepId) {
  if (!inputs.length) return '<span style="color:var(--text-dim);font-size:11px">None (entry point)</span>';
  const groups = {};
  inputs.forEach(function(name) {
    const base = name.split('.')[0];
    const src = INPUT_SOURCES[name] || INPUT_SOURCES[base] || null;
    if (!groups[src]) groups[src] = [];
    groups[src].push(name);
  });

  let html = '';
  const order = [null].concat(STEPS.map(function(s) { return s.id; }));
  const sortedKeys = Object.keys(groups).sort(function(a, b) {
    return order.indexOf(a === 'null' ? null : a) - order.indexOf(b === 'null' ? null : b);
  });

  sortedKeys.forEach(function(src) {
    const label = getSourceLabel(src);
    const stepId = (src && src !== 'null') ? src : null;
    const clickAttr = stepId ? ' onclick="navToStep(\'' + stepId + '\')"' : '';
    const linkClass = stepId ? ' src-link' : '';
    const edgeKey = stepId && targetStepId ? stepId + '->' + targetStepId : '';
    const hoverAttr = edgeKey ? ' onmouseenter="highlightEdge(\'' + edgeKey + '\')" onmouseleave="unhighlightEdge()"' : '';

    html += '<div class="input-group" data-edge="' + edgeKey + '"' + hoverAttr + '>';
    html += '<div class="input-group-label">from <span class="' + linkClass + '"' + clickAttr + '>' + label + '</span></div>';
    html += '<div class="data-flow">';
    groups[src].forEach(function(n) { html += '<span class="data-chip chip-in">' + n + '</span>'; });
    html += '</div></div>';
  });
  return html;
}

// --- renderFeedsInto: with validation loops + edge hover ---
function renderFeedsInto(stepId) {
  var outbound = getOutboundEdges(stepId);
  var loops = VALIDATION_LOOPS.filter(function(l) { return l.from === stepId || l.to === stepId; });
  if (!outbound.length && !loops.length) return '';
  var html = '<div class="detail-section"><h3><span class="dot" style="background:var(--orange)"></span>Feeds Into</h3>';
  // Validation loops first
  loops.forEach(function(loop) {
    var otherId = loop.from === stepId ? loop.to : loop.from;
    var other = STEPS.find(function(x) { return x.id === otherId; });
    if (!other) return;
    var loopKey = loop.from + '<->' + loop.to;
    var clickAttr = ' onclick="navToStep(\'' + otherId + '\')"';
    html += '<div class="input-group validation-loop-row" data-edge="' + loopKey + '" onmouseenter="highlightEdge(\'' + loopKey + '\')" onmouseleave="unhighlightEdge()">';
    html += '<div class="input-group-label"><span class="validation-loop-badge">\u21c4 validation loop</span> with <span class="src-link"' + clickAttr + '>Step ' + other.num + ': ' + other.name + '</span></div>';
    html += '<div style="color:var(--text-dim);font-size:11px;margin-top:2px">' + loop.label + '</div>';
    html += '</div>';
  });
  // Normal outbound edges
  outbound.forEach(function(edge) {
    var target = STEPS.find(function(x) { return x.id === edge.target; });
    if (!target) return;
    var clickAttr = ' onclick="navToStep(\'' + edge.target + '\')"';
    html += '<div class="input-group" data-edge="' + edge.source + '->' + edge.target + '" onmouseenter="highlightEdge(\'' + edge.source + '->' + edge.target + '\')" onmouseleave="unhighlightEdge()">';
    html += '<div class="input-group-label">to <span class="src-link"' + clickAttr + '>Step ' + target.num + ': ' + target.name + '</span></div>';
    if (edge.variables.length) {
      html += '<div class="data-flow">';
      edge.variables.forEach(function(v) { html += '<span class="data-chip chip-feeds">' + v + '</span>'; });
      html += '</div>';
    }
    html += '</div>';
  });
  html += '</div>';
  return html;
}

// --- navToStep: routes to correct view's selection method ---
function navToStep(id) {
  if (state.view === 'diagram') { selectDiagramNode(id); }
  else { selectStep(id); }
}
