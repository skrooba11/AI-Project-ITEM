"use strict";

// ============================================================
// 전역 상태
// ============================================================
const state = {
  meta: { categories: [], category_map: {}, codes: [] },
  filterMode: "today",
  sortReverse: false,
  logs: [],
  selectedLogIds: new Set(),
  favorites: {},
  todos: [],
  todoSort: "created_date",
  todoSortReverse: false,
  selectedTodoIds: new Set(),
  activeWork: null,       // {code, mk_number, category, task}
  workStartEpoch: null,   // ms
  timerHandle: null,
  editingLogId: null,     // null=추가모드, 있으면 편집모드
  editingFavNum: null,
  editingTodoId: null,
};

const MK_TYPING_RE = /^(\d{5})([mtr])$/i;
const MK_SUFFIX_SOURCE_RE = /^\d{5}[MTRmtr]?$/;

// ============================================================
// 공용 유틸
// ============================================================
function $(id) { return document.getElementById(id); }

async function api(path, method = "GET", body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  return { ok: res.ok, status: res.status, data };
}

function showAlert(message) {
  return new Promise((resolve) => {
    $("alert-message").textContent = message;
    $("alert-modal").classList.remove("hidden");
    const handler = () => {
      $("alert-modal").classList.add("hidden");
      $("alert-ok").removeEventListener("click", handler);
      resolve();
    };
    $("alert-ok").addEventListener("click", handler);
  });
}

function showConfirm(message) {
  return new Promise((resolve) => {
    $("confirm-message").textContent = message;
    $("confirm-modal").classList.remove("hidden");
    const okHandler = () => { cleanup(); resolve(true); };
    const cancelHandler = () => { cleanup(); resolve(false); };
    function cleanup() {
      $("confirm-modal").classList.add("hidden");
      $("confirm-ok").removeEventListener("click", okHandler);
      $("confirm-cancel").removeEventListener("click", cancelHandler);
    }
    $("confirm-ok").addEventListener("click", okHandler);
    $("confirm-cancel").addEventListener("click", cancelHandler);
  });
}

function closeAllOverlaysExceptLogin() {
  document.querySelectorAll(".overlay").forEach((el) => {
    if (el.id !== "login-overlay") el.classList.add("hidden");
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAllOverlaysExceptLogin();
});

// ============================================================
// MK번호 관련 (자동 대문자 변환 / M,T,R 버튼)
// ============================================================
function normalizeMkLive(inputEl) {
  const cur = inputEl.value;
  const m = cur.match(MK_TYPING_RE);
  if (m) {
    const newVal = m[1] + m[2].toUpperCase();
    if (newVal !== cur) inputEl.value = newVal;
  }
}

function applyMkSuffix(inputEl, suffix) {
  const cur = inputEl.value.trim();
  if (MK_SUFFIX_SOURCE_RE.test(cur)) {
    const numberPart = cur.slice(0, 5);
    if (numberPart.length === 5) {
      inputEl.value = numberPart + suffix;
      return true;
    }
  }
  showAlert("MK번호는 숫자 5자리만 입력한 후 M/T/R 버튼을 클릭해주세요.\n예: 25001 입력 후 M 버튼 클릭");
  return false;
}

function wireMkGroup(inputEl, buttonSelector) {
  inputEl.addEventListener("input", () => normalizeMkLive(inputEl));
  document.querySelectorAll(buttonSelector).forEach((btn) => {
    btn.addEventListener("click", () => {
      const suffix = btn.dataset.suffix || btn.dataset.lmSuffix || btn.dataset.favSuffix || btn.dataset.todoSuffix;
      applyMkSuffix(inputEl, suffix);
    });
  });
}

// ============================================================
// 초기 로그인 체크
// ============================================================
async function init() {
  const { data } = await api("/api/me");
  if (data && data.logged_in) {
    $("user-name-label").textContent = data.name + " 님";
    $("login-overlay").classList.add("hidden");
    $("app").classList.remove("hidden");
    await bootstrapApp();
  } else {
    $("login-overlay").classList.remove("hidden");
  }
}

$("login-btn").addEventListener("click", doLogin);
$("login-name").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });

