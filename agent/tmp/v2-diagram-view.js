// ═══════════════════════════════════════════════════════
// DIAGRAM VIEW — SVG node graph from v2
// Port this verbatim into pipeline-explorer.html
// ═══════════════════════════════════════════════════════

function zoomDiagram(delta) {
  if (delta === 0) {
    var wrap = document.getElementById('diagramWrap');
    var viewH = wrap.clientHeight;
    var viewW = wrap.clientWidth;
    var maxX = 0, maxY = 0;
    Object.values(NODE_POSITIONS).forEach(function(p) {
      if (p.x + NODE_W + 60 > maxX) maxX = p.x + NODE_W + 60;
      if (p.y + 120 > maxY) maxY = p.y + 120;
    });
    state.zoom = Math.min(viewW / (maxX + 40), viewH / (maxY + 40), 1.5);
    state.zoom = Math.round(state.zoom * 20) / 20;
  } else {
    state.zoom = Math.max(0.2, Math.min(2.0, state.zoom + delta));
    state.zoom = Math.round(state.zoom * 20) / 20;
  }
  applyZoom();
}

function applyZoom() {
  var canvas = document.getElementById('diagramCanvas');
  canvas.style.transform = 'scale(' + state.zoom + ')';
  document.getElementById('zoomLevel').textContent = Math.round(state.zoom * 100) + '%';
}

