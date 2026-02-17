// ═══════════════════════════════════════════════════════
// EDGE TOOLTIPS & HIGHLIGHTING from v2
// Port this verbatim into pipeline-explorer.html
// ═══════════════════════════════════════════════════════

function showEdgeTooltip(event, edgeKey) {
  var tooltip = document.getElementById('edgeTooltip');
  var html = '';

  var loop = VALIDATION_LOOPS.find(function(l) { return l.from + '<->' + l.to === edgeKey; });
  if (loop) {
    var fromStep = STEPS.find(function(s) { return s.id === loop.from; });
    var toStep = STEPS.find(function(s) { return s.id === loop.to; });
    if (!fromStep || !toStep) return;
    html += '<div style="color:#ff69b4;font-weight:600;font-size:11px;margin-bottom:6px">\u21c4 Validation Loop</div>';
    html += '<div style="color:var(--text-bright);font-size:10px;margin-bottom:6px">Step ' + fromStep.num + ' \u21c4 Step ' + toStep.num + '</div>';
    html += '<div style="color:var(--text-dim);font-size:10px">' + loop.label + '</div>';
  } else {
    var edge = COMPUTED_EDGES[edgeKey];
    if (!edge) return;
    var sourceStep = STEPS.find(function(s) { return s.id === edge.source; });
    var targetStep = STEPS.find(function(s) { return s.id === edge.target; });
    if (!sourceStep || !targetStep) return;

    html += '<div style="color:var(--text-bright);font-weight:600;font-size:11px;margin-bottom:6px">';
    html += 'Step ' + sourceStep.num + ' \u2192 Step ' + targetStep.num;
    html += '</div>';
    html += '<div style="color:var(--text-dim);font-size:10px;margin-bottom:6px">';
    html += sourceStep.name + ' \u2192 ' + targetStep.name;
    html += '</div>';

    if (edge.variables.length) {
      html += '<div class="data-flow" style="gap:3px">';
      edge.variables.forEach(function(v) {
        html += '<span class="data-chip chip-in" style="font-size:9px;padding:2px 6px">' + v + '</span>';
      });
      html += '</div>';
    }
  }

  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  tooltip.style.left = Math.min(event.clientX + 12, window.innerWidth - 300) + 'px';
  tooltip.style.top = (event.clientY - 10) + 'px';
}

function hideEdgeTooltip() {
  document.getElementById('edgeTooltip').style.display = 'none';
}

function highlightEdge(edgeKey) {
  state.highlightedEdge = edgeKey;
  var isLoop = edgeKey.indexOf('<->') !== -1;
  if (isLoop) {
    var parts = edgeKey.split('<->');
    var visPath = document.getElementById('epath-vloop-' + parts[0] + '-' + parts[1]);
    if (visPath) { visPath.setAttribute('stroke', '#ff69b4'); visPath.setAttribute('stroke-width', '3'); }
  } else {
    var visPath = document.getElementById('epath-' + edgeKey.replace('->','-'));
    if (visPath) { visPath.setAttribute('stroke', '#58a6ff'); visPath.setAttribute('stroke-width', '3'); }
    var visArrow = document.getElementById('earrow-' + edgeKey.replace('->','-'));
    if (visArrow) visArrow.setAttribute('fill', '#58a6ff');
  }
  document.querySelectorAll('[data-edge]').forEach(function(el) {
    el.classList.toggle('edge-highlighted', el.getAttribute('data-edge') === edgeKey);
  });
}

function unhighlightEdge() {
  if (state.highlightedEdge) {
    var isLoop = state.highlightedEdge.indexOf('<->') !== -1;
    if (isLoop) {
      var parts = state.highlightedEdge.split('<->');
      var loop = VALIDATION_LOOPS.find(function(l) { return l.from === parts[0] && l.to === parts[1]; });
      if (loop) {
        var isActive = state.selectedStep === loop.from || state.selectedStep === loop.to;
        var color = isActive ? 'rgba(255,105,180,0.8)' : 'rgba(255,105,180,0.35)';
        var width = isActive ? 2.5 : 1.5;
        var visPath = document.getElementById('epath-vloop-' + loop.from + '-' + loop.to);
        if (visPath) { visPath.setAttribute('stroke', color); visPath.setAttribute('stroke-width', String(width)); }
      }
    } else {
      var edge = COMPUTED_EDGES[state.highlightedEdge];
      if (edge) {
        var isActive = state.selectedStep === edge.source || state.selectedStep === edge.target;
        var color = isActive ? '#58a6ff' : 'rgba(48,54,61,0.45)';
        var width = isActive ? 2.5 : 1.5;
        var visPath = document.getElementById('epath-' + state.highlightedEdge.replace('->','-'));
        if (visPath) { visPath.setAttribute('stroke', color); visPath.setAttribute('stroke-width', String(width)); }
        var visArrow = document.getElementById('earrow-' + state.highlightedEdge.replace('->','-'));
        if (visArrow) visArrow.setAttribute('fill', color);
      }
    }
  }
  state.highlightedEdge = null;
  document.querySelectorAll('.edge-highlighted').forEach(function(el) {
    el.classList.remove('edge-highlighted');
  });
}

function selectEdgeNode(edgeKey) {
  var edge = COMPUTED_EDGES[edgeKey];
  if (!edge) return;
  if (state.view === 'diagram') selectDiagramNode(edge.target);
}
