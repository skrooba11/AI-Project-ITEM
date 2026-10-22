const $ = (sel) => document.querySelector(sel);

function formatBytes(value) {
  value = Number(value) || 0;
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(2)} ${units[i]}`;
}

function formatDate(ts) {
  if (!ts) return "-";
  const d = new Date(ts * 1000);
  if (isNaN(d.getTime())) return "-";
  return d.toISOString().slice(0, 10);
}

function showToast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { el.hidden = true; }, 2800);
}

// ------------------------------------------------------------- drive/state
let pollTimer = null;
let lastResult = null;

async function loadDrives() {
  const res = await fetch("/api/drives");
  const drives = await res.json();
  const sel = $("#driveSelect");
  sel.innerHTML = "";
  drives.forEach((d) => {
    const opt = document.createElement("option");
    opt.value = d.path;
    opt.textContent = d.label;
    sel.appendChild(opt);
  });
}

async function refreshStatus() {
  const res = await fetch("/api/analyze/status");
  const state = await res.json();
  applyState(state);
  return state;
}

function applyState(state) {
  const analyzeBtn = $("#analyzeBtn");
  const stopBtn = $("#stopBtn");
  const bar = $("#progressBar");
  const text = $("#progressText");

  if (state.status === "running" || state.status === "paused") {
    bar.hidden = false;
    stopBtn.hidden = false;
    analyzeBtn.textContent = state.status === "paused" ? "▶ 분석 재개" : "⏸ 분석 정지";
    analyzeBtn.disabled = false;
    text.textContent = state.status === "paused"
      ? `일시정지됨 - ${state.processed_files.toLocaleString()}개 파일 처리됨`
      : `분석 중... ${state.processed_files.toLocaleString()}개 파일 처리됨 · 초당 ${state.rate_per_sec}개 · 경과 ${state.elapsed_seconds}초`;
    if (!pollTimer) pollTimer = setInterval(refreshStatus, 1000);
  } else {
    bar.hidden = state.status !== "error";
    if (state.status === "error") text.textContent = `오류: ${state.error}`;
    stopBtn.hidden = true;
    analyzeBtn.textContent = "▶ 분석 시작";
    analyzeBtn.disabled = false;
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    if (state.result && state.result !== lastResult) {
      lastResult = state.result;
      renderResult(state.result);
      showToast(`분석 완료 (${state.result.total_files.toLocaleString()}개 파일, ${state.result.elapsed_seconds}초)`);
    }
    if (state.result) updateSidebarSizes(state.result);
  }
}

function renderResult(result) {
  const usedPercent = result.total ? Math.round((result.used / result.total) * 100) : 0;
  $("#storagePercent").textContent = `${usedPercent}%`;
  $("#storageLabel").textContent = "사용 중";
  $("#storageBytes").textContent = `${formatBytes(result.used)} / ${formatBytes(result.total)}`;
  $("#storageBar").style.width = `${usedPercent}%`;

  const grid = $("#typeGrid");
  grid.innerHTML = "";
  const entries = Object.entries(result.file_data).sort((a, b) => b[1].size - a[1].size);
  if (entries.length === 0) {
    grid.innerHTML = '<div class="muted">분류된 파일이 없습니다.</div>';
  }
  entries.forEach(([type, data]) => {
    const card = document.createElement("button");
    card.className = "type-card";
    card.innerHTML = `
      <div class="type-name">${type}</div>
      <div class="type-meta">${data.count.toLocaleString()}개 파일</div>
      <div class="type-size">${formatBytes(data.size)}</div>
    `;
    card.addEventListener("click", () => openTypeModal(type, data));
    grid.appendChild(card);
  });
}

function updateSidebarSizes(result) {
  $("#size-old").textContent = formatBytes(result.old_size || 0);
  $("#size-duplicates").textContent = formatBytes(result.dup_size || 0);
  $("#size-large").textContent = formatBytes(result.large_size || 0);
}

async function refreshTrashSize() {
  const res = await fetch("/api/trash");
  const data = await res.json();
  $("#size-trash").textContent = formatBytes(data.total_size || 0);
}

async function startAnalysis() {
  const drive = $("#driveSelect").value;
  if (!drive) { showToast("드라이브를 선택해주세요."); return; }
  const res = await fetch("/api/analyze", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ drive }),
  });
  const data = await res.json();
  if (data.error) { showToast(data.error); return; }
  lastResult = null;
  refreshStatus();
}

async function toggleAnalysis() {
  const state = await refreshStatus();
  if (state.status === "running") {
    await fetch("/api/analyze/pause", { method: "POST" });
  } else if (state.status === "paused") {
    await fetch("/api/analyze/resume", { method: "POST" });
  } else {
    await startAnalysis();
  }
  refreshStatus();
}

async function stopAnalysis() {
  await fetch("/api/analyze/stop", { method: "POST" });
  refreshStatus();
}

// -------------------------------------------------------------------modal
const modal = {
  overlay: null, mode: "normal", selected: new Set(), rows: [], fetcher: null,
};

function initModalRefs() {
  modal.overlay = $("#modalOverlay");
}

function closeModal() {
  modal.overlay.hidden = true;
  modal.selected.clear();
}

function renderModalRows(rows, mode) {
  const tbody = $("#modalTableBody");
  tbody.innerHTML = "";
  modal.rows = rows;
  modal.selected.clear();

  if (rows.length === 0) {
    $("#modalEmpty").hidden = false;
  } else {
    $("#modalEmpty").hidden = true;
  }

  let lastGroup = null;
  rows.forEach((row, idx) => {
    const tr = document.createElement("tr");
    if (mode === "duplicates" && row._group !== lastGroup) {
      tr.classList.add("group-sep");
      lastGroup = row._group;
    }
    const id = mode === "trash" ? row.trash_filename : row.path;
    tr.innerHTML = `
      <td><input type="checkbox" data-id="${idx}"></td>
      <td>${mode === "duplicates" ? `<span class="group-tag">#${row._group}</span>` : ""}${escapeHtml(row.name)}</td>
      <td class="col-path">${escapeHtml(mode === "trash" ? row.path : (row.path || "").replace(row.name, ""))}</td>
      <td class="col-size">${formatBytes(row.size)}</td>
      <td>${mode === "trash" ? (row.deleted_date || "-").slice(0, 10) : formatDate(row.modified)}</td>
    `;
    const cb = tr.querySelector("input");
    cb.addEventListener("change", () => {
      if (cb.checked) modal.selected.add(idx); else modal.selected.delete(idx);
      updateSelectionInfo();
    });
    tbody.appendChild(tr);
  });
  updateSelectionInfo();
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

function updateSelectionInfo() {
  const count = modal.selected.size;
  let size = 0;
  modal.selected.forEach((idx) => { size += modal.rows[idx].size; });
  $("#modalSelectionInfo").textContent = count ? `선택됨: ${count}개 · ${formatBytes(size)}` : "";
}

function selectAllRows() {
  modal.rows.forEach((_, idx) => modal.selected.add(idx));
  document.querySelectorAll("#modalTableBody input[type=checkbox]").forEach((cb) => (cb.checked = true));
  updateSelectionInfo();
}

function deselectAllRows() {
  modal.selected.clear();
  document.querySelectorAll("#modalTableBody input[type=checkbox]").forEach((cb) => (cb.checked = false));
  updateSelectionInfo();
}

function selectDuplicatesOnly() {
  modal.selected.clear();
  let lastGroup = null;
  modal.rows.forEach((row, idx) => {
    const cb = document.querySelector(`#modalTableBody input[data-id="${idx}"]`);
    if (row._group !== lastGroup) {
      lastGroup = row._group;
      cb.checked = false;
    } else {
      cb.checked = true;
      modal.selected.add(idx);
    }
  });
  updateSelectionInfo();
}

