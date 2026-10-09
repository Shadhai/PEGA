// import * as THREE from 'three';
// import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
// import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
// import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
// import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// const SCENE_COLORS = { dark: 0x050510, light: 0xe8eef5 };
// const GLOBE_R = 2;
// const MARS_COLOR = 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/mars_1k_color.jpg';
// const MARS_BUMP = 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/mars_1k_topo.jpg';

// // --- Container ---
// const container = document.getElementById('globe-container');
// const w = () => container.clientWidth;
// const h = () => container.clientHeight;

// // --- Scene ---
// const scene = new THREE.Scene();
// scene.background = new THREE.Color(SCENE_COLORS.dark);
// scene.fog = new THREE.FogExp2(SCENE_COLORS.dark, 0.035);

// const camera = new THREE.PerspectiveCamera(45, w() / h(), 0.1, 1000);
// camera.position.set(0, 1, 12);

// const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
// renderer.setSize(w(), h());
// renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
// renderer.toneMapping = THREE.ACESFilmicToneMapping;
// renderer.toneMappingExposure = 1.1;
// container.appendChild(renderer.domElement);

// const composer = new EffectComposer(renderer);
// composer.addPass(new RenderPass(scene, camera));
// const bloomPass = new UnrealBloomPass(new THREE.Vector2(w(), h()), 0.6, 0.4, 0.85);
// composer.addPass(bloomPass);

// const labelRenderer = new CSS2DRenderer();
// labelRenderer.setSize(w(), h());
// labelRenderer.domElement.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;';
// container.appendChild(labelRenderer.domElement);

// const controls = new OrbitControls(camera, renderer.domElement);
// controls.enableDamping = true;
// controls.dampingFactor = 0.05;
// controls.minDistance = 4;
// controls.maxDistance = 25;
// controls.autoRotate = true;
// controls.autoRotateSpeed = 0.3;

// // --- Starfield ---
// const starGeo = new THREE.BufferGeometry();
// const starCount = 3000;
// const starPos = new Float32Array(starCount * 3);
// for (let i = 0; i < starCount * 3; i++) starPos[i] = (Math.random() - 0.5) * 120;
// starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
// const starfield = new THREE.Points(
//   starGeo,
//   new THREE.PointsMaterial({ color: 0xffffff, size: 0.08, transparent: true, opacity: 0.8 })
// );
// scene.add(starfield);

// // --- Mars Globe ---
// const textureLoader = new THREE.TextureLoader();
// const marsTex = textureLoader.load(MARS_COLOR);
// const bumpTex = textureLoader.load(MARS_BUMP);

// const globe = new THREE.Mesh(
//   new THREE.SphereGeometry(GLOBE_R, 64, 64),
//   new THREE.MeshStandardMaterial({
//     map: marsTex,
//     bumpMap: bumpTex,
//     bumpScale: 0.04,
//     roughness: 0.9,
//     metalness: 0.05,
//   })
// );
// scene.add(globe);

// const wireOverlay = new THREE.Mesh(
//   new THREE.SphereGeometry(GLOBE_R + 0.01, 32, 32),
//   new THREE.MeshBasicMaterial({ color: 0x00d4ff, wireframe: true, transparent: true, opacity: 0.06 })
// );
// scene.add(wireOverlay);

// const atmosphere = new THREE.Mesh(
//   new THREE.SphereGeometry(GLOBE_R * 1.08, 64, 64),
//   new THREE.MeshBasicMaterial({ color: 0xff6b35, transparent: true, opacity: 0.18, side: THREE.BackSide })
// );
// scene.add(atmosphere);

// scene.add(new THREE.AmbientLight(0x404060, 0.6));
// const sunLight = new THREE.DirectionalLight(0xffeedd, 1.2);
// sunLight.position.set(8, 5, 10);
// scene.add(sunLight);
// const rimLight = new THREE.PointLight(0x00d4ff, 0.5, 30);
// rimLight.position.set(-6, 2, -4);
// scene.add(rimLight);

// // --- Markers & effects ---
// const markers = [];
// const pulseMeshes = [];

// function toGlobeCoords(x, y, z) {
//   const maxDist = 10;
//   const v = new THREE.Vector3((x / maxDist) * GLOBE_R, (y / maxDist) * GLOBE_R, (z / maxDist) * GLOBE_R);
//   return v.normalize().multiplyScalar(GLOBE_R + 0.05);
// }

// function addMarker(pos, color, label, meta = {}) {
//   const group = new THREE.Group();
//   group.position.copy(pos);

//   const core = new THREE.Mesh(
//     new THREE.SphereGeometry(0.06, 16, 16),
//     new THREE.MeshBasicMaterial({ color })
//   );
//   group.add(core);

//   const glow = new THREE.Mesh(
//     new THREE.SphereGeometry(0.12, 16, 16),
//     new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.25 })
//   );
//   group.add(glow);
//   pulseMeshes.push(glow);

//   if (meta.danger) {
//     const ring = new THREE.Mesh(
//       new THREE.RingGeometry(0.14, 0.18, 32),
//       new THREE.MeshBasicMaterial({ color: 0xff1744, transparent: true, opacity: 0.6, side: THREE.DoubleSide })
//     );
//     ring.lookAt(pos.clone().multiplyScalar(2));
//     group.add(ring);
//   }

//   scene.add(group);
//   markers.push({ group, core, meta: { ...meta, label } });

