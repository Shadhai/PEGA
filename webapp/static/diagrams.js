/* ==========================================================================
   CINT-70 — SCHEMATIC DIAGRAMS
   Hand-built, data-driven SVG diagrams (no third-party diagram library)
   styled to match the mission-control design system. Two views:
     - renderArchitecture(): system/data-flow schematic
     - renderWorkflow():      swimlane mission-event timeline
   ========================================================================== */

// ---- small SVG helpers ---------------------------------------------------

function rectNode(n) {
  const { x, y, w, h, id, label, sub, accent, shape } = n;
  const cls = `sc-node${accent ? ' accent-' + accent : ''}`;
  if (shape === 'diamond') {
    const cx = x + w / 2, cy = y + h / 2;
    const pts = [
      [cx, y], [x + w, cy], [cx, y + h], [x, cy]
    ].map(p => p.join(',')).join(' ');
    return `
      <g class="${cls}" data-id="${id}">
        <polygon points="${pts}" />
        <text x="${cx}" y="${cy - 2}" text-anchor="middle" font-weight="600">${label}</text>
        ${sub ? `<text class="sc-sub" x="${cx}" y="${cy + 12}" text-anchor="middle">${sub}</text>` : ''}
      </g>`;
  }
  const cx = x + w / 2, cy = y + h / 2;
  return `
    <g class="${cls}" data-id="${id}">
      <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3" />
      <text x="${cx}" y="${sub ? cy - 3 : cy + 4}" text-anchor="middle" font-weight="600">${label}</text>
      ${sub ? `<text class="sc-sub" x="${cx}" y="${cy + 13}" text-anchor="middle">${sub}</text>` : ''}
    </g>`;
}

// anchor point on a node's edge, by side: 'l' 'r' 't' 'b'
function anchor(n, side) {
  const cx = n.x + n.w / 2, cy = n.y + n.h / 2;
  switch (side) {
    case 'l': return [n.x, cy];
    case 'r': return [n.x + n.w, cy];
    case 't': return [cx, n.y];
    case 'b': return [cx, n.y + n.h];
    default: return [cx, cy];
  }
}

// orthogonal elbow path between two anchors
function elbow(a, b, bend = 'auto') {
  const [x1, y1] = a, [x2, y2] = b;
  if (bend === 'h') {
    const midX = (x1 + x2) / 2;
    return `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`;
  }
  if (bend === 'v') {
    const midY = (y1 + y2) / 2;
    return `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`;
  }
  return `M ${x1} ${y1} L ${x2} ${y1} L ${x2} ${y2}`;
}

function edgePath(d, flow = true, rust = false, label = '') {
  const cls = flow ? `sc-edge-flow${rust ? ' rust' : ''}` : 'sc-edge';
  const lbl = label ? labelOnPath(d, label) : '';
  return `<path class="${cls}" d="${d}" />${lbl}`;
}

function labelOnPath(d, text) {
  // crude midpoint estimate: parse the 2nd coordinate pair of the path
  const nums = d.match(/-?\d+(\.\d+)?/g).map(Number);
  const midX = (nums[0] + nums[nums.length - 2]) / 2;
  const midY = (nums[1] + nums[nums.length - 1]) / 2;
  return `<rect x="${midX - text.length * 3.1 - 4}" y="${midY - 9}" width="${text.length * 6.2 + 8}" height="14" fill="var(--panel,#0a0f16)" opacity="0.85" />
          <text class="sc-edge-label" x="${midX}" y="${midY + 2}" text-anchor="middle">${text}</text>`;
}

// ---- ARCHITECTURE DIAGRAM -------------------------------------------------

