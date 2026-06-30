/* ── Emily Pipeline Control ────────────────────────────────── */

const STAGE_ORDER = [
  'input_gateway', 'emotion_perception', 'dual_memory',
  'policy_mapper', 'prompt_constructor', 'reasoning_loop',
  'llm_generation', 'output_pruning',
];

const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
    return r.json();
  },
};

/* ── Toast ─────────────────────────────────────────────────── */
function showToast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}

/* ── Copy to clipboard ─────────────────────────────────────── */
function copyOutput(elId) {
  const el = document.getElementById(elId);
  if (!el || !el.textContent.trim()) return;
  navigator.clipboard.writeText(el.textContent).then(() => showToast('Copied'));
}

/* ── Time ago ──────────────────────────────────────────────── */
function timeAgo(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 5) return 'just now';
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/* ── Job persistence ───────────────────────────────────────── */
const JOB_STORAGE_KEY = 'emily-jobs';
const jobs = new Map();

function loadJobsFromStorage() {
  try {
    const raw = localStorage.getItem(JOB_STORAGE_KEY);
    if (raw) JSON.parse(raw).forEach(j => jobs.set(j.job_id, j));
  } catch { /* ignore */ }
}

function saveJobsToStorage() {
  localStorage.setItem(JOB_STORAGE_KEY, JSON.stringify([...jobs.values()]));
}

function addJob(job) {
  jobs.set(job.job_id, job);
  saveJobsToStorage();
  renderJobs();
  if (job.status === 'running') pollJob(job.job_id);
}

function updateJob(data) {
  const existing = jobs.get(data.job_id);
  if (existing) Object.assign(existing, data);
  else jobs.set(data.job_id, data);
  saveJobsToStorage();
  renderJobs();
}

async function syncJobsFromServer() {
  try {
    const r = await API.get('/api/jobs');
    if (r.jobs) {
      for (const sj of r.jobs) {
        const local = jobs.get(sj.job_id);
        if (!local) jobs.set(sj.job_id, sj);
        else if (sj.status !== 'running' && local.status === 'running') Object.assign(local, sj);
      }
      saveJobsToStorage();
      renderJobs();
      for (const [, j] of jobs) if (j.status === 'running') pollJob(j.job_id);
    }
  } catch { /* server might not be ready */ }
}

/* ── Job rendering ─────────────────────────────────────────── */
function renderJobs() {
  const el = document.getElementById('jobList');
  if (!el) return;
  if (!jobs.size) { el.innerHTML = '<div class="empty">No recent jobs</div>'; return; }
  el.innerHTML = '';
  const sorted = [...jobs.values()].sort((a, b) => {
    if (a.status === 'running' && b.status !== 'running') return -1;
    if (a.status !== 'running' && b.status === 'running') return 1;
    return (b.started_at || '').localeCompare(a.started_at || '');
  });
  for (const j of sorted) {
    const d = document.createElement('div');
    d.className = 'job-item';
    const dur = j.duration_ms ? ` (${j.duration_ms}ms)` : '';
    const ago = j.finished_at ? timeAgo(j.finished_at) : (j.started_at ? timeAgo(j.started_at) : '');
    d.innerHTML =
      `<span class="job-id">${j.job_id}</span>` +
      `<span class="job-kind">${formatJobKind(j.kind)}${dur}</span>` +
      `<span class="job-status ${j.status}">${j.status}</span>` +
      `<span class="job-time" style="font-size:0.6rem;color:var(--silver);min-width:50px;text-align:right">${ago}</span>`;
    el.appendChild(d);
  }
  document.getElementById('jobCount').textContent = jobs.size;
}

function formatJobKind(kind) {
  const map = { run_pipeline: 'Pipeline', prepare_dataset: 'Dataset', train_model: 'Training', test_suite: 'Tests' };
  return map[kind] || kind;
}

/* ── Stage progress ────────────────────────────────────────── */
function resetStageProgress() {
  document.querySelectorAll('.stage-progress').forEach(el => {
    el.classList.add('visible');
    el.querySelectorAll('.stage-step').forEach(s => {
      s.classList.remove('done', 'active', 'failed');
    });
    el.querySelectorAll('.stage-line').forEach(l => l.classList.remove('done'));
    const label = el.querySelector('.stage-label');
    if (label) label.textContent = 'Starting...';
  });
}

function updateStageProgress(currentStage, stagesCompleted) {
  document.querySelectorAll('.stage-progress').forEach(container => {
    container.classList.add('visible');
    const steps = container.querySelectorAll('.stage-step');
    const lines = container.querySelectorAll('.stage-line');
    steps.forEach(step => {
      const stage = step.dataset.stage;
      const idx = STAGE_ORDER.indexOf(stage);
      const doneIdx = (stagesCompleted || []).indexOf(stage);
      const currentIdx = STAGE_ORDER.indexOf(currentStage);
      step.classList.remove('done', 'active', 'failed');
      if (doneIdx !== -1 || (currentStage && idx < currentIdx)) {
        step.classList.add('done');
      } else if (stage === currentStage) {
        step.classList.add('active');
      }
    });
    lines.forEach((line, i) => {
      const stepBefore = steps[i];
      line.classList.toggle('done', stepBefore?.classList.contains('done'));
    });
    const label = container.querySelector('.stage-label');
    if (label && currentStage) {
      const name = currentStage.replace(/_/g, ' ');
      label.textContent = name.charAt(0).toUpperCase() + name.slice(1) + '...';
    }
  });
}

