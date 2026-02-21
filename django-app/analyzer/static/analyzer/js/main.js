/* ─── ClauseGuard Main JS ─── */

// ── DRAG & DROP ──────────────────────────────────────────────────────────────
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

if (dropZone) {
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) submitPDF(file);
  });
}

if (fileInput) {
  fileInput.addEventListener('change', e => {
    if (e.target.files[0]) submitPDF(e.target.files[0]);
  });
}

// ── CHARACTER COUNT ───────────────────────────────────────────────────────────
const textarea = document.getElementById('contract-text');
const charCount = document.getElementById('char-count');

if (textarea && charCount) {
  textarea.addEventListener('input', () => {
    const len = textarea.value.length;
    charCount.textContent = `${len.toLocaleString()} character${len !== 1 ? 's' : ''}`;
  });
}

// ── SUBMIT PDF ────────────────────────────────────────────────────────────────
async function submitPDF(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showError('Please upload a PDF file.');
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showError('File size exceeds 10MB.');
    return;
  }

  showLoading();

  const formData = new FormData();
  formData.append('contract_pdf', file);
  formData.append('csrfmiddlewaretoken', CSRF_TOKEN);

  try {
    const res = await fetch(ANALYZE_PDF_URL, {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Analysis failed. Please try again.');
    }

    window.location.href = data.redirect;

  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

// ── SUBMIT TEXT ───────────────────────────────────────────────────────────────
async function submitText() {
  const text = document.getElementById('contract-text').value.trim();

  if (text.length < 100) {
    showError('Please paste at least 100 characters of contract text.');
    return;
  }

  showLoading();

  try {
    const res = await fetch(ANALYZE_TEXT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: JSON.stringify({ text }),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Analysis failed. Please try again.');
    }

    window.location.href = data.redirect;

  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

// ── LOADING ───────────────────────────────────────────────────────────────────
const LOADING_MESSAGES = [
  'Extracting contract text...',
  'Identifying parties and clauses...',
  'Scanning for risk patterns...',
  'Evaluating liability exposure...',
  'Checking for missing protections...',
  'Generating risk report...',
];

function showLoading() {
  hideError();
  const overlay = document.getElementById('loading-overlay');
  if (!overlay) return;

  overlay.style.display = 'flex';

  // Animate steps
  const steps = overlay.querySelectorAll('.loading-steps li');
  steps.forEach((step, i) => {
    const delay = parseInt(step.dataset.delay || i * 600);
    setTimeout(() => step.classList.add('active'), delay);
  });
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'none';
}

// ── ERRORS ────────────────────────────────────────────────────────────────────
function showError(msg) {
  const el = document.getElementById('error-box');
  if (!el) return;
  el.textContent = `⚠️ ${msg}`;
  el.style.display = 'block';
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
  const el = document.getElementById('error-box');
  if (el) el.style.display = 'none';
}

// ── RISK CARD TOGGLE ──────────────────────────────────────────────────────────
function toggleRisk(header) {
  const card = header.closest('.risk-card');
  if (card) card.classList.toggle('open');
}
