"""Page content fragments for the Emily control panel."""

STAGE_NAMES = {
    "input_gateway": "Input Gateway",
    "emotion_perception": "Emotion Engine",
    "dual_memory": "Memory",
    "policy_mapper": "Policy",
    "prompt_constructor": "Prompt",
    "reasoning_loop": "Reasoning",
    "llm_generation": "LLM",
    "output_pruning": "Safety",
}

STAGE_PROGRESS_HTML = """
<div class="stage-progress" id="stageProgress">
  <div class="stage-track">
    <div class="stage-step" data-stage="input_gateway"><div class="stage-dot"></div><span>Input</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="emotion_perception"><div class="stage-dot"></div><span>Emotion</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="dual_memory"><div class="stage-dot"></div><span>Memory</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="policy_mapper"><div class="stage-dot"></div><span>Policy</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="prompt_constructor"><div class="stage-dot"></div><span>Prompt</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="llm_generation"><div class="stage-dot"></div><span>LLM</span></div>
    <div class="stage-line"></div>
    <div class="stage-step" data-stage="output_pruning"><div class="stage-dot"></div><span>Safety</span></div>
  </div>
  <div class="stage-label" id="stageLabel"></div>
</div>
"""

OVERVIEW = """
<div class="page-header">
  <h2>Overview</h2>
  <p>Pipeline status and quick actions</p>
</div>

<div class="section">
  <div class="card">
    <div class="status-row">
      <div class="status-item">
        <div class="status-value"><span class="pulse-dot active"></span>Ready</div>
        <div class="status-label">Pipeline</div>
      </div>
      <div class="status-divider"></div>
      <div class="status-item">
        <div class="status-value" id="jobCount">0</div>
        <div class="status-label">Jobs run</div>
      </div>
      <div class="status-divider"></div>
      <div class="status-item">
        <div class="status-value" id="reasoningStatus">Off</div>
        <div class="status-label">Reasoning loop</div>
      </div>
      <div class="status-divider"></div>
      <div class="status-item">
        <div class="status-value" id="modelStatus">&mdash;</div>
        <div class="status-label">Emotion model</div>
      </div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-label">Quick run</div>
  <div class="card">
    <div class="field-row">
      <label class="field-label" for="quickInput">Say something to Emily</label>
      <textarea id="quickInput" rows="2" placeholder="I have been feeling lonely and anxious lately..."></textarea>
    </div>
    """ + STAGE_PROGRESS_HTML + """
    <div class="btn-group">
      <button class="btn btn-primary" id="quickRunBtn" onclick="quickRun()">Send</button>
      <button class="btn btn-ghost" onclick="document.getElementById('quickInput').value='I have been feeling lonely and anxious lately.'">Sample</button>
    </div>
    <div style="margin-top:12px">
      <div class="output" id="quickOutput"></div>
    </div>
  </div>
</div>

<div class="grid-2">
  <div class="section">
    <div class="section-label">Test suite</div>
    <div class="card">
      <p style="font-size:0.78rem;color:var(--slate);line-height:1.6;margin-bottom:12px">
        Run the full test suite to verify pipeline integrity.
      </p>
      <div class="btn-group">
        <button class="btn btn-primary" id="runTestsBtn" onclick="runTests()">Run tests</button>
      </div>
      <div style="margin-top:12px">
        <div class="output" id="testOutput"></div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-label">Recent jobs</div>
    <div class="card">
      <div id="jobList"><div class="empty">No recent jobs</div></div>
    </div>
  </div>
</div>

<script>
async function quickRun() {
  const input = document.getElementById('quickInput').value.trim();
  if (!input) return;
  const btn = document.getElementById('quickRunBtn');
  const out = document.getElementById('quickOutput');
  btn.disabled = true;
  out.textContent = 'Running pipeline...';
  out.classList.add('running');
  resetStageProgress();
  const r = await API.post('/api/pipeline/run', { user_input: input });
  btn.disabled = false;
  if (r.error) { out.textContent = r.error; out.classList.remove('running'); return; }
  addJob({ ...r, kind: 'run_pipeline' });
}
async function runTests() {
  const btn = document.getElementById('runTestsBtn');
  const out = document.getElementById('testOutput');
  btn.disabled = true;
  out.textContent = 'Running tests...';
  out.classList.add('running');
  const r = await API.post('/api/tests/run');
  btn.disabled = false;
  if (r.error) { out.textContent = r.error; out.classList.remove('running'); return; }
  addJob({ ...r, kind: 'test_suite' });
}
async function loadOverview() {
  const cfg = await API.get('/api/config');
  if (!cfg.error) {
    document.getElementById('reasoningStatus').textContent = cfg.reasoning_loop_enabled ? 'On' : 'Off';
  }
  try {
    const s = await fetch('/dataset/emotion_model.json');
    document.getElementById('modelStatus').textContent = s.ok ? 'Trained' : 'Not found';
  } catch { document.getElementById('modelStatus').textContent = '\u2014'; }
  document.getElementById('jobCount').textContent = jobs.size;
}
loadOverview();
</script>
"""

