/* ── Emily Pipeline Control ────────────────────────────────── */

const API = {
  async get(path) {
    const r = await fetch(path);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
};

/* ── Job tracking ─────────────────────────────────────────── */
const jobs = new Map();

function addJob(job) {
  jobs.set(job.job_id, job);
  renderJobs();
  pollJob(job.job_id);
}

function renderJobs() {
  const el = document.getElementById('jobList');
  if (!el) return;
  if (!jobs.size) {
    el.innerHTML = '<div class="empty">No recent jobs</div>';
    return;
  }
  el.innerHTML = '';
  for (const [id, j] of jobs) {
    const d = document.createElement('div');
    d.className = 'job-item';
    d.innerHTML =
      `<span class="job-id">${j.job_id}</span>` +
      `<span class="job-kind">${j.kind}</span>` +
      `<span class="job-status ${j.status}">${j.status}</span>`;
    el.appendChild(d);
  }
}

async function pollJob(id) {
  const r = await API.get(`/api/jobs/${id}`);
  jobs.set(id, { ...jobs.get(id), ...r });
  renderJobs();
  if (r.status === 'running') {
    setTimeout(() => pollJob(id), 800);
  } else {
    const target = r.kind;
    const outEl =
      target === 'run_pipeline' ? document.getElementById('pipelineOutput') :
      target === 'prepare_dataset' ? document.getElementById('datasetOutput') :
      target === 'train_model' ? document.getElementById('trainOutput') : null;
    if (outEl) {
      outEl.textContent = r.status === 'completed' ? r.output : r.error;
      outEl.classList.remove('running');
    }
  }
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
      if (el.classList.contains('toggle')) {
        el.classList.toggle('on', !!r[key]);
      } else {
        el.value = r[key];
      }
    }
  });
  return r;
}

async function saveConfig() {
  const update = {};
  document.querySelectorAll('[data-config-key]').forEach(el => {
    const key = el.dataset.configKey;
    let val;
    if (el.classList.contains('toggle')) {
      val = el.classList.contains('on');
    } else {
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
    const href = link.getAttribute('href');
    if (href === path || (path === '/' && href === '/')) {
      link.classList.add('active');
    }
  });
}

/* ── Init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initToggles();
});