//   const div = document.createElement('div');
//   div.className = 'marker-label';
//   div.textContent = label;
//   div.style.borderColor = meta.danger ? '#ff1744' : '#00d4ff';
//   const labelObj = new CSS2DObject(div);
//   labelObj.position.set(0.15, 0.15, 0);
//   group.add(labelObj);
// }

// function addJointArc(from, to, color = 0x4488ff) {
//   const mid = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(GLOBE_R * 1.4);
//   const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
//   const line = new THREE.Line(
//     new THREE.BufferGeometry().setFromPoints(curve.getPoints(32)),
//     new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 })
//   );
//   scene.add(line);
// }

// async function loadSceneData() {
//   try {
//     const obstacles = await (await fetch('/api/obstacles')).json();
//     obstacles.forEach(o => {
//       const pos = toGlobeCoords(o.x, o.y, o.z);
//       const danger = o.clearance < 0.5;
//       addMarker(pos, danger ? 0xff1744 : 0x00e676, o.name, {
//         danger,
//         clearance: o.clearance,
//         type: 'obstacle',
//       });
//     });
//   } catch (_) {}

//   try {
//     const joints = await (await fetch('/api/joints')).json();
//     const jointPositions = [];
//     joints.forEach((j, i) => {
//       const angle = (i / joints.length) * Math.PI * 2;
//       const pos = new THREE.Vector3(Math.cos(angle) * GLOBE_R, 0.2, Math.sin(angle) * GLOBE_R)
//         .normalize()
//         .multiplyScalar(GLOBE_R + 0.05);
//       jointPositions.push(pos);
//       addMarker(pos, 0x4488ff, j.name, { type: 'joint', min: j.min, max: j.max });
//     });
//     for (let i = 0; i < jointPositions.length; i++) {
//       addJointArc(jointPositions[i], jointPositions[(i + 1) % jointPositions.length]);
//     }
//   } catch (_) {}
// }

// // --- Theme toggle (syncs 3D scene) ---
// const themeBtn = document.getElementById('themeToggle');

// function applyTheme(isLight) {
//   document.body.classList.toggle('light', isLight);
//   themeBtn.textContent = isLight ? '☀️ Light' : '🌙 Dark';
//   const bg = isLight ? SCENE_COLORS.light : SCENE_COLORS.dark;
//   scene.background = new THREE.Color(bg);
//   scene.fog.color = new THREE.Color(bg);
//   starfield.material.opacity = isLight ? 0.15 : 0.8;
//   atmosphere.material.opacity = isLight ? 0.08 : 0.18;
// }

// themeBtn.addEventListener('click', () => applyTheme(!document.body.classList.contains('light')));

// // --- Camera intro ---
// const introStart = performance.now();
// const introDuration = 2500;
// const startCam = new THREE.Vector3(0, 8, 20);
// const endCam = new THREE.Vector3(5, 2, 8);
// let introComplete = false;

// // --- Hover tooltip ---
// const raycaster = new THREE.Raycaster();
// const mouse = new THREE.Vector2();
// const tooltip = document.createElement('div');
// tooltip.className = 'globe-tooltip';
// container.appendChild(tooltip);

// renderer.domElement.addEventListener('mousemove', (e) => {
//   const rect = renderer.domElement.getBoundingClientRect();
//   mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
//   mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
//   raycaster.setFromCamera(mouse, camera);
//   const cores = markers.map(m => m.core);
//   const hits = raycaster.intersectObjects(cores);
//   if (hits.length) {
//     const hit = markers.find(m => m.core === hits[0].object);
//     if (hit) {
//       const m = hit.meta;
//       tooltip.style.display = 'block';
//       tooltip.style.left = `${e.clientX - container.getBoundingClientRect().left + 12}px`;
//       tooltip.style.top = `${e.clientY - container.getBoundingClientRect().top + 12}px`;
//       tooltip.innerHTML = m.type === 'obstacle'
//         ? `<strong>${m.label}</strong><br>Clearance: ${m.clearance?.toFixed(2) ?? 'N/A'} m`
//         : `<strong>${m.label}</strong><br>Range: ${m.min}° – ${m.max}°`;
//       return;
//     }
//   }
//   tooltip.style.display = 'none';
// });

// renderer.domElement.addEventListener('mouseleave', () => {
//   tooltip.style.display = 'none';
// });

// // --- Resize ---
// window.addEventListener('resize', () => {
//   camera.aspect = w() / h();
//   camera.updateProjectionMatrix();
//   renderer.setSize(w(), h());
//   composer.setSize(w(), h());
//   labelRenderer.setSize(w(), h());
//   bloomPass.resolution.set(w(), h());
// });

// // --- Dashboard ---
// async function updateDashboard() {
//   try {
//     const bench = await (await fetch('/api/benchmark/latest')).json();
//     if (bench.metrics) {
//       document.getElementById('stats').innerHTML = `
//         <div class="stat-box"><div class="label">AGA</div><div class="value">${bench.metrics.aga?.toFixed(1)}%</div></div>
//         <div class="stat-box"><div class="label">Avg Trust</div><div class="value">${(bench.metrics.avg_trust * 100)?.toFixed(0)}%</div></div>
//         <div class="stat-box"><div class="label">Approved</div><div class="value">${bench.metrics.approved}</div></div>
//         <div class="stat-box"><div class="label">Rejected</div><div class="value">${bench.metrics.rejected}</div></div>
//       `;
//     }
//     if (bench.results) {
//       let html = '<table><tr><th>Task</th><th>Chaos</th><th>Result</th><th>Trust</th><th>Rec.</th></tr>';
//       bench.results.slice(0, 10).forEach(r => {
//         html += `<tr>
//           <td>${r.task_id}</td><td>${r.failure_mode}</td>
//           <td class="${r.approved ? 'status-ok' : 'status-fail'}">${r.approved ? '✅' : '❌'}</td>
//           <td>${(r.trust_score * 100).toFixed(0)}%</td><td>${r.recoveries}</td>
//         </tr>`;
//       });
//       html += '</table>';
//       document.getElementById('task-table').innerHTML = html;
//     }
//   } catch (_) {}

