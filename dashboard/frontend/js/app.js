const API_BASE = 'http://localhost:8000';

const state = {
  view: 'upload',
  datasets: [],
  selectedDataId: null,
  selectedFilename: '',
  chatHistory: [],
  currentTab: 'info',
};

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadPage = document.getElementById('uploadPage');
const dashboardLayout = document.getElementById('dashboardLayout');
const backBtn = document.getElementById('backBtn');
const datasetName = document.getElementById('datasetName');
const chatPanel = document.getElementById('chatPanel');
const chatToggleBtn = document.getElementById('chatToggleBtn');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const fileListContainer = document.getElementById('fileListContainer');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const tabInfo = document.getElementById('tabInfo');
const tabStats = document.getElementById('tabStats');
const tabPlots = document.getElementById('tabPlots');

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragenter', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('drag-over'); });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  if (files.length > 0 && files[0].name.endsWith('.csv')) {
    uploadCSV(files[0]);
  }
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    uploadCSV(fileInput.files[0]);
    fileInput.value = '';
  }
});

function showUploadPage() {
  state.view = 'upload';
  uploadPage.style.display = 'flex';
  dashboardLayout.classList.remove('active');
  backBtn.style.display = 'none';
  chatToggleBtn.style.display = 'none';
  datasetName.textContent = '';
  chatPanel.classList.remove('active');
  loadUploads();
}

function showDashboard(dataId, filename) {
  state.view = 'dashboard';
  state.selectedDataId = dataId;
  state.selectedFilename = filename;
  state.chatHistory = [];
  uploadPage.style.display = 'none';
  dashboardLayout.classList.add('active');
  backBtn.style.display = 'inline-block';
  chatToggleBtn.style.display = 'inline-block';
  datasetName.textContent = filename;
  loadDataInfo(dataId);
  loadStats(dataId);
  loadPlots(dataId);
  switchTab('info');
}

function switchTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.tab-btn[data-tab="${tab}"]`).classList.add('active');
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`).classList.add('active');
}

function toggleChat() {
  chatPanel.classList.toggle('active');
  if (chatPanel.classList.contains('active')) {
    setTimeout(() => { chatMessages.scrollTop = chatMessages.scrollHeight; }, 50);
  }
}

async function loadUploads() {
  try {
    const data = await listUploads();
    state.datasets = data.uploads || [];
    renderFileList();
  } catch (err) {
    fileListContainer.innerHTML = `<div class="error-message">Failed to load uploads: ${err.message}</div>`;
  }
}

function renderFileList() {
  if (state.datasets.length === 0) {
    fileListContainer.innerHTML = '<div class="empty-state"><span class="icon">&#128202;</span><p>No datasets uploaded yet</p></div>';
    return;
  }
  fileListContainer.innerHTML = state.datasets.map(d => `
    <div class="file-item" onclick="showDashboard('${d.data_id}', '${escapeHtml(d.filename)}')">
      <div class="file-info">
        <span class="file-icon">&#128202;</span>
        <div>
          <div class="file-name">${escapeHtml(d.filename)}</div>
          <div class="file-date">${d.uploaded_at ? new Date(d.uploaded_at).toLocaleString() : ''}</div>
        </div>
      </div>
      <button class="load-btn">Load</button>
    </div>
  `).join('');
}

async function uploadCSV(file) {
  uploadProgress.classList.add('active');
  progressFill.style.width = '0%';
  progressText.textContent = 'Uploading...';
  try {
    const data = await uploadCSVRequest(file, (pct) => {
      progressFill.style.width = `${pct}%`;
    });
    progressFill.style.width = '100%';
    progressText.textContent = 'Upload complete!';
    setTimeout(() => { uploadProgress.classList.remove('active'); }, 1200);
    await loadUploads();
  } catch (err) {
    progressText.textContent = `Error: ${err.message}`;
    setTimeout(() => { uploadProgress.classList.remove('active'); }, 3000);
  }
}