PIPELINE = """
<div class="page-header">
  <h2>Pipeline</h2>
  <p>Run input through the emotive AI pipeline</p>
</div>

<div class="section">
  <div class="card">
    <div class="field-row">
      <label class="field-label" for="pipelineInput">User input</label>
      <textarea id="pipelineInput" rows="4" placeholder="Type a message for Emily..." onkeydown="if(event.key==='Enter'&&event.ctrlKey)runPipeline()"></textarea>
      <div class="field-hint">Ctrl+Enter to run</div>
    </div>
    """ + STAGE_PROGRESS_HTML + """
    <div class="btn-group">
      <button class="btn btn-primary" id="runBtn" onclick="runPipeline()">Run pipeline</button>
      <button class="btn btn-ghost" onclick="document.getElementById('pipelineInput').value='I have been feeling lonely and anxious lately.'">Load sample</button>
      <button class="btn btn-ghost" onclick="copyOutput('pipelineOutput')">Copy output</button>
    </div>
    <div style="margin-top:16px">
      <label class="field-label">Response</label>
      <div class="output" id="pipelineOutput"></div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-label">Reasoning loop</div>
  <div class="card">
    <div class="toggle-row">
      <span class="toggle-label">Enable self-critique loop</span>
      <div class="toggle" data-key="reasoning_loop_enabled"></div>
    </div>
    <div class="toggle-row">
      <span class="toggle-label">Max iterations</span>
      <input type="number" data-config-key="reasoning_loop_max_iterations" value="2" min="1" max="5" style="width:60px;padding:6px 8px;text-align:center;border:1px solid var(--pearl);background:transparent;font-family:var(--font-body);font-size:0.82rem">
    </div>
    <div class="toggle-row">
      <span class="toggle-label">Activation threshold</span>
      <input type="number" data-config-key="reasoning_loop_activation_threshold" value="0.5" min="0" max="1" step="0.1" style="width:60px;padding:6px 8px;text-align:center;border:1px solid var(--pearl);background:transparent;font-family:var(--font-body);font-size:0.82rem">
    </div>
  </div>
</div>

<script>
async function runPipeline() {
  const input = document.getElementById('pipelineInput').value.trim();
  if (!input) return;
  const btn = document.getElementById('runBtn');
  const out = document.getElementById('pipelineOutput');
  btn.disabled = true;
  out.textContent = 'Running pipeline...';
  out.classList.add('running');
  resetStageProgress();
  const r = await API.post('/api/pipeline/run', { user_input: input });
  btn.disabled = false;
  if (r.error) { out.textContent = r.error; out.classList.remove('running'); return; }
  addJob({ ...r, kind: 'run_pipeline' });
}
loadConfig();
</script>
"""