async function openTypeModal(type, data) {
  const res = await fetch(`/api/files/type/${encodeURIComponent(type)}`);
  const json = await res.json();
  openGenericModal(type, `${json.count.toLocaleString()}개 파일 · ${formatBytes(json.size)}`, json.files, "normal");
}

async function openOldModal() {
  const res = await fetch("/api/files/old");
  const json = await res.json();
  openGenericModal("사용하지 않는 파일", "지난 1년간 수정되지 않은 파일", json.files, "normal");
}

async function openLargeModal() {
  const res = await fetch("/api/files/large");
  const json = await res.json();
  openGenericModal("용량이 큰 파일", "1GB보다 큰 파일", json.files, "normal");
}

async function openDuplicatesModal() {
  const res = await fetch("/api/files/duplicates");
  const json = await res.json();
  const rows = [];
  json.groups.forEach((g) => {
    g.files.forEach((f) => rows.push({ ...f, _group: g.group }));
  });
  openGenericModal(
    "중복 파일",
    `${json.groups.length}개 그룹 · 절약 가능 ${formatBytes(json.saveable_size)}`,
    rows, "duplicates"
  );
}

async function openTrashModal() {
  const res = await fetch("/api/trash");
  const json = await res.json();
  openGenericModal("휴지통", `${json.files.length}개 파일 · ${formatBytes(json.total_size)}`, json.files, "trash");
}

