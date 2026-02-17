// ═══════════════════════════════════════════════════════
// RICH MARKDOWN GENERATION from v2
// Replaces pipeline-explorer's simple buildAllMarkdown()
// ═══════════════════════════════════════════════════════

function generateStepMarkdown(s) {
  var md = '';

  // Header
  md += '## Step ' + s.num + ': ' + s.name + '\n\n';
  md += '> ' + s.meta + '\n\n';

  // Metadata
  var types = getTypes(s).join(' + ');
  var exec = s.parallel ? 'parallel (Group ' + PARALLEL_GROUPS[s.id] + ')' : 'sequential';
  md += '### Metadata\n\n';
  md += '- **Node Step ID:** ' + s.id + '\n';
  md += '- **Node Type:** ' + types + '\n';
  md += '- **Node Execution:** ' + exec + '\n';
  // PIPELINE-SPECIFIC: add module/fn/timeout/service
  if (s.module) md += '- **Module:** ' + s.module + '\n';
  if (s.fn) md += '- **Function:** ' + s.fn + '\n';
  if (s.timeout) md += '- **Timeout:** ' + s.timeout + '\n';
  if (s.service) md += '- **Service:** ' + s.service + '\n';

  // Conditional Run
  if (s.conditionalRun) {
    var crType = s.conditionalRun.type;
    var crLabel = crType === 'always' ? 'Always runs' : crType === 'stop' ? 'Hard stop' : crType === 'skip' ? 'Conditional skip' : 'Branches';
    md += '\n### Conditional Run\n\n';
    md += '**' + crLabel + '**' + (s.conditionalRun.rule ? ' — ' + s.conditionalRun.rule.replace(/<b>/g, '**').replace(/<\/b>/g, '**') : '') + '\n';
  }

  // Tool Calls
  if (s.tools && s.tools.length) {
    md += '\n### Tool Calls\n\n';
    s.tools.forEach(function(t) { md += '- `' + t + '`\n'; });
  }

  // Data In (grouped by source)
  if (s.inputs && s.inputs.length) {
    md += '\n### Data In\n';
    var groups = {};
    s.inputs.forEach(function(name) {
      var base = name.split('.')[0];
      var src = INPUT_SOURCES[name] || INPUT_SOURCES[base] || null;
      if (!groups[src]) groups[src] = [];
      groups[src].push(name);
    });
    var order = [null].concat(STEPS.map(function(x) { return x.id; }));
    var sortedKeys = Object.keys(groups).sort(function(a, b) {
      return order.indexOf(a === 'null' ? null : a) - order.indexOf(b === 'null' ? null : b);
    });
    sortedKeys.forEach(function(src) {
      var label = getSourceLabel(src === 'null' ? null : src);
      md += '\n**From ' + label + ':**\n';
      groups[src].forEach(function(n) { md += '- `' + n + '`\n'; });
    });
  }

  // Data Out
  if (s.outputs && s.outputs.length) {
    md += '\n### Data Out\n\n';
    s.outputs.forEach(function(d) {
      var schema = s.outputSchema ? s.outputSchema[d] : null;
      if (schema) {
        md += '- `' + d + '`: ' + schema + '\n';
      } else {
        md += '- `' + d + '`\n';
      }
    });
  }

  // Feeds Into
  var outbound = getOutboundEdges(s.id);
  var loops = VALIDATION_LOOPS.filter(function(l) { return l.from === s.id || l.to === s.id; });
  if (outbound.length || loops.length) {
    md += '\n### Feeds Into\n\n';
    loops.forEach(function(loop) {
      var otherId = loop.from === s.id ? loop.to : loop.from;
      var other = STEPS.find(function(x) { return x.id === otherId; });
      if (!other) return;
      md += '**\u21c4 Validation loop** with Step ' + other.num + ': ' + other.name + '\n';
      md += loop.label.replace(/<b>/g, '**').replace(/<\/b>/g, '**') + '\n\n';
    });
    outbound.forEach(function(edge) {
      var target = STEPS.find(function(x) { return x.id === edge.target; });
      if (!target) return;
      md += '**\u2192 Step ' + target.num + ': ' + target.name + ':** ' + edge.variables.join(', ') + '\n';
    });
  }

  // Detail / Prompt sections
  var pt = primaryType(s);
  var isHybrid = getTypes(s).length > 1;

  if (isHybrid && s.detail) {
    var detailLabel = pt === 'tool' ? 'Tool Logic' : pt === 'validate' ? 'Validation Logic' : pt === 'logic' ? 'Logic' : pt === 'sqlite' ? 'DB Operations' : 'Detail';
    md += '\n### ' + detailLabel + '\n\n```\n' + s.detail + '\n```\n';
  }
  if (hasType(s, 'llm') && s.prompt) {
    var prompt = state.editedPrompts[s.id] || s.prompt;
    md += '\n### LLM Prompt\n\n```\n' + prompt + '\n```\n';
  }
  if (!hasType(s, 'llm') && s.prompt) {
    md += '\n### Prompt\n\n```\n' + s.prompt + '\n```\n';
  }
  if (!isHybrid && s.detail) {
    var dLabel = pt === 'template' ? 'Template' : pt === 'validate' ? 'Validation' : pt === 'llm' ? 'Detail' : pt === 'sqlite' ? 'DB Operations' : 'Logic';
    md += '\n### ' + dLabel + '\n\n```\n' + s.detail + '\n```\n';
  }

  // Scoring (pipeline-specific: s4)
  if (s.scoring) {
    md += '\n### Scoring Weights\n\n';
    Object.entries(s.scoring).forEach(function([k,v]) {
      md += '- **' + k.replace(/_/g, ' ') + ':** ' + v + '%\n';
    });
  }

  // Validation checks (pipeline-specific: s14)
  if (s.checks) {
    md += '\n### Validation Checks\n\n';
    s.checks.forEach(function(c, i) {
      md += (i+1) + '. ' + c + '\n';
    });
  }

  // Quality Rules
  if (s.qualityRules && s.qualityRules.length) {
    md += '\n### Quality Rules\n\n';
    s.qualityRules.forEach(function(r) { md += '- ' + r + '\n'; });
  }

  // Edge Cases
  if (s.edgeCases && s.edgeCases.length) {
    md += '\n### Errors & Fallbacks\n\n';
    s.edgeCases.forEach(function(ec) {
      var sev = (ec.severity || 'degrade').toUpperCase();
      md += '- **' + sev + '** — ' + ec.label + ': ' + ec.action + '\n';
    });
  }

  return md;
}

