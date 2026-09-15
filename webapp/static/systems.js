import { initTheme } from './theme.js';
import { mountArchitectureDiagram, mountWorkflowDiagram } from './diagrams.js';

initTheme('themeToggle');

const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
let workflowMounted = false;

// architecture is the default open tab — mount immediately
mountArchitectureDiagram(document.getElementById('tab-arch'));

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    btn.classList.add('active');
    const target = document.getElementById(btn.dataset.tab);
    if (!target) return;
    target.classList.add('active');

    if (btn.dataset.tab === 'tab-workflow' && !workflowMounted) {
      mountWorkflowDiagram(target);
      workflowMounted = true;
    }
  });
});