//   try {
//     const evidence = await (await fetch('/api/evidence/recent?limit=3')).json();
//     if (evidence.length) {
//       let html = '<h3>Recent Evidence</h3>';
//       evidence.forEach(e => {
//         html += `<div style="margin-bottom:10px;"><strong>${e.command?.substring(0, 50)}...</strong><br>
//         Trust: ${(e.trust_score * 100).toFixed(0)}%, Recovery: ${e.recovery_count}</div>`;
//       });
//       document.getElementById('evidence-panel').innerHTML = html;
//     }
//   } catch (_) {}
// }

// // --- Explain modal ---
// const explainBtn = document.getElementById('explainBtn');
// const modal = document.getElementById('explainModal');
// const closeBtn = document.querySelector('.close');
// explainBtn.addEventListener('click', () => { modal.style.display = 'block'; });
// closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });
// window.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });

// document.getElementById('explainContent').innerHTML = `
// <h2>CINT‑70: Embodied Interface Planning & Action‑Execution Assurance Benchmark</h2>
// <h3>Project Title</h3>
// <p>CINT‑70 – Graph‑Grounded Constraint Assurance for Safe Autonomous Robotics</p>
// <h3>Problem Statement</h3>
// <p>Large language models (LLMs) frequently hallucinate plausible but physically impossible robot plans – a phenomenon called <strong>action hallucination</strong>. In safety‑critical domains (space, disaster response), executing such plans can cause irreversible damage. Existing benchmarks evaluate task completion but ignore physical feasibility.</p>
// <h3>Motivation</h3>
// <p>As autonomous systems are deployed in high‑risk environments, a separate validation layer is essential to catch unsafe actions before execution. Our work is motivated by real NASA incident reports (LLIS), Mars rover operations, and ISS robotic arm constraints.</p>
// <h3>Objectives</h3>
// <ul>
//   <li>Detect action hallucinations by validating plans against a graph database of physical constraints.</li>
//   <li>Provide an <strong>Action Grounding Accuracy (AGA)</strong> metric.</li>
//   <li>Enable automatic recovery attempts via LangGraph cycles.</li>
//   <li>Produce fully auditable evidence trails for regulatory compliance.</li>
//   <li>Run entirely on consumer hardware (4 GB VRAM) with zero external API cost.</li>
// </ul>
// <h3>Existing System & Limitations</h3>
// <p>Current LLM‑based planners (e.g., GPT‑4, Claude) generate action sequences without verifying spatial constraints. Benchmarks like ALFRED and Habitat focus on task completion, not physical safety. There is no widely accepted standard for <em>assuring</em> that a plan respects real‑world physics.</p>
// <h3>Proposed Solution</h3>
// <p>CINT‑70 is a <strong>plan‑agnostic constraint assurance engine</strong>. It takes a plan from any source (LLM, human, algorithm) and validates it against a graph database (KùzuDB) that stores joint limits, obstacle positions, tool specifications, and thermal constraints. A forward‑kinematics engine and collision detector simulate each step. A dual‑memory RAG system combines static NASA documentation with a dynamic experience memory of past successes/failures.</p>
// <h3>Methodology</h3>
// <ol>
//   <li><strong>Data Ingestion:</strong> Structured knowledge derived from NASA PDS MEDA (3.2 M Mars temperature readings), ISS Reference Guides, NASA‑STD‑3001, LLIS failure reports, and Canadarm2 specs.</li>
//   <li><strong>Graph Construction:</strong> KùzuDB stores joints, obstacles, and tools as nodes with numeric constraints.</li>
//   <li><strong>Plan Generation:</strong> A quantised Qwen‑2.5‑1.5B model classifies the task (repair, inspect, etc.) and a symbolic library generates candidate paths.</li>
//   <li><strong>Validation:</strong> Each step is checked for joint limits, reachability, collision, and force limits via Cypher queries.</li>
//   <li><strong>Recovery:</strong> On failure, a LangGraph state machine retries with alternative coordinates up to 3 times.</li>
//   <li><strong>Evidence Logging:</strong> Every decision is saved with source citations.</li>
// </ol>
// <h3>Technologies Used</h3>
// <ul>
//   <li><strong>Languages:</strong> Python, JavaScript</li>
//   <li><strong>AI/ML:</strong> Hugging Face Transformers, Sentence‑Transformers, bitsandbytes (4‑bit quantisation)</li>
//   <li><strong>Graph DB:</strong> KùzuDB (embedded Cypher engine)</li>
//   <li><strong>Orchestration:</strong> LangGraph (cyclic state machine)</li>
//   <li><strong>Physics:</strong> Custom forward kinematics, collision detection (NumPy)</li>
//   <li><strong>Memory:</strong> SQLite + vector embeddings for experience retrieval</li>
//   <li><strong>Frontend:</strong> Three.js (3D globe), FastAPI, vanilla JavaScript</li>
// </ul>
// <h3>Expected Results</h3>
// <ul>
//   <li>Action Grounding Accuracy (AGA) of ~60% on 25 mixed‑difficulty scenarios (realistic, not 100%).</li>
//   <li>10/25 plans correctly rejected after exhausting recovery attempts.</li>
//   <li>Full evidence trail for every decision.</li>
//   <li>Demonstration that a small, local model can be effectively combined with symbolic planning for safety.</li>
// </ul>
// <h3>Applications</h3>
// <ul>
//   <li>Space robotics (ISS, Mars rovers)</li>
//   <li>Disaster response robots</li>
//   <li>Industrial manipulators</li>
//   <li>Regulatory compliance (EU AI Act)</li>
// </ul>
// <h3>Future Scope</h3>
// <ul>
//   <li>Integration with ROS 2 for real‑time robot control.</li>
//   <li>Reinforcement learning to optimise recovery strategies.</li>
//   <li>Multi‑agent constraint coordination.</li>
//   <li>Formal verification of the constraint graph.</li>
//   <li>Cloud‑based deployment for continuous learning across fleets.</li>
// </ul>
// `;