TRAINING = """
<div class="page-header">
  <h2>Training</h2>
  <p>Dataset preparation and model training</p>
</div>

<div class="grid-2">
  <div class="section">
    <div class="section-label">Dataset</div>
    <div class="card">
      <p style="font-size:0.78rem;color:var(--slate);line-height:1.6;margin-bottom:16px">
        Fetches emotion datasets from Hugging Face and normalizes them into training-ready JSONL format.
      </p>
      <div class="btn-group">
        <button class="btn btn-primary" onclick="prepareDataset()">Prepare dataset</button>
      </div>
      <div style="margin-top:12px">
        <div class="output" id="datasetOutput"></div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-label">Model</div>
    <div class="card">
      <p style="font-size:0.78rem;color:var(--slate);line-height:1.6;margin-bottom:16px">
        Trains the NLP emotion classifier on the prepared dataset. Requires dataset/emotion_train.jsonl.
      </p>
      <div class="btn-group">
        <button class="btn btn-primary" onclick="trainModel()">Train model</button>
      </div>
      <div style="margin-top:12px">
        <div class="output" id="trainOutput"></div>
      </div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-label">Dataset info</div>
  <div class="card">
    <div id="datasetInfo" style="font-size:0.78rem;color:var(--slate);line-height:1.8">Loading...</div>
  </div>
</div>

<script>
async function prepareDataset() {
  const out = document.getElementById('datasetOutput');
  out.textContent = 'Preparing...';
  out.classList.add('running');
  const r = await API.post('/api/dataset/prepare');
  if (r.error) { out.textContent = r.error; out.classList.remove('running'); return; }
  addJob({ ...r, kind: 'prepare_dataset' });
}
async function trainModel() {
  const out = document.getElementById('trainOutput');
  out.textContent = 'Training...';
  out.classList.add('running');
  const r = await API.post('/api/model/train');
  if (r.error) { out.textContent = r.error; out.classList.remove('running'); return; }
  addJob({ ...r, kind: 'train_model' });
}
async function loadDatasetInfo() {
  const el = document.getElementById('datasetInfo');
  try {
    const s = await fetch('/dataset/dataset_summary.json');
    if (!s.ok) { el.textContent = 'No dataset found. Run preparation first.'; return; }
    const d = await s.json();
    let html = '';
    for (const [src, info] of Object.entries(d.sources || {})) {
      html += `<b>${src}</b> \u2014 train: ${info.train_rows}`;
      if (info.validation_rows) html += `, val: ${info.validation_rows}`;
      if (info.test_rows) html += `, test: ${info.test_rows}`;
      html += '<br>';
    }
    el.innerHTML = html || 'No sources recorded.';
  } catch { el.textContent = 'Could not load dataset info.'; }
}
loadDatasetInfo();
</script>
"""

