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

/* ── Notifications ─────────────────────────────────────────── */
function notify(msg, type) {
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' toast-' + type : '');
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3000);
}

function copyOutput(elId) {
  const el = document.getElementById(elId);
  if (!el || !el.textContent.trim()) return;
  navigator.clipboard.writeText(el.textContent).then(() => notify('Copied', 'ok'));
}

/* ── Time helpers ──────────────────────────────────────────── */
function timeAgo(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 5) return 'just now';
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function localTime(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
  catch { return ''; }
}

/* ── Job persistence ───────────────────────────────────────── */
const JOB_KEY = 'emily-jobs';
const jobs = new Map();

function loadJobs() {
  try {
    const raw = localStorage.getItem(JOB_KEY);
    if (raw) JSON.parse(raw).forEach(j => { if (j.status === 'running') j.status = 'stale'; jobs.set(j.job_id, j); });
  } catch {}
}

function saveJobs() {
  localStorage.setItem(JOB_KEY, JSON.stringify([...jobs.values()]));
}

function addJob(job) {
  jobs.set(job.job_id, job);
  saveJobs();
  renderJobs();
  if (job.status === 'running') pollJob(job.job_id);
}

function mergeJob(data) {
  const ex = jobs.get(data.job_id);
  if (ex) Object.assign(ex, data);
  else jobs.set(data.job_id, data);
  saveJobs();
  renderJobs();
}

async function syncFromServer() {
  try {
    const r = await API.get('/api/jobs');
    if (r.jobs) {
      for (const sj of r.jobs) {
        const local = jobs.get(sj.job_id);
        if (!local) jobs.set(sj.job_id, sj);
        else if (sj.status !== 'running' && local.status === 'running') Object.assign(local, sj);
      }
      saveJobs();
      renderJobs();
      for (const [, j] of jobs) if (j.status === 'running') pollJob(j.job_id);
    }
  } catch {}
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
    const time = localTime(j.finished_at || j.started_at);
    const ago = j.finished_at ? timeAgo(j.finished_at) : '';
    d.innerHTML =
      `<span class="job-id">${j.job_id}</span>` +
      `<span class="job-kind">${fmtKind(j.kind)}${dur}</span>` +
      `<span class="job-status ${j.status}">${j.status}</span>` +
      `<span class="job-time" style="font-size:0.6rem;color:var(--silver);min-width:80px;text-align:right">${time}${ago ? ' (' + ago + ')' : ''}</span>`;
    el.appendChild(d);
  }
  const cnt = document.getElementById('jobCount');
  if (cnt) cnt.textContent = jobs.size;
}

function fmtKind(k) {
  return { run_pipeline: 'Pipeline', prepare_dataset: 'Dataset', train_model: 'Training', test_suite: 'Tests' }[k] || k;
}

/* ── Stage progress ────────────────────────────────────────── */
function resetStages() {
  document.querySelectorAll('.stage-progress').forEach(el => {
    el.classList.add('visible');
    el.querySelectorAll('.stage-step').forEach(s => s.classList.remove('done', 'active', 'failed'));
    el.querySelectorAll('.stage-line').forEach(l => l.classList.remove('done'));
    const lbl = el.querySelector('.stage-label');
    if (lbl) lbl.textContent = 'Starting...';
  });
}

function updateStages(current, done) {
  document.querySelectorAll('.stage-progress').forEach(ct => {
    ct.classList.add('visible');
    const steps = ct.querySelectorAll('.stage-step');
    const lines = ct.querySelectorAll('.stage-line');
    steps.forEach(s => {
      const idx = STAGE_ORDER.indexOf(s.dataset.stage);
      const curIdx = STAGE_ORDER.indexOf(current);
      s.classList.remove('done', 'active', 'failed');
      if ((done || []).includes(s.dataset.stage) || (current && idx < curIdx)) s.classList.add('done');
      else if (s.dataset.stage === current) s.classList.add('active');
    });
    lines.forEach((l, i) => l.classList.toggle('done', steps[i]?.classList.contains('done')));
    const lbl = ct.querySelector('.stage-label');
    if (lbl && current) lbl.textContent = current.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) + '...';
  });
}

function markFailed() {
  document.querySelectorAll('.stage-progress').forEach(ct => {
    const a = ct.querySelector('.stage-step.active');
    if (a) a.classList.add('failed');
    const lbl = ct.querySelector('.stage-label');
    if (lbl) lbl.textContent = 'Failed';
  });
}

/* ── Job polling ───────────────────────────────────────────── */
async function pollJob(id) {
  try {
    const r = await API.get(`/api/jobs/${id}`);
    mergeJob(r);
    if (r.status === 'running') {
      if (r.current_stage) updateStages(r.current_stage, r.stages_completed || []);
      setTimeout(() => pollJob(id), 500);
    } else {
      if (r.status === 'failed') markFailed();
      showResult(r);
      setTimeout(() => document.querySelectorAll('.stage-progress').forEach(el => el.classList.remove('visible')), 3000);
    }
  } catch (e) {
    const j = jobs.get(id);
    if (j) { j.status = 'failed'; j.error = e.message; saveJobs(); renderJobs(); }
    notify('Poll failed: ' + e.message, 'err');
  }
}