function openGenericModal(title, subtitle, rows, mode) {
  modal.mode = mode;
  $("#modalTitle").textContent = title;
  $("#modalSubtitle").textContent = subtitle;
  $("#modalSelectDupOnly").hidden = mode !== "duplicates";
  $("#modalSecondaryAction").hidden = mode !== "trash";
  $("#modalPrimaryAction").textContent = mode === "trash" ? "선택 복원" : "선택 삭제";
  $("#modalPrimaryAction").className = mode === "trash" ? "btn btn-primary btn-sm" : "btn btn-danger btn-sm";
  renderModalRows(rows, mode);
  modal.overlay.hidden = false;
}

async function handlePrimaryAction() {
  if (modal.selected.size === 0) { showToast("선택된 항목이 없습니다."); return; }
  const items = [...modal.selected].map((idx) => modal.rows[idx]);

  if (modal.mode === "trash") {
    if (!confirm(`${items.length}개 파일을 복원하시겠습니까?`)) return;
    const res = await fetch("/api/restore", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trash_filenames: items.map((i) => i.trash_filename) }),
    });
    const data = await res.json();
    showToast(`${data.restored}개 파일을 복원했습니다.`);
    openTrashModal();
    refreshTrashSize();
  } else {
    if (!confirm(`${items.length}개 파일을 휴지통으로 이동하시겠습니까?`)) return;
    const res = await fetch("/api/delete", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths: items.map((i) => i.path) }),
    });
    const data = await res.json();
    showToast(`${data.moved}개 파일을 휴지통으로 이동했습니다.`);
    closeModal();
    refreshTrashSize();
    refreshStatus();
  }
}

async function handleSecondaryAction() {
  if (modal.mode !== "trash" || modal.selected.size === 0) { showToast("선택된 항목이 없습니다."); return; }
  const items = [...modal.selected].map((idx) => modal.rows[idx]);
  if (!confirm(`${items.length}개 파일을 휴지통에서 완전히(영구) 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return;
  const res = await fetch("/api/trash/purge", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trash_filenames: items.map((i) => i.trash_filename) }),
  });
  const data = await res.json();
  showToast(`${data.purged}개 파일을 영구 삭제했습니다.`);
  openTrashModal();
  refreshTrashSize();
}

async function showHistory() {
  const res = await fetch("/api/history");
  const history = await res.json();
  const rows = [];
  history.forEach((h, hi) => {
    h.files.forEach((f) => rows.push({
      name: f.name, path: `${h.operation_type} · ${new Date(h.timestamp).toLocaleString()}`,
      size: f.size, modified: null,
    }));
  });
  $("#modalSelectDupOnly").hidden = true;
  $("#modalSecondaryAction").hidden = true;
  $("#modalPrimaryAction").hidden = true;
  $("#modalSelectAll").hidden = true;
  $("#modalDeselectAll").hidden = true;
  modal.mode = "history";
  $("#modalTitle").textContent = "최근 삭제 이력";
  $("#modalSubtitle").textContent = `${history.length}건`;
  renderModalRows(rows, "history");
  modal.overlay.hidden = false;
}

function resetModalToolbarVisibility() {
  $("#modalPrimaryAction").hidden = false;
  $("#modalSelectAll").hidden = false;
  $("#modalDeselectAll").hidden = false;
}

// --------------------------------------------------------------------init
document.addEventListener("DOMContentLoaded", async () => {
  initModalRefs();
  await loadDrives();
  await refreshStatus();
  refreshTrashSize();

  $("#analyzeBtn").addEventListener("click", toggleAnalysis);
  $("#stopBtn").addEventListener("click", stopAnalysis);

  document.querySelectorAll(".action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.dataset.action;
      resetModalToolbarVisibility();
      if (action === "trash") openTrashModal();
      else if (action === "old") openOldModal();
      else if (action === "duplicates") openDuplicatesModal();
      else if (action === "large") openLargeModal();
    });
  });

  $("#modalClose").addEventListener("click", closeModal);
  $("#modalOverlay").addEventListener("click", (e) => { if (e.target.id === "modalOverlay") closeModal(); });
  $("#modalSelectAll").addEventListener("click", selectAllRows);
  $("#modalDeselectAll").addEventListener("click", deselectAllRows);
  $("#modalSelectDupOnly").addEventListener("click", selectDuplicatesOnly);
  $("#modalPrimaryAction").addEventListener("click", handlePrimaryAction);
  $("#modalSecondaryAction").addEventListener("click", handleSecondaryAction);

  $("#reportBtn").addEventListener("click", () => { window.location.href = "/api/report"; });
  $("#historyBtn").addEventListener("click", () => { resetModalToolbarVisibility(); showHistory(); });
});