function renderDiagram() {
  var nodesEl = document.getElementById('diagramNodes');
  var svgEl = document.getElementById('diagramSvg');
  var canvas = document.getElementById('diagramCanvas');

  // Calculate canvas bounds
  var maxX = 0, maxY = 0;
  Object.values(NODE_POSITIONS).forEach(function(p) {
    if (p.x + NODE_W + 60 > maxX) maxX = p.x + NODE_W + 60;
    if (p.y + 120 > maxY) maxY = p.y + 120;
  });
  var canvasW = maxX + 80;
  var canvasH = maxY + 80;

  canvas.style.width = canvasW + 'px';
  canvas.style.height = canvasH + 'px';
  nodesEl.style.width = canvasW + 'px';
  nodesEl.style.height = canvasH + 'px';
  svgEl.setAttribute('width', canvasW);
  svgEl.setAttribute('height', canvasH);
  svgEl.style.width = canvasW + 'px';
  svgEl.style.height = canvasH + 'px';

  applyZoom();

  // Phase section backgrounds (rendered first → paint behind nodes and groups)
  var nodesHtml = '';
  var phaseGroups = {};
  STEPS.forEach(function(s) {
    var pos = NODE_POSITIONS[s.id];
    if (!pos) return;
    if (!phaseGroups[s.phase]) phaseGroups[s.phase] = { label: PHASE_LABELS[s.phase], nodes: [] };
    phaseGroups[s.phase].nodes.push(pos);
  });
  var NODE_H = 85;
  var LABEL_H = 16, MIN_W = 260;
  var PHASE_PADS = { generate: { x: 60, y: 56 }, discover: { x: 56, y: 50 } };
  var DEFAULT_PAD = { x: 28, y: 20 };
  Object.keys(phaseGroups).forEach(function(phase) {
    var g = phaseGroups[phase];
    var pad = PHASE_PADS[phase] || DEFAULT_PAD;
    var padX = pad.x, padY = pad.y;
    var minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
    g.nodes.forEach(function(p) {
      if (p.x < minX) minX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.x + NODE_W > maxX) maxX = p.x + NODE_W;
      if (p.y + NODE_H > maxY) maxY = p.y + NODE_H;
    });
    var dimmed = state.focusPhase !== 'all' && !phaseMatch(phase, state.focusPhase);
    var contentW = maxX - minX + padX * 2;
    var centerX = (minX + maxX) / 2;
    var sW = Math.max(contentW, MIN_W);
    var sL = centerX - sW / 2;
    var sT = minY - padY - LABEL_H;
    var sH = maxY - minY + padY * 2 + LABEL_H * 2;
    nodesHtml += '<div class="dphase-section' + (dimmed ? ' dphase-dimmed' : '') + '" style="left:' + sL + 'px;top:' + sT + 'px;width:' + sW + 'px;height:' + sH + 'px">';
    nodesHtml += '<span class="dphase-section-label">' + g.label + '</span></div>';
  });

  // Draw nodes
  STEPS.forEach(function(s) {
    var pos = NODE_POSITIONS[s.id];
    if (!pos) return;
    var dimmed = state.focusPhase !== 'all' && !phaseMatch(s.phase, state.focusPhase);
    var selected = state.selectedStep === s.id;
    nodesHtml += '<div class="dnode dnode-' + primaryType(s) + ' ' + (selected ? 'dnode-selected' : '') + ' ' + (dimmed ? 'dnode-dimmed' : '') + '"';
    nodesHtml += ' style="left:' + pos.x + 'px;top:' + pos.y + 'px;width:' + NODE_W + 'px"';
    nodesHtml += ' onclick="selectDiagramNode(\'' + s.id + '\')" id="dnode-' + s.id + '">';
    nodesHtml += '<div class="dnode-num">' + typeBadges(s) + ' ' + s.num + '</div>';
    nodesHtml += '<div class="dnode-name">' + s.name + '</div>';
    nodesHtml += '<div class="dnode-meta">' + (s.meta.length > 50 ? s.meta.slice(0, 47) + '...' : s.meta) + '</div>';
    nodesHtml += '</div>';
  });

  // Parallel group: Discovery (s3a, s3b, s3c)
  var p1L = NODE_POSITIONS.s3a.x - 16, p1T = NODE_POSITIONS.s3a.y - 24;
  var p1R = NODE_POSITIONS.s3c.x + NODE_W + 16, p1B = NODE_POSITIONS.s3a.y + 110;
  nodesHtml += '<div class="dgroup-parallel" style="left:' + p1L + 'px;top:' + p1T + 'px;width:' + (p1R-p1L) + 'px;height:' + (p1B-p1T) + 'px">';
  nodesHtml += '<span class="dgroup-parallel-label">PARALLEL — 3 discovery searches</span></div>';

  // Parallel group: Intel + Generation (s6, s7, s8, s9, s10, s11, s12)
  var p2L = NODE_POSITIONS.s6.x - 40, p2T = NODE_POSITIONS.s6.y - 48;
  var p2R = NODE_POSITIONS.s12.x + NODE_W + 40, p2B = NODE_POSITIONS.s9.y + 132;
  nodesHtml += '<div class="dgroup-parallel" style="left:' + p2L + 'px;top:' + p2T + 'px;width:' + (p2R-p2L) + 'px;height:' + (p2B-p2T) + 'px">';
  nodesHtml += '<span class="dgroup-parallel-label">PARALLEL — 5 branches: 2 intel chains + 3 generators</span></div>';

  // Sequential sub-chain: s6 -> s9
  var sq1L = NODE_POSITIONS.s6.x - 20, sq1T = NODE_POSITIONS.s6.y - 24;
  var sq1R = NODE_POSITIONS.s6.x + NODE_W + 20, sq1B = NODE_POSITIONS.s9.y + 112;
  nodesHtml += '<div class="dgroup-sequential" style="left:' + sq1L + 'px;top:' + sq1T + 'px;width:' + (sq1R-sq1L) + 'px;height:' + (sq1B-sq1T) + 'px">';
  nodesHtml += '<span class="dgroup-sequential-label">SEQUENTIAL</span></div>';

  // Sequential sub-chain: s7 -> s10
  var sq2L = NODE_POSITIONS.s7.x - 20, sq2T = NODE_POSITIONS.s7.y - 24;
  var sq2R = NODE_POSITIONS.s7.x + NODE_W + 20, sq2B = NODE_POSITIONS.s10.y + 112;
  nodesHtml += '<div class="dgroup-sequential" style="left:' + sq2L + 'px;top:' + sq2T + 'px;width:' + (sq2R-sq2L) + 'px;height:' + (sq2B-sq2T) + 'px">';
  nodesHtml += '<span class="dgroup-sequential-label">SEQUENTIAL</span></div>';

  nodesEl.innerHTML = nodesHtml;

  // Draw SVG arrows from COMPUTED_EDGES
  var svgHtml = '';
  var edgeKeys = Object.keys(COMPUTED_EDGES);

  // Count incoming edges per target for spread calculation
  var incomingEdges = {};
  edgeKeys.forEach(function(key) {
    var edge = COMPUTED_EDGES[key];
    if (!incomingEdges[edge.target]) incomingEdges[edge.target] = [];
    incomingEdges[edge.target].push(edge.source);
  });

  function spreadX(nodeX, index, count) {
    if (count <= 1) return nodeX + NODE_W / 2;
    var pad = NODE_W / 2 - Math.min(count - 1, 6) * 5;
    var usable = NODE_W - pad * 2;
    return nodeX + pad + (index / (count - 1)) * usable;
  }

  var inIdx = {};
  edgeKeys.forEach(function(key) {
    var edge = COMPUTED_EDGES[key];
    var from = NODE_POSITIONS[edge.source];
    var to = NODE_POSITIONS[edge.target];
    if (!from || !to) return;

    var isActive = state.selectedStep === edge.source || state.selectedStep === edge.target;
    var isHighlighted = state.highlightedEdge === key;

    var fromCx = from.x + NODE_W / 2;
    var fromBottom = from.y + 85;

    var inCount = (incomingEdges[edge.target] || []).length;
    var iIdx = inIdx[edge.target] || 0;
    inIdx[edge.target] = iIdx + 1;
    var toCx = spreadX(to.x, iIdx, inCount);
    var toTop = to.y;

    var dy = toTop - fromBottom;
    var cpOffset = Math.max(40, Math.abs(dy) * 0.35);

    var color, width;
    if (isHighlighted) { color = '#58a6ff'; width = 3; }
    else if (isActive) { color = '#58a6ff'; width = 2.5; }
    else { color = 'rgba(48,54,61,0.45)'; width = 1.5; }

    var arrowLen = 8;
    var pathEndY = toTop - arrowLen;
    var pathD = 'M ' + fromCx + ' ' + fromBottom + ' C ' + fromCx + ' ' + (fromBottom + cpOffset) + ', ' + toCx + ' ' + (toTop - cpOffset) + ', ' + toCx + ' ' + pathEndY;

    var pathId = key.replace('->','-');
    svgHtml += '<path id="epath-' + pathId + '" d="' + pathD + '" fill="none" stroke="' + color + '" stroke-width="' + width + '"/>';
    svgHtml += '<polygon id="earrow-' + pathId + '" points="' + (toCx-4) + ',' + pathEndY + ' ' + (toCx+4) + ',' + pathEndY + ' ' + toCx + ',' + toTop + '" fill="' + color + '"/>';
    // Invisible hit target for hover tooltip
    svgHtml += '<path d="' + pathD + '" fill="none" stroke="transparent" stroke-width="14" style="pointer-events:stroke;cursor:pointer" data-edge="' + key + '" onmouseenter="showEdgeTooltip(event,\'' + key + '\')" onmouseleave="hideEdgeTooltip()" onclick="selectEdgeNode(\'' + key + '\')"/>';
  });

  // Validation loop arrows (pink, dotted, bidirectional)
  VALIDATION_LOOPS.forEach(function(loop) {
    var from = NODE_POSITIONS[loop.from];
    var to = NODE_POSITIONS[loop.to];
    if (!from || !to) return;
    var loopKey = loop.from + '<->' + loop.to;
    var isHighlighted = state.highlightedEdge === loopKey;
    var isActive = state.selectedStep === loop.from || state.selectedStep === loop.to;

    var color = isHighlighted ? '#ff69b4' : (isActive ? 'rgba(255,105,180,0.8)' : 'rgba(255,105,180,0.35)');
    var width = isHighlighted ? 3 : (isActive ? 2.5 : 1.5);

    var fromX = from.x + NODE_W + 8;
    var fromY = from.y + 42;
    var toX = to.x + NODE_W + 8;
    var toY = to.y + 42;

    var bulge = 60;
    var cpX = Math.max(fromX, toX) + bulge;
    var pathD = 'M ' + fromX + ' ' + fromY + ' C ' + cpX + ' ' + fromY + ', ' + cpX + ' ' + toY + ', ' + toX + ' ' + toY;

    var a1 = '<polygon points="' + toX + ',' + toY + ' ' + (toX+7) + ',' + (toY-4) + ' ' + (toX+7) + ',' + (toY+4) + '" fill="' + color + '"/>';
    var a2 = '<polygon points="' + fromX + ',' + fromY + ' ' + (fromX+7) + ',' + (fromY-4) + ' ' + (fromX+7) + ',' + (fromY+4) + '" fill="' + color + '"/>';

    svgHtml += '<path id="epath-vloop-' + loop.from + '-' + loop.to + '" d="' + pathD + '" fill="none" stroke="' + color + '" stroke-width="' + width + '" stroke-dasharray="4,4"/>';
    svgHtml += a1 + a2;
    svgHtml += '<path d="' + pathD + '" fill="none" stroke="transparent" stroke-width="14" style="pointer-events:stroke;cursor:pointer" data-edge="' + loopKey + '" onmouseenter="showEdgeTooltip(event,\'' + loopKey + '\')" onmouseleave="hideEdgeTooltip()"/>';
  });

  svgEl.innerHTML = svgHtml;
}