// // --- Init ---
// loadSceneData();
// updateDashboard();
// setInterval(updateDashboard, 10000);

// // --- Animation ---
// const clock = new THREE.Clock();
// function animate() {
//   requestAnimationFrame(animate);
//   const t = clock.getElapsedTime();

//   if (!introComplete) {
//     const elapsed = performance.now() - introStart;
//     if (elapsed < introDuration) {
//       const p = 1 - Math.pow(1 - elapsed / introDuration, 3);
//       camera.position.lerpVectors(startCam, endCam, p);
//       controls.autoRotate = false;
//     } else {
//       introComplete = true;
//       controls.autoRotate = true;
//     }
//   }

//   globe.rotation.y += 0.0008;
//   wireOverlay.rotation.y += 0.0008;
//   starfield.rotation.y += 0.00003;

//   pulseMeshes.forEach((glow, i) => {
//     const s = 1 + Math.sin(t * 2 + i * 0.7) * 0.25;
//     glow.scale.setScalar(s);
//     glow.material.opacity = 0.15 + Math.sin(t * 2 + i) * 0.1;
//   });

//   controls.update();
//   composer.render();
//   labelRenderer.render(scene, camera);
// }
// animate();
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { initTheme } from './theme.js';

const SCENE_COLORS = { dark: 0x04060a, light: 0xeef2f6 };
const GLOBE_R = 2;
const MARS_COLOR = 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/mars_1k_color.jpg';
const MARS_BUMP = 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/mars_1k_topo.jpg';

// --- Container ---
const container = document.getElementById('globe-container');
const w = () => container.clientWidth;
const h = () => container.clientHeight;

// --- Scene ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(SCENE_COLORS.dark);
scene.fog = new THREE.FogExp2(SCENE_COLORS.dark, 0.035);

const camera = new THREE.PerspectiveCamera(45, w() / h(), 0.1, 1000);
camera.position.set(0, 1, 12);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(w(), h());
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
container.appendChild(renderer.domElement);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloomPass = new UnrealBloomPass(new THREE.Vector2(w(), h()), 0.6, 0.4, 0.85);
composer.addPass(bloomPass);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(w(), h());
labelRenderer.domElement.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;';
container.appendChild(labelRenderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.minDistance = 4;
controls.maxDistance = 25;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.3;

// --- Starfield ---
const starGeo = new THREE.BufferGeometry();
const starCount = 3000;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount * 3; i++) starPos[i] = (Math.random() - 0.5) * 120;
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starfield = new THREE.Points(
  starGeo,
  new THREE.PointsMaterial({ color: 0xffffff, size: 0.08, transparent: true, opacity: 0.8 })
);
scene.add(starfield);

// --- Mars Globe ---
const textureLoader = new THREE.TextureLoader();
const marsTex = textureLoader.load(MARS_COLOR);
const bumpTex = textureLoader.load(MARS_BUMP);

const globe = new THREE.Mesh(
  new THREE.SphereGeometry(GLOBE_R, 64, 64),
  new THREE.MeshStandardMaterial({
    map: marsTex,
    bumpMap: bumpTex,
    bumpScale: 0.04,
    roughness: 0.9,
    metalness: 0.05,
  })
);
scene.add(globe);

// telemetry wireframe overlay — tuned to the design system's ice-blue accent
const wireOverlay = new THREE.Mesh(
  new THREE.SphereGeometry(GLOBE_R + 0.01, 32, 32),
  new THREE.MeshBasicMaterial({ color: 0x3ea6ff, wireframe: true, transparent: true, opacity: 0.06 })
);
scene.add(wireOverlay);

// atmosphere glow — matches the mars-rust accent used across the UI
const atmosphere = new THREE.Mesh(
  new THREE.SphereGeometry(GLOBE_R * 1.08, 64, 64),
  new THREE.MeshBasicMaterial({ color: 0xff6b35, transparent: true, opacity: 0.18, side: THREE.BackSide })
);
scene.add(atmosphere);

scene.add(new THREE.AmbientLight(0x404060, 0.6));
const sunLight = new THREE.DirectionalLight(0xffeedd, 1.2);
sunLight.position.set(8, 5, 10);
scene.add(sunLight);
const rimLight = new THREE.PointLight(0x3ea6ff, 0.5, 30);
rimLight.position.set(-6, 2, -4);
scene.add(rimLight);

// --- Markers & effects ---
const markers = [];
const pulseMeshes = [];

function toGlobeCoords(x, y, z) {
  const maxDist = 10;
  const v = new THREE.Vector3((x / maxDist) * GLOBE_R, (y / maxDist) * GLOBE_R, (z / maxDist) * GLOBE_R);
  return v.normalize().multiplyScalar(GLOBE_R + 0.05);
}