async function loadDataInfo(dataId) {
  tabInfo.innerHTML = '<div class="loading-overlay active"><div class="spinner large"></div><span>Loading info...</span></div>';
  try {
    const info = await getDataInfo(dataId);
    const missingCount = Object.values(info.missing || {}).reduce((a, b) => a + b, 0);
    tabInfo.innerHTML = `
      <div class="info-card">
        <h3>Dataset Summary</h3>
        <div class="info-grid">
          <div class="info-item">
            <div class="label">Filename</div>
            <div class="value">${escapeHtml(info.filename)}</div>
          </div>
          <div class="info-item">
            <div class="label">Rows</div>
            <div class="value">${info.rows.toLocaleString()}</div>
          </div>
          <div class="info-item">
            <div class="label">Columns</div>
            <div class="value">${info.columns.length}</div>
          </div>
          <div class="info-item">
            <div class="label">Missing Values</div>
            <div class="value ${missingCount > 0 ? 'missing' : ''}">${missingCount.toLocaleString()}</div>
          </div>
        </div>
      </div>
      <div class="info-card">
        <h3>Columns</h3>
        <div class="columns-list">
          ${info.columns.map(col => {
            const dtype = (info.dtypes && info.dtypes[col]) || 'unknown';
            const missing = (info.missing && info.missing[col]) || 0;
            return `<span class="column-tag">
              ${escapeHtml(col)}
              <span class="type-badge">${dtype}</span>
              ${missing > 0 ? `<span class="missing-badge">${missing} missing</span>` : ''}
            </span>`;
          }).join('')}
        </div>
      </div>
      <div class="info-card">
        <h3>Preview (First 5 Rows)</h3>
        <div class="stats-table-wrapper">
          <table class="stats-table">
            <thead><tr>${info.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr></thead>
            <tbody>
              ${(info.preview || []).map(row => `
                <tr>${info.columns.map(c => `<td>${row[c] !== null && row[c] !== undefined ? escapeHtml(String(row[c])) : '—'}</td>`).join('')}</tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    tabInfo.innerHTML = `<div class="error-message">Failed to load data info: ${err.message}</div>`;
  }
}