CONFIG = """
<div class="page-header">
  <h2>Settings</h2>
  <p>Pipeline configuration and appearance</p>
</div>

<div class="section">
  <div class="section-label">Theme</div>
  <div class="card">
    <div class="theme-grid">
      <div class="theme-card" data-theme="minimalist">
        <div class="theme-name">Modern Minimalist</div>
        <div class="theme-swatches">
          <div class="theme-swatch" style="background:#36454f"></div>
          <div class="theme-swatch" style="background:#708090"></div>
          <div class="theme-swatch" style="background:#e8eaed"></div>
          <div class="theme-swatch" style="background:#f5f5f5"></div>
        </div>
      </div>
      <div class="theme-card" data-theme="sunset">
        <div class="theme-name">Sunset Boulevard</div>
        <div class="theme-swatches">
          <div class="theme-swatch" style="background:#264653"></div>
          <div class="theme-swatch" style="background:#e76f51"></div>
          <div class="theme-swatch" style="background:#f4a261"></div>
          <div class="theme-swatch" style="background:#e9c46a"></div>
        </div>
      </div>
      <div class="theme-card" data-theme="ocean">
        <div class="theme-name">Ocean Depths</div>
        <div class="theme-swatches">
          <div class="theme-swatch" style="background:#1a2332"></div>
          <div class="theme-swatch" style="background:#2d8b8b"></div>
          <div class="theme-swatch" style="background:#a8dadc"></div>
          <div class="theme-swatch" style="background:#f1faee"></div>
        </div>
      </div>
      <div class="theme-card" data-theme="galaxy">
        <div class="theme-name">Midnight Galaxy</div>
        <div class="theme-swatches">
          <div class="theme-swatch" style="background:#2b1e3e"></div>
          <div class="theme-swatch" style="background:#4a4e8f"></div>
          <div class="theme-swatch" style="background:#a490c2"></div>
          <div class="theme-swatch" style="background:#e6e6fa"></div>
        </div>
      </div>
      <div class="theme-card" data-theme="arctic">
        <div class="theme-name">Arctic Frost</div>
        <div class="theme-swatches">
          <div class="theme-swatch" style="background:#4a6fa5"></div>
          <div class="theme-swatch" style="background:#c0c0c0"></div>
          <div class="theme-swatch" style="background:#d4e4f7"></div>
          <div class="theme-swatch" style="background:#fafafa"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-label">Pipeline</div>
  <div class="card">
    <div class="config-grid" id="configGrid">
      <div class="empty full-width">Loading configuration...</div>
    </div>
  </div>
</div>

<div class="btn-group" style="margin-top:16px">
  <button class="btn btn-primary" onclick="saveConfig()">Save changes</button>
  <button class="btn btn-ghost" onclick="loadConfigPage()">Reload</button>
  <span id="configStatus" style="font-size:0.7rem;color:var(--slate);align-self:center;margin-left:8px"></span>
</div>

<script>
async function loadConfigPage() {
  const cfg = await API.get('/api/config');
  if (cfg.error) return;
  const grid = document.getElementById('configGrid');
  grid.innerHTML = '';
  for (const [key, val] of Object.entries(cfg)) {
    const field = document.createElement('div');
    field.className = 'config-field';
    const label = document.createElement('label');
    label.className = 'field-label';
    label.textContent = key.replace(/_/g, ' ');
    const input = document.createElement('input');
    input.type = typeof val === 'number' ? 'number' : 'text';
    input.value = val;
    input.dataset.configKey = key;
    if (typeof val === 'number' && val < 1 && val > 0) input.step = '0.1';
    field.appendChild(label);
    field.appendChild(input);
    grid.appendChild(field);
  }
}
async function saveConfig() {
  await saveConfig();
  const el = document.getElementById('configStatus');
  el.textContent = 'Saved';
  setTimeout(() => el.textContent = '', 2000);
}
loadConfigPage();
</script>
"""

LOGS = """
<div class="page-header">
  <h2>Logs</h2>
  <p>Telemetry from pipeline executions</p>
</div>

<div class="section">
  <div class="btn-group" style="margin-bottom:12px">
    <button class="btn btn-secondary" onclick="loadTelemetry()">Refresh</button>
    <button class="btn btn-ghost" onclick="document.getElementById('logOutput').textContent=''">Clear</button>
  </div>
  <div class="card">
    <div class="output" id="logOutput" style="max-height:500px;font-size:0.68rem"></div>
  </div>
</div>

<script>
async function loadTelemetry() {
  const el = document.getElementById('logOutput');
  el.textContent = 'Loading...';
  const r = await API.get('/api/telemetry?lines=100');
  if (!r.entries || !r.entries.length) {
    el.textContent = 'No telemetry entries yet.';
    return;
  }
  el.innerHTML = r.entries.map(e => {
    const ts = e.timestamp ? e.timestamp.split('T')[1]?.split('.')[0] || '' : '';
    const name = e.trace_name || '';
    const status = e.payload?.status || '';
    return `<div class="log-entry"><span class="log-time">${ts}</span><span class="log-stage">${name}</span> ${status}</div>`;
  }).join('');
  el.scrollTop = el.scrollHeight;
}
loadTelemetry();
</script>
"""