const ARCH_NODES = {
  cmd:        { id: 'cmd',        x: 20,  y: 460, w: 150, h: 54, label: 'USER COMMAND',        sub: 'natural-language input' },
  classifier: { id: 'classifier', x: 230, y: 460, w: 160, h: 54, label: 'LLM CLASSIFIER',       sub: 'Qwen-2.5-1.5B · 4-bit' },
  taskType:   { id: 'taskType',   x: 460, y: 425, w: 170, h: 124, label: 'TASK TYPE', sub: 'routing decision', shape: 'diamond' },

  repair:   { id: 'repair',   x: 700, y: 40,  w: 190, h: 48, label: 'REPAIR PLANS',      sub: 'plan library' },
  inspect:  { id: 'inspect',  x: 700, y: 190, w: 190, h: 48, label: 'INSPECT PLANS',     sub: 'plan library' },
  sample:   { id: 'sample',   x: 700, y: 340, w: 190, h: 48, label: 'SAMPLE PLANS',      sub: 'plan library' },
  toolchg:  { id: 'toolchg',  x: 700, y: 490, w: 190, h: 48, label: 'TOOL CHANGE PLANS', sub: 'plan library' },
  leakchk:  { id: 'leakchk',  x: 700, y: 640, w: 190, h: 48, label: 'LEAK CHECK PLANS',  sub: 'plan library' },

  coordSearch: { id: 'coordSearch', x: 960, y: 340, w: 210, h: 54, label: 'ADAPTIVE COORD. SEARCH', sub: 'candidate path gen' },
  graphVal:    { id: 'graphVal',    x: 960, y: 450, w: 210, h: 54, label: 'KÙZUDB GRAPH VALIDATION', sub: 'Cypher constraint checks' },
  violation:   { id: 'violation',   x: 970, y: 555, w: 190, h: 120, label: 'VIOLATION?', sub: 'collision / limit', shape: 'diamond' },

  approved: { id: 'approved', x: 800, y: 740, w: 170, h: 50, label: 'APPROVED', sub: 'execute on hardware', accent: 'green' },
  recovery: { id: 'recovery', x: 1060, y: 740, w: 190, h: 50, label: 'LANGGRAPH RECOVERY', sub: 'retry ≤ 3, new coords' },
  rejected: { id: 'rejected', x: 1060, y: 840, w: 190, h: 50, label: 'REJECTED', sub: 'human intervention', accent: 'red' },

  evidence: { id: 'evidence', x: 880, y: 930, w: 190, h: 50, label: 'EVIDENCE LOGGER', sub: 'cited decision trail' },
  memory:   { id: 'memory',   x: 880, y: 1020, w: 190, h: 48, label: 'EXPERIENCE MEMORY', sub: 'SQLite + embeddings' },
};

const ARCH_DETAILS = {
  cmd: 'Operator or upstream system issues a plain-language directive — e.g. "repair thermal shield panel 3."',
  classifier: 'A locally-run, 4-bit quantised Qwen-2.5-1.5B model classifies intent into one of five task types. No external API calls.',
  taskType: 'Routes to the matching symbolic plan library. This is the only branch point in the pipeline — everything downstream is deterministic.',
  repair: 'Parameterised repair sequences: tool approach, contact force envelopes, dwell times.',
  inspect: 'Camera / sensor sweep patterns with standoff-distance constraints.',
  sample: 'Sample-arm extension paths bounded by regolith contact limits.',
  toolchg: 'End-effector swap choreography, interlocked against tool-bay occupancy.',
  leakchk: 'Pressure-differential probe routes around seals and joints.',
  coordSearch: 'Given a plan skeleton, searches for joint coordinates that satisfy reachability before anything touches the graph database.',
  graphVal: 'Every step is checked against KùzuDB — a graph of joints, obstacles, tools and thermal limits — via Cypher queries, not learned heuristics.',
  violation: 'A single failed check (collision, joint limit, force limit) trips this gate. Physics, not confidence scores, decides.',
  approved: 'Plan is cleared for execution with a trust score attached, then handed to the evidence logger.',
  recovery: 'A LangGraph cyclic state machine perturbs coordinates and re-submits to search — up to three attempts before giving up.',
  rejected: 'After three failed recoveries, the plan is refused and flagged for a human operator — no silent fallback execution.',
  evidence: 'Every approval or rejection is logged with the exact constraint citations that produced the outcome — built for audit, not just debugging.',
  memory: 'Successes and failure patterns are embedded and stored, so future coordinate searches can start from what already worked.',
};