function generateAllMarkdown() {
  var md = '';
  var today = new Date();
  var dateStr = today.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  md += '# Starbridge Intel Brief Pipeline — Full Workflow Spec\n\n';
  md += '> 19-step pipeline: webhook → discovery → intel → report → publish\n';
  md += '> Generated: ' + dateStr + '\n\n';

  // Table of Contents
  md += '## Table of Contents\n\n';
  var tocPhase = '';
  STEPS.forEach(function(s) {
    if (s.phase !== tocPhase) {
      if (tocPhase) md += '\n';
      md += '**Phase ' + PHASE_ROMAN[s.phase] + ': ' + PHASE_LABELS[s.phase] + '**\n';
      tocPhase = s.phase;
    }
    md += '- Step ' + s.num + ': ' + s.name + ' (' + s.id + ')\n';
  });
  md += '\n';

  var lastPhase = '';
  STEPS.forEach(function(s, i) {
    if (s.phase !== lastPhase) {
      if (lastPhase) md += '\n---\n\n';
      md += '# Phase ' + PHASE_ROMAN[s.phase] + ': ' + PHASE_LABELS[s.phase] + '\n\n';
      lastPhase = s.phase;
    } else if (i > 0) {
      md += '\n---\n\n';
    }
    md += generateStepMarkdown(s);
  });

  return md;
}