async function doLogin() {
  const name = $("login-name").value.trim();
  $("login-error").textContent = "";
  if (!name) { $("login-error").textContent = "이름을 입력해주세요."; return; }
  const { ok, data } = await api("/api/login", "POST", { name });
  if (!ok) { $("login-error").textContent = (data && data.error) || "로그인 실패"; return; }
  $("user-name-label").textContent = data.name + " 님";
  $("login-overlay").classList.add("hidden");
  $("app").classList.remove("hidden");
  await bootstrapApp();
}

$("logout-btn").addEventListener("click", async () => {
  const ok = await showConfirm("사용자를 변경하시겠습니까? (진행 중인 업무는 저장되지 않습니다)");
  if (!ok) return;
  await api("/api/logout", "POST");
  stopTimer();
  location.reload();
});

// ============================================================
// 부트스트랩
// ============================================================
async function bootstrapApp() {
  const metaRes = await api("/api/meta");
  state.meta = metaRes.data;
  populateCategoryList();
  populateCodeSelects();
  buildFavoritesGrid();

  startClock();
  await refreshWorkState();
  await refreshLogs();
  await refreshFavorites();
  await refreshTodos();
}

function populateCategoryList() {
  const dl = $("category-list");
  dl.innerHTML = "";
  state.meta.categories.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    dl.appendChild(opt);
  });
}

function populateCodeSelects() {
  document.querySelectorAll("select#code-select, select#lm-code, select#fav-code, select#todo-code").forEach((sel) => {
    const keep = sel.querySelector("option[value='']");
    sel.innerHTML = "";
    if (keep) sel.appendChild(keep.cloneNode(true));
    else sel.appendChild(new Option("", ""));
    state.meta.codes.forEach((code) => sel.appendChild(new Option(code, code)));
  });
}