function selectDiagramNode(id) {
  state.selectedStep = id;
  renderDiagram();
  showDiagramDetail(id);
  updatePrompt();
}

// showDiagramDetail — renders the same content as renderDetail but in the floating panel
// Uses the SAME section-rendering logic from renderDetail
function showDiagramDetail(id) {
  var s = STEPS.find(function(x) { return x.id === id; });
  var el = document.getElementById('diagramDetail');
  if (!s) { closeDiagramDetail(); return; }

  // Build HTML using same sections as renderDetail (see spec for full list)
  var html = '<button class="detail-close" onclick="closeDiagramDetail()">&times;</button>';
  html += '<h2 style="font-size:16px;font-weight:600;color:var(--text-bright);margin-bottom:4px;padding-right:30px">Step ' + s.num + ': ' + s.name + '</h2>';
  html += '<div style="font-size:12px;color:var(--text-dim);margin-bottom:16px">' + s.meta + '</div>';

  // [Same sections as renderDetail: conditionalRun, implementation, tools, dataIn, dataOut, feedsInto, prompt/detail, scoring, checks, qualityRules, edgeCases]
  // See spec for exact rendering logic

  el.innerHTML = html;
  el.classList.add('visible');
}

function closeDiagramDetail() {
  document.getElementById('diagramDetail').classList.remove('visible');
  state.selectedStep = null;
  if (state.view === 'diagram') renderDiagram();
}

// Scroll zoom
// document.getElementById('diagramWrap').addEventListener('wheel', function(e) {
//   if (e.ctrlKey || e.metaKey) {
//     e.preventDefault();
//     var delta = e.deltaY < 0 ? 0.05 : -0.05;
//     zoomDiagram(delta);
//   }
// }, { passive: false });