function addMarker(pos, color, label, meta = {}) {
  const group = new THREE.Group();
  group.position.copy(pos);

  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.06, 16, 16),
    new THREE.MeshBasicMaterial({ color })
  );
  group.add(core);

  const glow = new THREE.Mesh(
    new THREE.SphereGeometry(0.12, 16, 16),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.25 })
  );
  group.add(glow);
  pulseMeshes.push(glow);

  if (meta.danger) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.14, 0.18, 32),
      new THREE.MeshBasicMaterial({ color: 0xff3b4e, transparent: true, opacity: 0.6, side: THREE.DoubleSide })
    );
    ring.lookAt(pos.clone().multiplyScalar(2));
    group.add(ring);
  }

  scene.add(group);
  markers.push({ group, core, meta: { ...meta, label } });

  const div = document.createElement('div');
  div.className = 'marker-label';
  div.textContent = label;
  div.style.borderColor = meta.danger ? '#ff3b4e' : '#3ea6ff';
  const labelObj = new CSS2DObject(div);
  labelObj.position.set(0.15, 0.15, 0);
  group.add(labelObj);
}

function addJointArc(from, to, color = 0x3ea6ff) {
  const mid = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(GLOBE_R * 1.4);
  const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(curve.getPoints(32)),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 })
  );
  scene.add(line);
}

async function loadSceneData() {
  try {
    const obstacles = await (await fetch('/api/obstacles')).json();
    obstacles.forEach(o => {
      const pos = toGlobeCoords(o.x, o.y, o.z);
      const danger = o.clearance < 0.5;
      addMarker(pos, danger ? 0xff3b4e : 0x00e68a, o.name, {
        danger,
        clearance: o.clearance,
        type: 'obstacle',
      });
    });
  } catch (_) {}

  try {
    const joints = await (await fetch('/api/joints')).json();
    const jointPositions = [];
    joints.forEach((j, i) => {
      const angle = (i / joints.length) * Math.PI * 2;
      const pos = new THREE.Vector3(Math.cos(angle) * GLOBE_R, 0.2, Math.sin(angle) * GLOBE_R)
        .normalize()
        .multiplyScalar(GLOBE_R + 0.05);
      jointPositions.push(pos);
      addMarker(pos, 0x3ea6ff, j.name, { type: 'joint', min: j.min, max: j.max });
    });
    for (let i = 0; i < jointPositions.length; i++) {
      addJointArc(jointPositions[i], jointPositions[(i + 1) % jointPositions.length]);
    }
  } catch (_) {}
}

// --- Theme toggle (syncs 3D scene, persists across Home / Dashboard / Systems) ---
initTheme('themeToggle', (isLight) => {
  const bg = isLight ? SCENE_COLORS.light : SCENE_COLORS.dark;
  scene.background = new THREE.Color(bg);
  scene.fog.color = new THREE.Color(bg);
  starfield.material.opacity = isLight ? 0.15 : 0.8;
  atmosphere.material.opacity = isLight ? 0.08 : 0.18;
});

// --- Camera intro ---
const introStart = performance.now();
const introDuration = 2500;
const startCam = new THREE.Vector3(0, 8, 20);
const endCam = new THREE.Vector3(5, 2, 8);
let introComplete = false;

// --- Hover tooltip ---
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.createElement('div');
tooltip.className = 'globe-tooltip';
container.appendChild(tooltip);

renderer.domElement.addEventListener('mousemove', (e) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const cores = markers.map(m => m.core);
  const hits = raycaster.intersectObjects(cores);
  if (hits.length) {
    const hit = markers.find(m => m.core === hits[0].object);
    if (hit) {
      const m = hit.meta;
      tooltip.style.display = 'block';
      tooltip.style.left = `${e.clientX - container.getBoundingClientRect().left + 12}px`;
      tooltip.style.top = `${e.clientY - container.getBoundingClientRect().top + 12}px`;
      tooltip.innerHTML = m.type === 'obstacle'
        ? `<strong>${m.label}</strong><br>Clearance: ${m.clearance?.toFixed(2) ?? 'N/A'} m`
        : `<strong>${m.label}</strong><br>Range: ${m.min}° – ${m.max}°`;
      return;
    }
  }
  tooltip.style.display = 'none';
});

renderer.domElement.addEventListener('mouseleave', () => {
  tooltip.style.display = 'none';
});

// --- Resize ---
window.addEventListener('resize', () => {
  camera.aspect = w() / h();
  camera.updateProjectionMatrix();
  renderer.setSize(w(), h());
  composer.setSize(w(), h());
  labelRenderer.setSize(w(), h());
  bloomPass.resolution.set(w(), h());
});

// --- Data indicator: prove the graph data actually loaded ---
async function updateDataCounts() {
  try {
    const [obstacles, joints] = await Promise.all([
      (await fetch('/api/obstacles')).json(),
      (await fetch('/api/joints')).json(),
    ]);
    document.getElementById('obstacle-count').textContent = `${obstacles.length} obstacles`;
    document.getElementById('joint-count').textContent = `${joints.length} joints`;
  } catch (_) {}
}

// --- Experience memory stats ---
async function updateMemoryStats() {
  try {
    const stats = await (await fetch('/api/stats')).json();
    const container = document.getElementById('memory-stats');
    if (!container) return;
    container.innerHTML = `
      <div class="stat-box small"><div class="label">Experiences</div><div class="value">${stats.total_experiences ?? '—'}</div></div>
      <div class="stat-box small"><div class="label">Approval Rate</div><div class="value">${stats.approval_rate ?? '—'}</div></div>
      <div class="stat-box small"><div class="label">Failure Patterns</div><div class="value">${stats.failure_patterns ?? '—'}</div></div>
    `;
  } catch (_) {}
}