function startClock() {
  const el = $("current-time");
  function tick() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    el.textContent = `현재시간: ${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  }
  tick();
  setInterval(tick, 1000);
}

// ============================================================
// 공정명 <-> 작업코드 자동 연동
// ============================================================
function wireCategoryCodeSync(categoryEl, codeEl) {
  const sync = () => {
    const val = categoryEl.value.trim();
    if (val && state.meta.category_map[val]) {
      codeEl.value = state.meta.category_map[val];
    }
  };
  categoryEl.addEventListener("input", sync);
  categoryEl.addEventListener("change", sync);
  categoryEl.addEventListener("blur", sync);
}

// ============================================================
// 진행중인 업무 (START / END / RESET)
// ============================================================
function setFormDisabled(disabled) {
  $("mk-number").disabled = disabled;
  $("category-input").disabled = disabled;
  $("code-select").disabled = disabled;
  $("task-input").disabled = disabled;
  document.querySelectorAll(".mk-input-group .btn-mini").forEach((b) => { b.disabled = disabled; });
  document.querySelectorAll(".fav-btn").forEach((b) => { b.disabled = disabled; });
}

function stopTimer() {
  if (state.timerHandle) { clearInterval(state.timerHandle); state.timerHandle = null; }
  $("duration-value").textContent = "00 : 00";
}

function startTimerFromEpoch(epochMs) {
  state.workStartEpoch = epochMs;
  if (state.timerHandle) clearInterval(state.timerHandle);
  const update = () => {
    const elapsed = Math.max(0, Math.floor((Date.now() - state.workStartEpoch) / 1000));
    const m = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const s = String(elapsed % 60).padStart(2, "0");
    $("duration-value").textContent = `${m} : ${s}`;
  };
  update();
  state.timerHandle = setInterval(update, 1000);
}

async function refreshWorkState() {
  const { data } = await api("/api/work");
  if (data && data.active) {
    state.activeWork = data.active;
    $("status-label").textContent = "업무ing...";
    $("status-label").classList.add("working");
    $("mk-number").value = data.active.mk_number || "";
    $("category-input").value = data.active.category || "";
    $("code-select").value = data.active.code || "";
    $("task-input").value = data.active.task || "";
    setFormDisabled(true);
    startTimerFromEpoch(Date.now() - data.active.elapsed_seconds * 1000);
  } else {
    state.activeWork = null;
    $("status-label").textContent = "업무 대기";
    $("status-label").classList.remove("working");
    setFormDisabled(false);
    stopTimer();
  }
}

$("reset-btn").addEventListener("click", async () => {
  await api("/api/work/reset", "POST");
  state.activeWork = null;
  $("mk-number").value = "";
  $("category-input").value = "";
  $("code-select").value = "";
  $("task-input").value = "";
  setFormDisabled(false);
  $("status-label").textContent = "업무 대기";
  $("status-label").classList.remove("working");
  stopTimer();
});

async function doStartWork(force) {
  const body = {
    code: $("code-select").value.trim(),
    mk_number: $("mk-number").value.trim(),
    category: $("category-input").value.trim(),
    task: $("task-input").value,
    force: !!force,
  };
  const { ok, status, data } = await api("/api/work/start", "POST", body);
  if (ok) {
    await refreshWorkState();
    if (data.closed_previous) await refreshLogs();
    return;
  }
  if (status === 409 && data && data.needs_confirm) {
    const confirmed = await showConfirm(data.message);
    if (confirmed) await doStartWork(true);
    return;
  }
  await showAlert((data && data.error) || "업무 시작 실패");
}

$("start-btn").addEventListener("click", () => doStartWork(false));

$("end-btn").addEventListener("click", async () => {
  const { ok, data } = await api("/api/work/end", "POST");
  if (!ok) { await showAlert((data && data.error) || "종료할 업무가 없습니다."); return; }
  $("mk-number").value = "";
  $("category-input").value = "";
  $("code-select").value = "";
  $("task-input").value = "";
  setFormDisabled(false);
  state.activeWork = null;
  $("status-label").textContent = "업무 대기";
  $("status-label").classList.remove("working");
  stopTimer();
  await refreshLogs();
});

wireMkGroup($("mk-number"), "[data-suffix]");
wireCategoryCodeSync($("category-input"), $("code-select"));

// ============================================================
// 즐겨찾기
// ============================================================
function buildFavoritesGrid() {
  const grid = $("favorites-grid");
  grid.innerHTML = "";
  for (let i = 1; i <= 8; i++) {
    const btn = document.createElement("button");
    btn.className = "fav-btn";
    btn.dataset.num = i;
    btn.textContent = `즐겨찾기${i}`;
    btn.addEventListener("click", () => applyFavorite(i));
    btn.addEventListener("contextmenu", (e) => { e.preventDefault(); openFavModal(i); });
    grid.appendChild(btn);
  }
}

async function refreshFavorites() {
  const { data } = await api("/api/favorites");
  state.favorites = (data && data.favorites) || {};
  document.querySelectorAll(".fav-btn").forEach((btn) => {
    const num = btn.dataset.num;
    const fav = state.favorites[num];
    if (fav && fav.name) {
      btn.textContent = fav.name.includes("_") ? fav.name.split("_").join("\n") : fav.name;
    } else {
      btn.textContent = `즐겨찾기${num}`;
    }
  });
}

function applyFavorite(num) {
  if (state.activeWork) return; // 업무 진행 중에는 적용하지 않음
  const fav = state.favorites[String(num)];
  if (!fav) return;
  $("mk-number").value = fav.mk_number || "";
  $("category-input").value = fav.category || "";
  $("code-select").value = fav.code || "";
  $("task-input").value = fav.task || "";
}

function openFavModal(num) {
  state.editingFavNum = num;
  const fav = state.favorites[String(num)] || { name: `즐겨찾기${num}`, mk_number: "", category: "", code: "", task: "" };
  $("fav-modal-title").textContent = `즐겨찾기${num} 설정`;
  $("fav-name").value = fav.name || `즐겨찾기${num}`;
  $("fav-mk").value = fav.mk_number || "";
  $("fav-category").value = fav.category || "";
  $("fav-code").value = fav.code || "";
  $("fav-task").value = fav.task || "";
  $("fav-modal-error").textContent = "";
  $("fav-modal").classList.remove("hidden");
}

wireMkGroup($("fav-mk"), "[data-fav-suffix]");
wireCategoryCodeSync($("fav-category"), $("fav-code"));

$("fav-modal-cancel").addEventListener("click", () => $("fav-modal").classList.add("hidden"));

$("fav-modal-save").addEventListener("click", async () => {
  const num = state.editingFavNum;
  const body = {
    name: $("fav-name").value.trim(),
    mk_number: $("fav-mk").value.trim(),
    category: $("fav-category").value.trim(),
    code: $("fav-code").value.trim(),
    task: $("fav-task").value,
  };
  const { ok, data } = await api(`/api/favorites/${num}`, "PUT", body);
  if (!ok) { $("fav-modal-error").textContent = (data && data.error) || "저장 실패"; return; }
  $("fav-modal").classList.add("hidden");
  await refreshFavorites();
});

$("fav-modal-reset").addEventListener("click", async () => {
  const num = state.editingFavNum;
  await api(`/api/favorites/${num}`, "DELETE");
  $("fav-modal").classList.add("hidden");
  await refreshFavorites();
});

// ============================================================
// 업무 로그 테이블
// ============================================================
$("filter-toggle-btn").addEventListener("click", async () => {
  state.filterMode = state.filterMode === "today" ? "all" : "today";
  $("filter-toggle-btn").textContent = state.filterMode === "today" ? "전체 기록보기" : "오늘 기록보기";
  await refreshLogs();
});

$("th-date").addEventListener("click", async () => {
  state.sortReverse = !state.sortReverse;
  await refreshLogs();
});

async function refreshLogs() {
  const { data } = await api(`/api/logs?mode=${state.filterMode}&reverse=${state.sortReverse ? 1 : 0}`);
  state.logs = (data && data.logs) || [];
  state.selectedLogIds.clear();
  $("log-select-all").checked = false;
  renderLogs();
  $("th-date").textContent = "날짜" + (state.sortReverse ? " ▼" : " ▲");
}

function renderLogs() {
  const tbody = $("log-tbody");
  tbody.innerHTML = "";
  state.logs.forEach((log) => {
    const tr = document.createElement("tr");
    tr.dataset.id = log.id;
    tr.innerHTML = `
      <td class="col-check"><input type="checkbox" data-id="${log.id}"></td>
      <td>${escapeHtml(log.date)}</td>
      <td>${escapeHtml(log.start_time)}</td>
      <td>${escapeHtml(log.end_time)}</td>
      <td>${escapeHtml(log.code)}</td>
      <td>${escapeHtml(log.mk_number)}</td>
      <td class="text-left">${escapeHtml(log.category)}</td>
      <td class="task-cell">${escapeHtml(log.task)}</td>
      <td>${escapeHtml(log.duration_str)}</td>
    `;
    tr.addEventListener("dblclick", () => openLogModal(log));
    tr.querySelector("input[type=checkbox]").addEventListener("change", (e) => {
      if (e.target.checked) state.selectedLogIds.add(log.id);
      else state.selectedLogIds.delete(log.id);
      tr.classList.toggle("selected", e.target.checked);
    });
    tbody.appendChild(tr);
  });
}

$("log-select-all").addEventListener("change", (e) => {
  document.querySelectorAll("#log-tbody input[type=checkbox]").forEach((cb) => {
    cb.checked = e.target.checked;
    cb.dispatchEvent(new Event("change"));
  });
});

function escapeHtml(s) {
  if (s === undefined || s === null) return "";
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---- 로그 추가/편집 모달 ----
function computeAddDuration() {
  const sh = parseInt($("lm-sh").value || "0", 10);
  const sm = parseInt($("lm-sm").value || "0", 10);
  const eh = parseInt($("lm-eh").value || "0", 10);
  const em = parseInt($("lm-em").value || "0", 10);
  const startTotal = sh * 60 + sm;
  const endTotal = eh * 60 + em;
  const diff = endTotal >= startTotal ? endTotal - startTotal : 0;
  $("lm-dh").value = Math.floor(diff / 60);
  $("lm-dm").value = diff % 60;
  $("lm-ds").value = 0;
}

["lm-sh", "lm-sm", "lm-eh", "lm-em"].forEach((id) => {
  $(id).addEventListener("input", () => { if (state.editingLogId === null) computeAddDuration(); });
});

function openLogModal(log) {
  state.editingLogId = log ? log.id : null;
  $("log-modal-title").textContent = log ? "로그 편집" : "로그 추가";
  $("log-modal-error").textContent = "";

  const now = new Date();
  const [y, mo, d] = log ? log.date.split("-").map(Number) : [now.getFullYear(), now.getMonth() + 1, now.getDate()];
  $("lm-year").value = y; $("lm-month").value = mo; $("lm-day").value = d;

  const extractNums = (text) => (text || "").match(/\d+/g) || [];
  if (log) {
    const s = extractNums(log.start_time), e = extractNums(log.end_time), du = extractNums(log.duration_str);
    $("lm-sh").value = s[0] || 0; $("lm-sm").value = s[1] || 0;
    $("lm-eh").value = e[0] || 0; $("lm-em").value = e[1] || 0;
    $("lm-dh").value = du[0] || 0; $("lm-dm").value = du[1] || 0; $("lm-ds").value = du[2] || 0;
    $("lm-code").value = log.code || "";
    $("lm-mk").value = log.mk_number || "";
    $("lm-category").value = log.category || "";
    $("lm-task").value = log.task || "";
    $("lm-duration-legend").textContent = "소요시간 (직접 편집)";
    ["lm-dh", "lm-dm", "lm-ds"].forEach((id) => { $(id).readOnly = false; });
  } else {
    const pad = (n) => String(n).padStart(2, "0");
    $("lm-sh").value = now.getHours(); $("lm-sm").value = now.getMinutes();
    $("lm-eh").value = now.getHours(); $("lm-em").value = now.getMinutes();
    $("lm-code").value = ""; $("lm-mk").value = ""; $("lm-category").value = ""; $("lm-task").value = "";
    $("lm-duration-legend").textContent = "소요시간 (자동 계산)";
    ["lm-dh", "lm-dm", "lm-ds"].forEach((id) => { $(id).readOnly = true; });
    computeAddDuration();
  }
  $("log-modal").classList.remove("hidden");
}

$("add-log-btn").addEventListener("click", () => openLogModal(null));
$("edit-log-btn").addEventListener("click", () => {
  if (state.selectedLogIds.size !== 1) { showAlert("편집할 로그를 하나만 선택해주세요."); return; }
  const id = [...state.selectedLogIds][0];
  const log = state.logs.find((l) => l.id === id);
  if (log) openLogModal(log);
});
$("log-modal-cancel").addEventListener("click", () => $("log-modal").classList.add("hidden"));

$("log-modal-save").addEventListener("click", async () => {
  const body = {
    year: $("lm-year").value, month: $("lm-month").value, day: $("lm-day").value,
    start_h: $("lm-sh").value, start_m: $("lm-sm").value,
    end_h: $("lm-eh").value, end_m: $("lm-em").value,
    duration_h: $("lm-dh").value, duration_m: $("lm-dm").value, duration_s: $("lm-ds").value,
    code: $("lm-code").value, mk_number: $("lm-mk").value,
    category: $("lm-category").value, task: $("lm-task").value,
  };
  let res;
  if (state.editingLogId) res = await api(`/api/logs/${state.editingLogId}`, "PUT", body);
  else res = await api("/api/logs", "POST", body);
  if (!res.ok) { $("log-modal-error").textContent = (res.data && res.data.error) || "저장 실패"; return; }
  $("log-modal").classList.add("hidden");
  await refreshLogs();
});

wireMkGroup($("lm-mk"), "[data-lm-suffix]");
wireCategoryCodeSync($("lm-category"), $("lm-code"));

$("delete-log-btn").addEventListener("click", async () => {
  if (state.selectedLogIds.size === 0) { await showAlert("삭제할 로그를 선택해주세요."); return; }
  const count = state.selectedLogIds.size;
  const msg = count === 1 ? "선택한 로그를 삭제하시겠습니까?" : `선택한 ${count}개의 로그를 삭제하시겠습니까?`;
  const confirmed = await showConfirm(msg);
  if (!confirmed) return;
  await api("/api/logs/delete", "POST", { ids: [...state.selectedLogIds] });
  await refreshLogs();
});

$("export-btn").addEventListener("click", () => {
  window.location.href = `/api/logs/export?mode=${state.filterMode}`;
});

// ============================================================
// 해야할 업무 (Todo)
// ============================================================
["th-created", "th-deadline", "th-dday"].forEach((id) => {
  const colMap = { "th-created": "created_date", "th-deadline": "deadline", "th-dday": "dday" };
  $(id).addEventListener("click", async () => {
    const col = colMap[id];
    if (state.todoSort === col) state.todoSortReverse = !state.todoSortReverse;
    else { state.todoSort = col; state.todoSortReverse = false; }
    await refreshTodos();
  });
});

async function refreshTodos() {
  const { data } = await api(`/api/todos?sort=${state.todoSort}&reverse=${state.todoSortReverse ? 1 : 0}`);
  state.todos = (data && data.todos) || [];
  state.selectedTodoIds.clear();
  $("todo-select-all").checked = false;
  renderTodos();
  const labels = { created_date: "th-created", deadline: "th-deadline", dday: "th-dday" };
  ["th-created", "th-deadline", "th-dday"].forEach((id) => {
    const base = { "th-created": "등록일", "th-deadline": "기한", "th-dday": "D-day" }[id];
    $(id).textContent = base;
  });
  const activeId = labels[state.todoSort];
  if (activeId) {
    const base = { "th-created": "등록일", "th-deadline": "기한", "th-dday": "D-day" }[activeId];
    $(activeId).textContent = base + (state.todoSortReverse ? " ▼" : " ▲");
  }
}

function renderTodos() {
  const tbody = $("todo-tbody");
  tbody.innerHTML = "";
  state.todos.forEach((todo) => {
    const tr = document.createElement("tr");
    tr.dataset.id = todo.id;
    tr.innerHTML = `
      <td class="col-check"><input type="checkbox" data-id="${todo.id}"></td>
      <td class="col-important">${todo.important ? "✅" : ""}</td>
      <td class="task-cell">${escapeHtml(todo.display_text)}</td>
      <td>${escapeHtml(todo.created_date)}</td>
      <td>${escapeHtml(todo.formatted_deadline)}</td>
      <td>${escapeHtml(todo.dday_text)}</td>
    `;
    tr.querySelector(".col-important").addEventListener("click", async () => {
      await api("/api/todos/toggle-important", "POST", { ids: [todo.id] });
      await refreshTodos();
    });
    tr.querySelector(".task-cell").addEventListener("dblclick", () => applyTodoToForm(todo));
    tr.querySelector("input[type=checkbox]").addEventListener("change", (e) => {
      if (e.target.checked) state.selectedTodoIds.add(todo.id);
      else state.selectedTodoIds.delete(todo.id);
      tr.classList.toggle("selected", e.target.checked);
    });
    tbody.appendChild(tr);
  });
}

$("todo-select-all").addEventListener("change", (e) => {
  document.querySelectorAll("#todo-tbody input[type=checkbox]").forEach((cb) => {
    cb.checked = e.target.checked;
    cb.dispatchEvent(new Event("change"));
  });
});

function applyTodoToForm(todo) {
  if (state.activeWork) return;
  $("mk-number").value = todo.mk_number || "";
  $("category-input").value = todo.category || "";
  $("code-select").value = todo.code || "";
  $("task-input").value = todo.task || "";
}

function openTodoModal(todo) {
  state.editingTodoId = todo ? todo.id : null;
  $("todo-modal-title").textContent = todo ? "해야할 업무 편집" : "해야할 업무 등록";
  $("todo-modal-error").textContent = "";
  $("todo-mk").value = todo ? todo.mk_number : "";
  $("todo-category").value = todo ? todo.category : "";
  $("todo-code").value = todo ? todo.code : "";
  $("todo-deadline").value = todo ? todo.deadline : "";
  $("todo-task").value = todo ? todo.task : "";
  $("todo-modal").classList.remove("hidden");
}

$("add-todo-btn").addEventListener("click", () => openTodoModal(null));
$("edit-todo-btn").addEventListener("click", () => {
  if (state.selectedTodoIds.size !== 1) { showAlert("편집할 항목을 하나만 선택해주세요."); return; }
  const id = [...state.selectedTodoIds][0];
  const todo = state.todos.find((t) => t.id === id);
  if (todo) openTodoModal(todo);
});
$("todo-modal-cancel").addEventListener("click", () => $("todo-modal").classList.add("hidden"));

$("todo-modal-save").addEventListener("click", async () => {
  const body = {
    mk_number: $("todo-mk").value.trim(),
    category: $("todo-category").value.trim(),
    code: $("todo-code").value.trim(),
    deadline: $("todo-deadline").value.trim(),
    task: $("todo-task").value,
  };
  let res;
  if (state.editingTodoId) res = await api(`/api/todos/${state.editingTodoId}`, "PUT", body);
  else res = await api("/api/todos", "POST", body);
  if (!res.ok) { $("todo-modal-error").textContent = (res.data && res.data.error) || "저장 실패"; return; }
  $("todo-modal").classList.add("hidden");
  await refreshTodos();
});

wireMkGroup($("todo-mk"), "[data-todo-suffix]");
wireCategoryCodeSync($("todo-category"), $("todo-code"));

$("delete-todo-btn").addEventListener("click", async () => {
  if (state.selectedTodoIds.size === 0) { await showAlert("삭제할 항목을 선택해주세요."); return; }
  const confirmed = await showConfirm(`선택한 ${state.selectedTodoIds.size}개 항목을 삭제하시겠습니까?`);
  if (!confirmed) return;
  await api("/api/todos/delete", "POST", { ids: [...state.selectedTodoIds] });
  await refreshTodos();
});

$("toggle-important-btn").addEventListener("click", async () => {
  if (state.selectedTodoIds.size === 0) { await showAlert("항목을 선택해주세요."); return; }
  await api("/api/todos/toggle-important", "POST", { ids: [...state.selectedTodoIds] });
  await refreshTodos();
});

// ============================================================
// 도움말
// ============================================================
$("help-btn").addEventListener("click", () => $("help-modal").classList.remove("hidden"));
$("help-close").addEventListener("click", () => $("help-modal").classList.add("hidden"));

// ============================================================
// 시작
// ============================================================
init();
