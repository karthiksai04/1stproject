/**
 * CartCompass-BI - Data Ingestion & Live Upload Controller (upload.html)
 * Manages file selection, client-side CSV preview, schema normalization,
 * multipart upload to Flask backend, and live dashboard state updates.
 */

let selectedFile = null;
let parsedPreviewRows = [];

document.addEventListener('DOMContentLoaded', async () => {
    setupSharedControls(refreshUploadPage);
    await initBackendHealth();
    setupUploadHandlers();
});

function refreshUploadPage() {
    // No-op for upload view
}

function setupUploadHandlers() {
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('dataset-file-input');
    const browseBtn = document.getElementById('btn-browse-file');
    const processBtn = document.getElementById('btn-process-upload');
    const resetBtn = document.getElementById('btn-reset-demo');

    if (!dropzone || !fileInput) return;

    // Trigger file chooser
    browseBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag & Drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('drag-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('drag-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });

    // Process & Update Dashboard button
    processBtn?.addEventListener('click', async () => {
        await executeUpload();
    });

    // Reset to benchmark button
    resetBtn?.addEventListener('click', async () => {
        if (confirm("Reset CartCompass-BI to the original 750-order verified benchmark dataset? This will regenerate all default charts and tables.")) {
            await executeResetToBenchmark();
        }
    });
}

function handleFileSelection(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
        alert("Please upload a .csv, .xlsx, or .xls file.");
        return;
    }

    selectedFile = file;

    // Update UI badge
    const badge = document.getElementById('file-badge');
    const badgeText = document.getElementById('file-badge-text');
    const processBtn = document.getElementById('btn-process-upload');

    if (badge && badgeText) {
        badge.style.display = 'inline-flex';
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        badgeText.textContent = `Selected: ${file.name} (${sizeMb > 0 ? sizeMb + ' MB' : (file.size / 1024).toFixed(1) + ' KB'})`;
    }

    if (processBtn) {
        processBtn.disabled = false;
        processBtn.style.opacity = '1';
        processBtn.classList.add('pulse-glow');
    }

    // Generate quick client-side preview if CSV
    if (ext === 'csv') {
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target.result;
            renderClientPreview(text);
        };
        reader.readAsText(file.slice(0, 50000)); // Read first 50KB for fast preview
    } else {
        const previewCard = document.getElementById('preview-card');
        if (previewCard) previewCard.style.display = 'none';
    }
}

function renderClientPreview(csvText) {
    const lines = csvText.trim().split(/\r\n|\n/).filter(line => line.trim().length > 0);
    if (lines.length < 2) return;

    const headers = parseCSVLine(lines[0]);
    const rows = lines.slice(1, 6).map(parseCSVLine);

    const thead = document.getElementById('preview-thead');
    const tbody = document.getElementById('preview-tbody');
    const previewCard = document.getElementById('preview-card');

    if (!thead || !tbody || !previewCard) return;

    thead.innerHTML = `<tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map(r => `<tr>${r.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('');

    previewCard.style.display = 'block';
}

function parseCSVLine(line) {
    const result = [];
    let insideQuotes = false;
    let entry = '';

    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            insideQuotes = !insideQuotes;
        } else if (char === ',' && !insideQuotes) {
            result.push(entry.trim());
            entry = '';
        } else {
            entry += char;
        }
    }
    result.push(entry.trim());
    return result;
}

async function executeUpload() {
    if (!selectedFile) return;

    const statusBox = document.getElementById('upload-status-box');
    const statusMsg = document.getElementById('status-message-text');
    const statusDetails = document.getElementById('status-details-text');
    const summaryGrid = document.getElementById('summary-stats-grid');
    const quickLinks = document.getElementById('quick-nav-links');
    const processBtn = document.getElementById('btn-process-upload');

    if (!statusBox) return;

    statusBox.className = 'upload-status-box active';
    statusBox.style.display = 'block';
    statusMsg.textContent = 'Processing dataset & updating SQLite engine...';
    statusMsg.style.color = 'var(--brand-orange)';
    statusDetails.textContent = 'Normalizing schema, inserting records, and re-running KPI formulations...';
    summaryGrid.style.display = 'none';
    quickLinks.style.display = 'none';

    if (processBtn) {
        processBtn.disabled = true;
        processBtn.textContent = 'Ingesting Data...';
    }

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (res.ok && data.status === 'success') {
            statusBox.className = 'upload-status-box active success';
            statusMsg.textContent = '✓ Dataset Ingestion Successful!';
            statusMsg.style.color = 'var(--accent-emerald)';
            statusDetails.textContent = data.message || 'All records ingested, SQLite tables refreshed, and publication charts regenerated.';

            // Populate summary stats
            const s = data.summary;
            if (s) {
                document.getElementById('stat-orders').textContent = formatNumber(s.total_orders);
                document.getElementById('stat-items').textContent = formatNumber(s.total_items);
                document.getElementById('stat-products').textContent = `${formatNumber(s.total_products)} Items (${s.categories.length} Verticals)`;
                document.getElementById('stat-net').textContent = formatCurrency(s.net_sales);
                summaryGrid.style.display = 'grid';
            }

            await refreshSidebarMetrics();
            quickLinks.style.display = 'flex';
        } else {
            throw new Error(data.message || 'Failed to process dataset.');
        }
    } catch (err) {
        statusBox.className = 'upload-status-box active error';
        statusMsg.textContent = '✕ Upload Processing Error';
        statusMsg.style.color = 'var(--accent-rose)';
        statusDetails.textContent = err.message || 'An error occurred while uploading. Please check CSV format.';
    } finally {
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                <span>Process &amp; Update Dashboard</span>
            `;
        }
    }
}

async function executeResetToBenchmark() {
    const statusBox = document.getElementById('upload-status-box');
    const statusMsg = document.getElementById('status-message-text');
    const statusDetails = document.getElementById('status-details-text');
    const summaryGrid = document.getElementById('summary-stats-grid');
    const quickLinks = document.getElementById('quick-nav-links');

    if (!statusBox) return;

    statusBox.className = 'upload-status-box active';
    statusBox.style.display = 'block';
    statusMsg.textContent = 'Resetting to verified benchmark dataset...';
    statusMsg.style.color = 'var(--brand-orange)';
    statusDetails.textContent = 'Regenerating 750 orders across 14 months and restoring default charts...';
    summaryGrid.style.display = 'none';
    quickLinks.style.display = 'none';

    try {
        const res = await fetch('/api/reset-demo', { method: 'POST' });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
            statusBox.className = 'upload-status-box active success';
            statusMsg.textContent = '✓ Benchmark Reset Completed!';
            statusMsg.style.color = 'var(--accent-emerald)';
            statusDetails.textContent = data.message;
            await refreshSidebarMetrics();
            quickLinks.style.display = 'flex';
        } else {
            throw new Error(data.message || 'Failed to reset benchmark data.');
        }
    } catch (err) {
        statusBox.className = 'upload-status-box active error';
        statusMsg.textContent = '✕ Benchmark Reset Error';
        statusMsg.style.color = 'var(--accent-rose)';
        statusDetails.textContent = err.message;
    }
}