// --- Dashboard ---
async function updateDashboard() {
  try {
    const bench = await (await fetch('/api/benchmark/latest')).json();
    if (bench.metrics) {
      const aga = bench.metrics.aga ?? (bench.metrics.f1 != null ? bench.metrics.f1 * 100 : null);
      const benchmarkTimestamp = bench.timestamp ? new Date(bench.timestamp).toLocaleString() : '—';
      document.getElementById('benchmark-ts').textContent = benchmarkTimestamp;
      document.getElementById('stats').innerHTML = `
        <div class="stat-box"><div class="label">AGA</div><div class="value">${aga != null ? aga.toFixed(1) + '%' : '—'}</div></div>
        <div class="stat-box"><div class="label">Avg Trust</div><div class="value">${bench.metrics.avg_trust != null ? (bench.metrics.avg_trust * 100).toFixed(0) + '%' : '—'}</div></div>
        <div class="stat-box"><div class="label">Approved</div><div class="value">${bench.metrics.approved}</div></div>
        <div class="stat-box"><div class="label">Rejected</div><div class="value">${bench.metrics.rejected}</div></div>
      `;
    }
    if (bench.results) {
      let html = '<table><tr><th>Task</th><th>Chaos</th><th>Result</th><th>Trust</th><th>Rec.</th></tr>';
      bench.results.slice(0, 10).forEach((r, i) => {
        const trustScore = Number.isFinite(Number(r.trust_score)) ? Number(r.trust_score) : 0;
        html += `<tr data-row-index="${i}" data-task-id="${r.task_id ?? ''}">
          <td>${r.task_id}</td><td>${r.failure_mode}</td>
          <td class="${r.approved ? 'status-ok' : 'status-fail'}">${r.approved ? '✅' : '❌'}</td>
          <td>${(trustScore * 100).toFixed(0)}%</td><td>${r.recoveries ?? 0}</td>
        </tr>`;
      });
      html += '</table>';
      document.getElementById('task-table').innerHTML = html;

      // (re)wire row clicks — table is rebuilt every poll, so this must run each time
      document.querySelectorAll('#task-table tbody tr, #task-table table tr[data-row-index]').forEach(row => {
        row.addEventListener('click', () => showTestDetails(row.dataset.taskId, row.dataset.rowIndex));
      });
    }
  } catch (_) {}

  // initial evidence panel population only — after the user filters, loadFilteredEvidence owns this element
  if (!evidenceFilterEngaged) {
    try {
      const evidence = await (await fetch('/api/evidence/recent?limit=5')).json();
      renderEvidence(evidence);
    } catch (_) {}
  }
}

// --- Generic modal helpers (works for both #explainModal and #testDetailModal) ---
function openModal(modal) {
  modal.style.display = 'block';
  modal.setAttribute('aria-hidden', 'false');
}
function closeModalEl(modal) {
  modal.style.display = 'none';
  modal.setAttribute('aria-hidden', 'true');
}
document.querySelectorAll('.modal').forEach(modal => {
  modal.querySelector('.close')?.addEventListener('click', () => closeModalEl(modal));
  modal.addEventListener('click', (e) => { if (e.target === modal || e.target.classList.contains('modal-backdrop')) closeModalEl(modal); });
});
window.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  document.querySelectorAll('.modal').forEach(modal => {
    if (modal.style.display === 'block') closeModalEl(modal);
  });
});

// --- Explain modal ---
const explainBtn = document.getElementById('explainBtn');
const modal = document.getElementById('explainModal');
explainBtn.addEventListener('click', () => openModal(modal));