async function loadStats(dataId) {
  tabStats.innerHTML = '<div class="loading-overlay active"><div class="spinner large"></div><span>Loading statistics...</span></div>';
  try {
    const stats = await getStats(dataId);
    let html = '';
    const numeric = stats.numeric || {};
    const numericCols = Object.keys(numeric);
    if (numericCols.length > 0) {
      html += `
        <div class="stats-section">
          <h3>Numeric Columns</h3>
          <div class="stats-table-wrapper">
            <table class="stats-table">
              <thead><tr><th>Column</th><th>Mean</th><th>Median</th><th>Std</th><th>Min</th><th>Max</th><th>Q1</th><th>Q3</th></tr></thead>
              <tbody>
                ${numericCols.map(col => `
                  <tr>
                    <td><strong>${escapeHtml(col)}</strong></td>
                    <td>${formatNum(numeric[col].mean)}</td>
                    <td>${formatNum(numeric[col].median)}</td>
                    <td>${formatNum(numeric[col].std)}</td>
                    <td>${formatNum(numeric[col].min)}</td>
                    <td>${formatNum(numeric[col].max)}</td>
                    <td>${formatNum(numeric[col].q1)}</td>
                    <td>${formatNum(numeric[col].q3)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }
    const categorical = stats.categorical || {};
    const catCols = Object.keys(categorical);
    if (catCols.length > 0) {
      html += `
        <div class="stats-section">
          <h3>Categorical Columns</h3>
          <div class="stats-table-wrapper">
            <table class="stats-table">
              <thead><tr><th>Column</th><th>Unique Values</th><th>Missing</th><th>Top Values</th></tr></thead>
              <tbody>
                ${catCols.map(col => {
                  const cat = categorical[col];
                  const topVals = Object.entries(cat.top_values || {}).slice(0, 5)
                    .map(([k, v]) => `${escapeHtml(k)}: ${v}`).join(', ');
                  return `
                    <tr>
                      <td><strong>${escapeHtml(col)}</strong></td>
                      <td>${cat.unique_values}</td>
                      <td>${cat.missing || 0}</td>
                      <td>${topVals || '—'}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }
    if (!html) {
      html = '<div class="empty-state"><span class="icon">&#128200;</span><p>No statistics available</p></div>';
    }
    tabStats.innerHTML = html;
  } catch (err) {
    tabStats.innerHTML = `<div class="error-message">Failed to load statistics: ${err.message}</div>`;
  }
}

async function loadPlots(dataId) {
  tabPlots.innerHTML = '<div class="loading-overlay active"><div class="spinner large"></div><span>Loading plots...</span></div>';
  try {
    const plotsData = await getPlots(dataId);
    let html = '';
    const plots = plotsData.plots || [];
    if (plots.length > 0) {
      html += '<div class="plots-grid">';
      plots.forEach(p => {
        html += `
          <div class="plot-card">
            <div class="plot-header">
              <span class="plot-title">${escapeHtml(p.column)}</span>
              <span class="plot-type-badge">${escapeHtml(p.type)}</span>
            </div>
            <img class="plot-image" src="data:image/png;base64,${p.image_base64}" alt="${escapeHtml(p.description || p.column)}">
            ${p.description ? `<div class="plot-description">${escapeHtml(p.description)}</div>` : ''}
          </div>
        `;
      });
      html += '</div>';
    }
    if (plotsData.correlation_matrix_base64) {
      html += `
        <div class="corr-card">
          <div class="corr-header">Correlation Matrix</div>
          <img class="corr-image" src="data:image/png;base64,${plotsData.correlation_matrix_base64}" alt="Correlation Matrix">
        </div>
      `;
    }
    if (!html) {
      html = '<div class="empty-state"><span class="icon">&#128202;</span><p>No plots available</p></div>';
    }
    tabPlots.innerHTML = html;
  } catch (err) {
    tabPlots.innerHTML = `<div class="error-message">Failed to load plots: ${err.message}</div>`;
  }
}

async function sendChatMessage() {
  const msg = chatInput.value.trim();
  if (!msg || !state.selectedDataId) return;
  chatInput.value = '';
  sendBtn.disabled = true;
  renderChatMessages();
  const loadingEl = document.createElement('div');
  loadingEl.className = 'message loading';
  loadingEl.innerHTML = '<div class="spinner"></div><span>Thinking...</span>';
  chatMessages.appendChild(loadingEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  try {
    const result = await sendChatMessageRequest(state.selectedDataId, msg, state.chatHistory);
    chatMessages.removeChild(loadingEl);
    state.chatHistory = result.updated_history || state.chatHistory;
    renderChatMessages();
    if (result.plots && result.plots.length > 0) {
      result.plots.forEach(plotBase64 => {
        const imgMsg = document.createElement('div');
        imgMsg.className = 'message assistant';
        imgMsg.innerHTML = `<img class="inline-plot" src="data:image/png;base64,${plotBase64}" alt="Chat plot">`;
        chatMessages.appendChild(imgMsg);
      });
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  } catch (err) {
    if (loadingEl.parentNode) chatMessages.removeChild(loadingEl);
    const errMsg = document.createElement('div');
    errMsg.className = 'message assistant';
    errMsg.textContent = `Error: ${err.message}`;
    chatMessages.appendChild(errMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  sendBtn.disabled = false;
  chatInput.focus();
}

function renderChatMessages() {
  chatMessages.innerHTML = state.chatHistory.map(m => {
    if (m.role === 'user') {
      return `<div class="message user">${escapeHtml(m.content)}</div>`;
    }
    return `<div class="message assistant">${escapeHtml(m.content)}</div>`;
  }).join('');
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function uploadCSVRequest(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);
  const xhr = new XMLHttpRequest();
  return new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || xhr.statusText));
        } catch {
          reject(new Error(xhr.statusText || 'Upload failed'));
        }
      }
    });
    xhr.addEventListener('error', () => reject(new Error('Network error')));
    xhr.open('POST', `${API_BASE}/api/upload`);
    xhr.send(formData);
  });
}

async function getDataInfo(dataId) {
  const res = await fetch(`${API_BASE}/api/data/${dataId}/info`);
  if (!res.ok) { const e = await res.json().catch(() => {}); throw new Error((e && e.detail) || res.statusText); }
  return res.json();
}

async function getStats(dataId) {
  const res = await fetch(`${API_BASE}/api/data/${dataId}/stats`);
  if (!res.ok) { const e = await res.json().catch(() => {}); throw new Error((e && e.detail) || res.statusText); }
  return res.json();
}

async function getPlots(dataId, columns) {
  let url = `${API_BASE}/api/data/${dataId}/plots`;
  if (columns) url += `?columns=${encodeURIComponent(columns)}`;
  const res = await fetch(url);
  if (!res.ok) { const e = await res.json().catch(() => {}); throw new Error((e && e.detail) || res.statusText); }
  return res.json();
}

async function sendChatMessageRequest(dataId, message, history) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data_id: dataId, message, history }),
  });
  if (!res.ok) { const e = await res.json().catch(() => {}); throw new Error((e && e.detail) || res.statusText); }
  return res.json();
}

async function listUploads() {
  const res = await fetch(`${API_BASE}/api/uploads`);
  if (!res.ok) { const e = await res.json().catch(() => {}); throw new Error((e && e.detail) || res.statusText); }
  return res.json();
}

function formatNum(v) {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') {
    if (Number.isInteger(v)) return v.toLocaleString();
    return v.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  return v;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

loadUploads();
