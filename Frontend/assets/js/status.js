const STATUS_CONFIG = {
  API_BASE_URL: (() => {
    try {
      if (typeof window.API_BASE_URL === 'string' && /^https?:\/\//.test(window.API_BASE_URL)) {
        return window.API_BASE_URL.replace(/\/+$/,'');
      }
      const ls = localStorage.getItem('API_BASE_URL');
      if (ls && /^https?:\/\//.test(ls)) {
        return ls.replace(/\/+$/,'');
      }
      const meta = document.querySelector('meta[name="api-base"]');
      if (meta && /^https?:\/\//.test(meta.content || '')) {
        return (meta.content || '').replace(/\/+$/,'');
      }
    } catch {}
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') return 'http://127.0.0.1:8000';
    return window.location.origin;
  })(),
  REQUEST_TIMEOUT: 20000
};

function qs(id) {
  return document.getElementById(id);
}

function formatAmount(v) {
  const n = parseInt(v || 0, 10);
  return isNaN(n) ? '0' : n.toLocaleString();
}

function prettyWard(w) {
  return (w || '').replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function setText(id, val) {
  const el = qs(id);
  if (el) el.textContent = val;
}

async function fetchStatus(reference) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), STATUS_CONFIG.REQUEST_TIMEOUT);
  try {
   const res = await fetch(`${STATUS_CONFIG.API_BASE_URL}/api/bursary/applications/${encodeURIComponent(reference)}/`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal
    });
    clearTimeout(timer);

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const msg = data && data.error ? data.error : 'Application not found';
      throw new Error(msg);
    }

    const data = await res.json();
    return data;
  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

function renderResult(app) {
  setText('res-ref', app.reference_number);
  setText('res-name', app.full_name);
  setText('res-institution', app.institution_name);
  setText('res-amount', formatAmount(app.amount));
  setText('res-ward', prettyWard(app.ward));
  try {
    const d = new Date(app.submitted_at);
    setText('res-submitted', d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }));
  } catch {
    setText('res-submitted', app.submitted_at || '');
  }
  const statusEl = qs('res-status');
  if (statusEl) {
    statusEl.textContent = (app.status || '').toUpperCase();
    statusEl.style.color = app.status === 'approved' ? '#008000' : (app.status === 'rejected' ? '#bb0000' : '#ff9800');
  }

  qs('status-error').style.display = 'none';
  qs('status-result').style.display = 'block';
}

function showError(msg) {
  const el = qs('status-error');
  if (el) {
    el.textContent = msg;
    el.style.display = 'block';
  }
  const rs = qs('status-result');
  if (rs) rs.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = qs('check-status-btn');
  const input = qs('ref-input');

  // Allow direct link with ?ref=XYZ
  const params = new URLSearchParams(window.location.search);
  const initialRef = params.get('ref');
  if (initialRef && input) {
    input.value = initialRef;
    fetchStatus(initialRef)
      .then(renderResult)
      .catch(err => showError(err.message || 'Failed to fetch status'));
  }

  if (btn && input) {
    btn.addEventListener('click', async () => {
      const ref = (input.value || '').trim();
      if (!ref) {
        showError('Please enter your reference number');
        return;
      }
      qs('status-error').style.display = 'none';
      btn.disabled = true;
      const original = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
      try {
        const data = await fetchStatus(ref);
        renderResult(data);
      } catch (e) {
        showError(e.message || 'Failed to fetch status');
      }
      btn.disabled = false;
      btn.innerHTML = original;
    });
  }
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        btn && btn.click();
      }
    });
  }
});