function archEdges() {
  const n = ARCH_NODES;
  const libs = ['repair', 'inspect', 'sample', 'toolchg', 'leakchk'];
  const libLabels = ['repair', 'inspect', 'sample', 'tool_change', 'leak_check'];
  let s = '';
  s += edgePath(elbow(anchor(n.cmd, 'r'), anchor(n.classifier, 'l')), true);
  s += edgePath(elbow(anchor(n.classifier, 'r'), anchor(n.taskType, 'l')), true);
  libs.forEach((id, i) => {
    s += edgePath(elbow(anchor(n.taskType, 'r'), anchor(n[id], 'l'), 'h'), true, false, libLabels[i]);
    s += edgePath(elbow(anchor(n[id], 'r'), anchor(n.coordSearch, 'l'), 'h'));
  });
  s += edgePath(elbow(anchor(n.coordSearch, 'b'), anchor(n.graphVal, 't')), true);
  s += edgePath(elbow(anchor(n.graphVal, 'b'), anchor(n.violation, 't')), true);
  s += edgePath(elbow(anchor(n.violation, 'l'), anchor(n.approved, 't'), 'v'), true, false, 'no');
  s += edgePath(elbow(anchor(n.violation, 'r'), anchor(n.recovery, 't'), 'v'), true, true, 'yes');
  // retry loop back up to coord search
  s += edgePath(`M ${n.recovery.x + n.recovery.w} ${n.recovery.y + n.recovery.h / 2}
                 L ${n.recovery.x + n.recovery.w + 60} ${n.recovery.y + n.recovery.h / 2}
                 L ${n.recovery.x + n.recovery.w + 60} ${n.coordSearch.y + n.coordSearch.h / 2}
                 L ${n.coordSearch.x + n.coordSearch.w} ${n.coordSearch.y + n.coordSearch.h / 2}`,
                 true, true, 'retry ≤ 3');
  s += edgePath(elbow(anchor(n.recovery, 'b'), anchor(n.rejected, 't')), true, true, 'max retries');
  s += edgePath(elbow(anchor(n.approved, 'b'), anchor(n.evidence, 't'), 'v'));
  s += edgePath(elbow(anchor(n.rejected, 'b'), anchor(n.evidence, 'r'), 'v'));
  s += edgePath(elbow(anchor(n.evidence, 'b'), anchor(n.memory, 't')));
  return s;
}

function renderArchitecture() {
  const nodes = Object.values(ARCH_NODES).map(rectNode).join('');
  const edges = archEdges();
  return `
    <div class="schematic-wrap">
      <svg class="schematic-svg" viewBox="0 0 1290 1100" xmlns="http://www.w3.org/2000/svg">
        <g>${edges}</g>
        <g>${nodes}</g>
      </svg>
    </div>
    <p class="diagram-caption">Plan-agnostic validation · graph-grounded constraints · bounded adaptive recovery</p>
    <div class="sc-detail" data-panel="arch">Hover or tap a block to see what it does.</div>
  `;
}

// ---- WORKFLOW (SWIMLANE) DIAGRAM ------------------------------------------

const LANES = ['User', 'LLM Classifier', 'Symbolic Planner', 'KùzuDB Graph', 'Physics Validator', 'Experience Memory'];
const LANE_Y = { 'User': 60, 'LLM Classifier': 160, 'Symbolic Planner': 260, 'KùzuDB Graph': 360, 'Physics Validator': 460, 'Experience Memory': 560 };
const LANE_X0 = 190, LANE_X1 = 1080;

const WF_STEPS = [
  { id: 'w1', from: 'User', to: 'LLM Classifier', x: 260, label: 'command', detail: 'Operator sends: "Repair thermal shield panel 3."' },
  { id: 'w2', from: 'LLM Classifier', to: 'Symbolic Planner', x: 360, label: 'task_type + tool', detail: 'Classifier emits a structured intent: {task_type: repair, tool: thermal_applicator}.' },
  { id: 'w3', from: 'Symbolic Planner', to: 'KùzuDB Graph', x: 460, label: 'query constraints', detail: 'Planner asks the graph for obstacles, joint limits and tool specs relevant to this task.' },
  { id: 'w4', from: 'KùzuDB Graph', to: 'Symbolic Planner', x: 560, label: 'constraints list', detail: 'Graph returns the applicable numeric constraints.' },
  { id: 'w5', from: 'Symbolic Planner', to: 'Physics Validator', x: 660, label: 'candidate plan', detail: 'After an adaptive coordinate search, the planner hands off a plan with proposed coordinates.' },
  { id: 'w6', from: 'Physics Validator', to: 'KùzuDB Graph', x: 760, label: 'check each step', detail: 'Every step is checked for collision and joint/force limits via Cypher queries.' },
  { id: 'w7', from: 'Physics Validator', to: 'Symbolic Planner', x: 860, label: 'violation + retry', detail: 'On a failed check: failure context returns to the planner for replanning (up to 3 attempts).' },
  { id: 'w8', from: 'Physics Validator', to: 'User', x: 960, label: 'approved · trust 95%', detail: 'All steps pass → plan is approved with a computed trust score.' },
  { id: 'w9', from: 'Physics Validator', to: 'Experience Memory', x: 1020, label: 'store outcome', detail: 'Successful plans and failure patterns are both written to experience memory for future reuse.' },
];