function showResult(r) {
  // Find output element — try all possible IDs
  const el =
    document.getElementById('pipelineOutput') ||
    document.getElementById('quickOutput') ||
    document.getElementById('datasetOutput') ||
    document.getElementById('trainOutput') ||
    document.getElementById('testOutput');
  if (!el) return;

  if (r.status === 'completed') {
    if (r.kind === 'run_pipeline' && r.result_data && r.result_data.response) {
      el.innerHTML = fmtPipeline(r);
    } else if (r.kind === 'test_suite' && r.result_data && r.result_data.total) {
      const d = r.result_data;
      el.textContent = `Tests: ${d.passed}/${d.total} passed\n\n${d.raw || r.output}`;
    } else {
      el.textContent = r.output || 'Completed';
    }
    el.classList.remove('running', 'error');
    notify(`${fmtKind(r.kind)} completed${r.duration_ms ? ' in ' + r.duration_ms + 'ms' : ''}`, 'ok');
  } else {
    el.innerHTML = fmtError(r);
    el.classList.remove('running');
    el.classList.add('error');
    notify(`${fmtKind(r.kind)} failed`, 'err');
  }
}

function fmtPipeline(r) {
  const d = r.result_data;
  let h = '<div class="pipeline-result">';
  h += `<div class="pr-response">${esc(d.response || 'No response')}</div>`;
  if (d.raw_text && d.raw_text !== d.response) {
    h += `<div class="pr-section"><span class="pr-label">Raw (${d.pruning_method})</span><div class="pr-note" style="font-style:italic">${esc(d.raw_text)}</div></div>`;
  }
  if (d.safety_notes?.length) {
    h += '<div class="pr-section"><span class="pr-label">Safety</span>';
    d.safety_notes.forEach(n => h += `<div class="pr-note">${esc(n)}</div>`);
    h += '</div>';
  }
  if (d.traces?.length) {
    h += '<div class="pr-section"><span class="pr-label">Stages</span><div class="pr-stages">';
    d.traces.forEach(t => h += `<span class="pr-stage ${t.status}">${t.stage}</span>`);
    h += '</div></div>';
  }
  if (r.duration_ms) h += `<div style="font-size:0.6rem;color:var(--silver);margin-top:6px">${r.duration_ms}ms</div>`;
  h += '</div>';
  return h;
}

function fmtError(r) {
  if (!r.error_detail) return `Error: ${r.error || 'Unknown'}`;
  const d = r.error_detail;
  let h = `<span class="err-type">${d.error_type}</span>`;
  if (d.stage) h += ` <span class="err-stage">[${d.stage}]</span>`;
  if (d.part) h += `::<span class="err-part">${d.part}</span>`;
  h += `\n${d.detail}`;
  if (d.hint) h += `\nHint: ${d.hint}`;
  return h;
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

/* ── Config helpers ────────────────────────────────────────── */
async function loadConfig() {
  const r = await API.get('/api/config');
  if (r.error) return;
  document.querySelectorAll('[data-config-key]').forEach(el => {
    const k = el.dataset.configKey;
    if (r[k] !== undefined) {
      if (el.classList.contains('toggle')) el.classList.toggle('on', !!r[k]);
      else el.value = r[k];
    }
  });
  return r;
}

async function saveConfig() {
  const u = {};
  document.querySelectorAll('[data-config-key]').forEach(el => {
    const k = el.dataset.configKey;
    let v;
    if (el.classList.contains('toggle')) v = el.classList.contains('on');
    else { v = el.value; if (v === 'true') v = true; else if (v === 'false') v = false; else if (!isNaN(v) && v !== '') v = Number(v); }
    u[k] = v;
  });
  await API.post('/api/config', u);
}

function initToggles() {
  document.querySelectorAll('.toggle[data-key]').forEach(el => {
    el.addEventListener('click', async () => {
      el.classList.toggle('on');
      await API.post('/api/config', { [el.dataset.key]: el.classList.contains('on') });
    });
  });
}

/* ── Nav + Theme ───────────────────────────────────────────── */
function initNav() {
  const p = location.pathname;
  document.querySelectorAll('.nav-link').forEach(l => { if (l.getAttribute('href') === p) l.classList.add('active'); });
}

function getTheme() { return localStorage.getItem('emily-theme') || 'minimalist'; }

function applyTheme(id) {
  document.body.className = '';
  if (id !== 'minimalist') document.body.classList.add('theme-' + id);
  localStorage.setItem('emily-theme', id);
  document.querySelectorAll('.theme-card').forEach(c => c.classList.toggle('selected', c.dataset.theme === id));
}

function initThemes() {
  applyTheme(getTheme());
  document.querySelectorAll('.theme-card').forEach(c => c.addEventListener('click', () => applyTheme(c.dataset.theme)));
}

/* ── Init ──────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initToggles();
  initThemes();
  loadJobs();
  renderJobs();
  syncFromServer();
});