document.getElementById('explainContent').innerHTML = `
<h2>CINT‑70: Embodied Interface Planning & Action‑Execution Assurance Benchmark</h2>
<h3>Project Title</h3>
<p>CINT‑70 – Graph‑Grounded Constraint Assurance for Safe Autonomous Robotics</p>
<h3>Problem Statement</h3>
<p>Large language models (LLMs) frequently hallucinate plausible but physically impossible robot plans – a phenomenon called <strong>action hallucination</strong>. In safety‑critical domains (space, disaster response), executing such plans can cause irreversible damage. Existing benchmarks evaluate task completion but ignore physical feasibility.</p>
<h3>Motivation</h3>
<p>As autonomous systems are deployed in high‑risk environments, a separate validation layer is essential to catch unsafe actions before execution. Our work is motivated by real NASA incident reports (LLIS), Mars rover operations, and ISS robotic arm constraints.</p>
<h3>Objectives</h3>
<ul>
  <li>Detect action hallucinations by validating plans against a graph database of physical constraints.</li>
  <li>Provide an <strong>Action Grounding Accuracy (AGA)</strong> metric.</li>
  <li>Enable automatic recovery attempts via LangGraph cycles.</li>
  <li>Produce fully auditable evidence trails for regulatory compliance.</li>
  <li>Run entirely on consumer hardware (4 GB VRAM) with zero external API cost.</li>
</ul>
<h3>Existing System & Limitations</h3>
<p>Current LLM‑based planners (e.g., GPT‑4, Claude) generate action sequences without verifying spatial constraints. Benchmarks like ALFRED and Habitat focus on task completion, not physical safety. There is no widely accepted standard for <em>assuring</em> that a plan respects real‑world physics.</p>
<h3>Proposed Solution</h3>
<p>CINT‑70 is a <strong>plan‑agnostic constraint assurance engine</strong>. It takes a plan from any source (LLM, human, algorithm) and validates it against a graph database (KùzuDB) that stores joint limits, obstacle positions, tool specifications, and thermal constraints. A forward‑kinematics engine and collision detector simulate each step. A dual‑memory RAG system combines static NASA documentation with a dynamic experience memory of past successes/failures.</p>
<h3>Methodology</h3>
<ol>
  <li><strong>Data Ingestion:</strong> Structured knowledge derived from NASA PDS MEDA (3.2 M Mars temperature readings), ISS Reference Guides, NASA‑STD‑3001, LLIS failure reports, and Canadarm2 specs.</li>
  <li><strong>Graph Construction:</strong> KùzuDB stores joints, obstacles, and tools as nodes with numeric constraints.</li>
  <li><strong>Plan Generation:</strong> A quantised Qwen‑2.5‑1.5B model classifies the task (repair, inspect, etc.) and a symbolic library generates candidate paths.</li>
  <li><strong>Validation:</strong> Each step is checked for joint limits, reachability, collision, and force limits via Cypher queries.</li>
  <li><strong>Recovery:</strong> On failure, a LangGraph state machine retries with alternative coordinates up to 3 times.</li>
  <li><strong>Evidence Logging:</strong> Every decision is saved with source citations.</li>
</ol>
<h3>Technologies Used</h3>
<ul>
  <li><strong>Languages:</strong> Python, JavaScript</li>
  <li><strong>AI/ML:</strong> Hugging Face Transformers, Sentence‑Transformers, bitsandbytes (4‑bit quantisation)</li>
  <li><strong>Graph DB:</strong> KùzuDB (embedded Cypher engine)</li>
  <li><strong>Orchestration:</strong> LangGraph (cyclic state machine)</li>
  <li><strong>Physics:</strong> Custom forward kinematics, collision detection (NumPy)</li>
  <li><strong>Memory:</strong> SQLite + vector embeddings for experience retrieval</li>
  <li><strong>Frontend:</strong> Three.js (3D globe), FastAPI, vanilla JavaScript</li>
</ul>
<h3>Expected Results</h3>
<ul>
  <li>Action Grounding Accuracy (AGA) of ~60% on 25 mixed‑difficulty scenarios (realistic, not 100%).</li>
  <li>10/25 plans correctly rejected after exhausting recovery attempts.</li>
  <li>Full evidence trail for every decision.</li>
  <li>Demonstration that a small, local model can be effectively combined with symbolic planning for safety.</li>
</ul>
<h3>Applications</h3>
<ul>
  <li>Space robotics (ISS, Mars rovers)</li>
  <li>Disaster response robots</li>
  <li>Industrial manipulators</li>
  <li>Regulatory compliance (EU AI Act)</li>
</ul>
<h3>Future Scope</h3>
<ul>
  <li>Integration with ROS 2 for real‑time robot control.</li>
  <li>Reinforcement learning to optimise recovery strategies.</li>
  <li>Multi‑agent constraint coordination.</li>
  <li>Formal verification of the constraint graph.</li>
  <li>Cloud‑based deployment for continuous learning across fleets.</li>
</ul>
`;

// --- Test detail modal (bench-row click → most recent full run) ---
const testDetailModal = document.getElementById('testDetailModal');
const testDetailContent = document.getElementById('testDetailContent');

function trustBadgeClass(score) {
  if (score >= 0.7) return 'high';
  if (score < 0.4) return 'low';
  return '';
}