function laneRail(name) {
  const y = LANE_Y[name];
  return `
    <line class="sc-lane-line" x1="${LANE_X0}" y1="${y}" x2="${LANE_X1}" y2="${y}" />
    <text class="sc-lane-label" x="20" y="${y + 4}">${name}</text>`;
}

function wfStep(s, i) {
  const y1 = LANE_Y[s.from], y2 = LANE_Y[s.to];
  const isRetry = s.id === 'w7';
  const isBack = y2 < y1 && s.from !== 'Physics Validator' ? true : (s.to === 'Symbolic Planner' && s.from === 'Physics Validator');
  const cls = `sc-edge-flow${isRetry ? ' rust' : ''}`;
  const dot1 = `<circle cx="${s.x}" cy="${y1}" r="3.5" fill="var(--ice,#3ea6ff)" />`;
  const dot2 = `<circle cx="${s.x}" cy="${y2}" r="3.5" fill="var(--ice,#3ea6ff)" />`;
  const midY = (y1 + y2) / 2;
  const label = `<rect x="${s.x + 8}" y="${midY - 9}" width="${s.label.length * 6.1 + 10}" height="15" fill="var(--panel,#0a0f16)" opacity="0.9" />
                 <text class="sc-edge-label" x="${s.x + 13}" y="${midY + 3}">${s.label}</text>`;
  return `
    <g class="sc-node" data-id="${s.id}">
      <path class="${cls}" d="M ${s.x} ${y1} L ${s.x} ${y2}" />
      <path d="M ${s.x} ${y1} L ${s.x} ${y2}" stroke="transparent" stroke-width="16" fill="none" />
      ${dot1}${dot2}${label}
    </g>`;
}

function renderWorkflow() {
  const lanes = LANES.map(laneRail).join('');
  const steps = WF_STEPS.map(wfStep).join('');
  return `
    <div class="schematic-wrap">
      <svg class="schematic-svg" viewBox="0 0 1120 610" xmlns="http://www.w3.org/2000/svg">
        <g>${lanes}</g>
        <g>${steps}</g>
      </svg>
    </div>
    <p class="diagram-caption">One command, six systems: classification → planning → validation → recovery → evidence</p>
    <div class="sc-detail" data-panel="wf">Hover or tap a step on the timeline to see what it carries.</div>
  `;
}

// ---- wiring ---------------------------------------------------------------

function wireInteractivity(root, details, panelSelector) {
  const panel = root.querySelector(panelSelector);
  root.querySelectorAll('.sc-node').forEach(node => {
    const id = node.getAttribute('data-id');
    const text = details[id];
    if (!text || !panel) return;
    const show = () => {
      root.querySelectorAll('.sc-node').forEach(n => n.classList.remove('active'));
      node.classList.add('active');
      panel.innerHTML = `<span class="k">▸</span> <strong>${text}</strong>`;
    };
    node.addEventListener('mouseenter', show);
    node.addEventListener('click', show);
    node.addEventListener('focus', show);
  });
}

const WF_DETAILS = Object.fromEntries(WF_STEPS.map(s => [s.id, s.detail]));

export function mountArchitectureDiagram(container) {
  container.innerHTML = renderArchitecture();
  wireInteractivity(container, ARCH_DETAILS, '[data-panel="arch"]');
}

export function mountWorkflowDiagram(container) {
  container.innerHTML = renderWorkflow();
  wireInteractivity(container, WF_DETAILS, '[data-panel="wf"]');
}