function markStageFailed() {
  document.querySelectorAll('.stage-progress').forEach(container => {
    const active = container.querySelector('.stage-step.active');
    if (active) active.classList.add('failed');
    const label = container.querySelector('.stage-label');
    if (label) label.textContent = 'Failed';
  });
}

/* ── Job polling ───────────────────────────────────────────── */
async function pollJob(id) {
  try {
    const r = await API.get(`/api/jobs/${id}`);
    updateJob(r);
    if (r.status === 'running') {
      if (r.current_stage) updateStageProgress(r.current_stage, r.stages_completed || []);
      setTimeout(() => pollJob(id), 500);
    } else {
      if (r.status === 'failed') markStageFailed();
      showJobResult(r);
      setTimeout(() => {
        document.querySelectorAll('.stage-progress').forEach(el => el.classList.remove('visible'));
      }, 3000);
    }
  } catch (e) {
    const j = jobs.get(id);
    if (j) { j.status = 'failed'; j.error = e.message; saveJobsToStorage(); renderJobs(); }
  }
}

function showJobResult(r) {
  const outEl =
    r.kind === 'run_pipeline' ? document.getElementById('pipelineOutput') || document.getElementById('quickOutput') :
    r.kind === 'prepare_dataset' ? document.getElementById('datasetOutput') :
    r.kind === 'train_model' ? document.getElementById('trainOutput') :
    r.kind === 'test_suite' ? document.getElementById('testOutput') : null;
  if (!outEl) return;
  if (r.status === 'completed') {
    if (r.kind === 'test_suite' && r.result_data) {
      const d = r.result_data;
      outEl.textContent = `Tests: ${d.passed}/${d.total} passed` +
        (d.failed ? ` | Failed: ${d.failed}` : '') +
        (d.errors ? ` | Errors: ${d.errors}` : '') +
        '\n\n' + (d.raw || r.output);
    } else {
      outEl.textContent = r.output;
    }
    outEl.classList.remove('running', 'error');
  } else {
    outEl.innerHTML = formatError(r);
    outEl.classList.remove('running');
    outEl.classList.add('error');
  }
}

/* ── Error formatting ──────────────────────────────────────── */
function formatError(job) {
  if (!job.error_detail) return `Error: ${job.error || 'Unknown error'}`;
  const d = job.error_detail;
  let html = `<span class="err-type">${d.error_type}</span>`;
  if (d.stage) html += ` <span class="err-stage">[${d.stage}]</span>`;
  if (d.part) html += `::<span class="err-part">${d.part}</span>`;
  html += `\n${d.detail}`;
  if (d.hint) html += `\nHint: ${d.hint}`;
  return html;
}

/* ── Toggle helper ────────────────────────────────────────── */
function initToggles() {
  document.querySelectorAll('.toggle[data-key]').forEach(el => {
    el.addEventListener('click', async () => {
      const isOn = el.classList.toggle('on');
      await API.post('/api/config', { [el.dataset.key]: isOn });
    });
  });
}

/* ── Config helpers ───────────────────────────────────────── */
async function loadConfig() {
  const r = await API.get('/api/config');
  if (r.error) return;
  document.querySelectorAll('[data-config-key]').forEach(el => {
    const key = el.dataset.configKey;
    if (r[key] !== undefined) {
      if (el.classList.contains('toggle')) el.classList.toggle('on', !!r[key]);
      else el.value = r[key];
    }
  });
  return r;
}

async function saveConfig() {
  const update = {};
  document.querySelectorAll('[data-config-key]').forEach(el => {
    const key = el.dataset.configKey;
    let val;
    if (el.classList.contains('toggle')) val = el.classList.contains('on');
    else {
      val = el.value;
      if (val === 'true') val = true;
      else if (val === 'false') val = false;
      else if (!isNaN(val) && val !== '') val = Number(val);
    }
    update[key] = val;
  });
  await API.post('/api/config', update);
}

/* ── Sidebar active state ─────────────────────────────────── */
function initNav() {
  const path = location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
}

/* ── Theme switching ──────────────────────────────────────── */
function getStoredTheme() { return localStorage.getItem('emily-theme') || 'minimalist'; }

function applyTheme(id) {
  document.body.className = '';
  if (id !== 'minimalist') document.body.classList.add('theme-' + id);
  localStorage.setItem('emily-theme', id);
  document.querySelectorAll('.theme-card').forEach(c => c.classList.toggle('selected', c.dataset.theme === id));
}

function initThemes() {
  applyTheme(getStoredTheme());
  document.querySelectorAll('.theme-card').forEach(c => c.addEventListener('click', () => applyTheme(c.dataset.theme)));
}

/* ── Init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initToggles();
  initThemes();
  loadJobsFromStorage();
  renderJobs();
  syncJobsFromServer();
});