async function showTestDetails(taskId, resultIndex = null) {
  testDetailContent.innerHTML = '<p class="empty-state">Loading run details…</p>';
  openModal(testDetailModal);
  try {
    if (resultIndex === null) {
      testDetailContent.innerHTML = '<p class="empty-state">Select a benchmark row to view its details.</p>';
      return;
    }
    const response = await fetch(`/api/benchmark/result/${encodeURIComponent(resultIndex)}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const e = await response.json();
    if (e.error) {
      testDetailContent.innerHTML = `<p class="empty-state">${e.error}</p>`;
      return;
    }
    const trustPct = ((e.trust_score ?? 0) * 100).toFixed(0);
    testDetailContent.innerHTML = `
      <p class="empty-state" style="text-align:left;padding:0 0 10px;">Benchmark result: <strong>${taskId ?? 'Unnamed task'}</strong> · ${e.failure_mode ?? 'unknown failure mode'}</p>
      <h3>${e.task_id ?? 'Unnamed task'}</h3>
      <div class="run-meta">
        <span class="badge trust-badge ${trustBadgeClass(e.trust_score ?? 0)}">Trust ${trustPct}%</span>
        <span class="badge">${e.approved ? 'Approved' : 'Rejected'}</span>
        <span class="badge recovery-badge">Recoveries: ${e.recovery_count ?? 0}</span>
      </div>
      <h4>Plan Steps</h4>
      <ol>${(e.plan ?? []).map(s => `<li>${s.action ?? s}${s.rationale ? ' — ' + s.rationale : ''}</li>`).join('') || '<li>No plan steps recorded.</li>'}</ol>
      <h4>Violations</h4>
      ${(e.violation_details ?? []).length ? e.violation_details.map(v => `<div class="violation">${v.message ?? v}</div>`).join('') : '<p class="empty-state" style="text-align:left;padding:0;">None</p>'}
    `;
  } catch (_) {
    testDetailContent.innerHTML = '<p class="empty-state">Couldn\'t load run details.</p>';
  }
}

// --- Live pipeline trigger ---
const liveTestForm = document.getElementById('liveTestForm');
const liveCommandInput = document.getElementById('liveCommand');
const runLiveBtn = document.getElementById('runLiveBtn');
const liveResult = document.getElementById('liveResult');
const liveTestStatus = document.getElementById('live-test-status');

liveTestForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const cmd = liveCommandInput.value.trim();
  if (!cmd) return;

  runLiveBtn.disabled = true;
  runLiveBtn.textContent = 'Running…';
  liveTestStatus.textContent = 'executing';
  liveResult.innerHTML = '<p class="empty-state">Running plan through classifier → search → graph validation…</p>';

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const trustPct = ((data.trust_score ?? 0) * 100).toFixed(0);
    liveResult.innerHTML = `
      <div class="stats-grid">
        <div class="stat-box"><div class="label">Result</div><div class="value" style="font-size:1.05rem;color:${data.approved ? 'var(--green)' : 'var(--red)'}">${data.approved ? '✅ Approved' : '❌ Rejected'}</div></div>
        <div class="stat-box"><div class="label">Trust</div><div class="value">${trustPct}%</div></div>
        <div class="stat-box"><div class="label">Recoveries</div><div class="value">${data.recovery_count ?? 0}</div></div>
      </div>
      <h4>Violations</h4>
      ${(data.violations ?? []).length ? `<ul>${data.violations.map(v => `<li>${v.message ?? v}</li>`).join('')}</ul>` : '<p class="empty-state" style="text-align:left;padding:0;">None</p>'}
    `;
    liveTestStatus.textContent = data.approved ? 'approved' : 'rejected';
  } catch (err) {
    liveResult.innerHTML = `<p class="empty-state">Run failed: ${err.message}. Check that /api/run is wired up on the backend.</p>`;
    liveTestStatus.textContent = 'error';
  } finally {
    runLiveBtn.disabled = false;
    runLiveBtn.textContent = 'Execute';
  }
});

// --- Evidence trail: search & filter ---
const evidenceSearchInput = document.getElementById('evidenceSearch');
const evidenceTaskFilter = document.getElementById('evidenceTaskFilter');
const applyFilterBtn = document.getElementById('applyFilterBtn');
let evidenceFilterEngaged = false;
let evidenceDebounce = null;

function renderEvidence(evidence) {
  const panel = document.getElementById('evidence-panel');
  if (!evidence || !evidence.length) {
    panel.innerHTML = '<p class="empty-state">No evidence found.</p>';
    return;
  }
  panel.innerHTML = evidence.map(e => {
    const trustPct = ((e.trust_score ?? 0) * 100).toFixed(0);
    return `
      <div class="evidence-item" data-evidence-id="${e.filename ?? ''}">
        <strong title="${e.command ?? ''}">${(e.command ?? 'Unnamed command').substring(0, 60)}</strong>
        <span class="badge trust-badge ${trustBadgeClass(e.trust_score ?? 0)}">${trustPct}%</span>
        <span class="badge recovery-badge">Rec. ${e.recovery_count ?? 0}</span>
      </div>`;
  }).join('');

  panel.querySelectorAll('.evidence-item').forEach(item => {
    item.addEventListener('click', () => showTestDetails(null));
  });
}

async function loadFilteredEvidence() {
  evidenceFilterEngaged = true;
  const search = evidenceSearchInput.value.trim();
  const task = evidenceTaskFilter.value;
  const params = new URLSearchParams();
  if (task) params.append('task', task);
  if (search) params.append('search', search);
  params.append('limit', '20');

  document.getElementById('evidence-panel').innerHTML = '<div class="skeleton timeline-skeleton"></div>';
  try {
    const evidence = await (await fetch('/api/evidence?' + params.toString())).json();
    renderEvidence(evidence);
  } catch (_) {
    document.getElementById('evidence-panel').innerHTML = '<p class="empty-state">Couldn\'t load evidence. Check that /api/evidence is wired up on the backend.</p>';
  }
}

applyFilterBtn.addEventListener('click', loadFilteredEvidence);
evidenceTaskFilter.addEventListener('change', loadFilteredEvidence);
evidenceSearchInput.addEventListener('input', () => {
  clearTimeout(evidenceDebounce);
  evidenceDebounce = setTimeout(loadFilteredEvidence, 400);
});
evidenceSearchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') { e.preventDefault(); clearTimeout(evidenceDebounce); loadFilteredEvidence(); }
});

// --- Init ---
loadSceneData();
updateDashboard();
updateDataCounts();
updateMemoryStats();
setInterval(updateDashboard, 10000);
setInterval(updateMemoryStats, 10000);

// --- Animation ---
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();

  if (!introComplete) {
    const elapsed = performance.now() - introStart;
    if (elapsed < introDuration) {
      const p = 1 - Math.pow(1 - elapsed / introDuration, 3);
      camera.position.lerpVectors(startCam, endCam, p);
      controls.autoRotate = false;
    } else {
      introComplete = true;
      controls.autoRotate = true;
    }
  }

  globe.rotation.y += 0.0008;
  wireOverlay.rotation.y += 0.0008;
  starfield.rotation.y += 0.00003;

  pulseMeshes.forEach((glow, i) => {
    const s = 1 + Math.sin(t * 2 + i * 0.7) * 0.25;
    glow.scale.setScalar(s);
    glow.material.opacity = 0.15 + Math.sin(t * 2 + i) * 0.1;
  });

  controls.update();
  composer.render();
  labelRenderer.render(scene, camera);
}
animate();