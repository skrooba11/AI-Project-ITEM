'use strict';

/* ==========================================================================
   전역 상태
   ========================================================================== */
let templateNames = [];          // 메인 화면 템플릿 목록(순서 있음)
let selectedTemplateName = null; // 메인 화면에서 선택된 템플릿

let editingTemplateName = null;  // 편집기: null이면 "새 템플릿"
let editorTree = [];             // 편집기: 현재 편집중인 트리(메모리, 저장 전까지 서버 반영 안됨)
let editorDirty = false;

let selectedNodeIds = [];        // 편집기: 현재 선택된 노드 id 목록
let expandedIds = new Set();     // 편집기: 펼쳐진 폴더 id
let lastClickedId = null;        // 편집기: shift 범위선택 기준

let dragFromIds = null;          // 편집기: 드래그 중인 노드 id 목록

/* ==========================================================================
   유틸
   ========================================================================== */
function uid() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID().replace(/-/g, '');
  return 'id' + Date.now().toString(16) + Math.random().toString(16).slice(2);
}

function toast(msg, type) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast' + (type ? ' ' + type : '');
  el.classList.remove('hidden');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add('hidden'), 2600);
}

async function api(path, options) {
  const res = await fetch(path, options);
  let data = null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    data = await res.json();
  }
  if (!res.ok) {
    const msg = (data && data.error) || `요청 실패 (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result; // data:...;base64,XXXX
      const idx = result.indexOf(',');
      resolve(idx >= 0 ? result.slice(idx + 1) : result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/* ==========================================================================
   트리 조작 헬퍼 (데스크톱 버전의 파이썬 트리 함수들과 동일한 동작)
   ========================================================================== */
function findNodeAndParent(nodes, id, parent) {
  parent = parent || null;
  for (const node of nodes) {
    if (node.id === id) return { node, parentArray: nodes };
    if (node.type === 'folder' && node.children) {
      const found = findNodeAndParent(node.children, id, node.children);
      if (found) return found;
    }
  }
  return null;
}

function findNode(nodes, id) {
  const r = findNodeAndParent(nodes, id);
  return r ? r.node : null;
}

function deleteNodeById(nodes, id) {
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].id === id) {
      nodes.splice(i, 1);
      return true;
    }
    if (nodes[i].type === 'folder' && nodes[i].children) {
      if (deleteNodeById(nodes[i].children, id)) return true;
    }
  }
  return false;
}

function addNode(tree, parentId, node) {
  if (parentId === null || parentId === undefined) {
    tree.push(node);
    return true;
  }
  const parent = findNode(tree, parentId);
  if (parent && parent.type === 'folder') {
    parent.children = parent.children || [];
    parent.children.push(node);
    return true;
  }
  return false; // 원본 데스크톱 버전과 동일하게, 부모가 폴더가 아니면 추가하지 않음
}

function renameNodeById(nodes, id, newName) {
  const node = findNode(nodes, id);
  if (node) { node.name = newName; return true; }
  return false;
}

function moveNodeUp(tree, id) {
  function rec(nodes) {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].id === id) {
        if (i > 0) { [nodes[i - 1], nodes[i]] = [nodes[i], nodes[i - 1]]; return true; }
        return false;
      }
      if (nodes[i].children && rec(nodes[i].children)) return true;
    }
    return false;
  }
  return rec(tree);
}

function moveNodeDown(tree, id) {
  function rec(nodes) {
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].id === id) {
        if (i < nodes.length - 1) { [nodes[i], nodes[i + 1]] = [nodes[i + 1], nodes[i]]; return true; }
        return false;
      }
      if (nodes[i].children && rec(nodes[i].children)) return true;
    }
    return false;
  }
  return rec(tree);
}

function moveNodes(tree, fromIds, toId) {
  const moved = [];
  for (const fid of fromIds) {
    const node = findNode(tree, fid);
    if (node) moved.push(node);
  }
  for (const fid of fromIds) deleteNodeById(tree, fid);

  if (toId === null || toId === undefined || fromIds.includes(toId)) {
    for (const node of moved) tree.push(node);
    return;
  }
  const dest = findNode(tree, toId);
  if (dest && dest.type === 'folder') {
    dest.children = dest.children || [];
    for (const node of moved) dest.children.push(node);
  } else {
    for (const node of moved) tree.push(node);
  }
}

function collectAllIds(nodes, out) {
  out = out || [];
  for (const n of nodes) {
    out.push(n.id);
    if (n.children) collectAllIds(n.children, out);
  }
  return out;
}

/* ==========================================================================
   메인 화면: 템플릿 목록
   ========================================================================== */
async function loadTemplateList(keepSelection) {
  const data = await api('/api/templates');
  templateNames = data.names;
  const prevSelected = selectedTemplateName;
  const listEl = document.getElementById('templateList');
  listEl.innerHTML = '';
  templateNames.forEach(name => {
    const li = document.createElement('li');
    li.textContent = name;
    li.dataset.name = name;
    if (name === selectedTemplateName) li.classList.add('selected');
    li.addEventListener('click', () => selectTemplate(name));
    li.addEventListener('dblclick', () => openEditor(name));
    listEl.appendChild(li);
  });
  if (keepSelection && prevSelected && templateNames.includes(prevSelected)) {
    selectTemplate(prevSelected);
  } else if (templateNames.length > 0 && !templateNames.includes(selectedTemplateName)) {
    selectTemplate(templateNames[0]);
  } else if (templateNames.length === 0) {
    selectTemplate(null);
  }
}

function selectTemplate(name) {
  selectedTemplateName = name;
  document.querySelectorAll('#templateList li').forEach(li => {
    li.classList.toggle('selected', li.dataset.name === name);
  });
  document.getElementById('selectedTemplateLabel').textContent =
    '선택된 템플릿: ' + (name || '없음');
  if (name && !document.getElementById('rootNameInput').value) {
    document.getElementById('rootNameInput').value = name;
  }
  if (name) document.getElementById('rootNameInput').placeholder = name;
}

async function moveTemplate(direction) {
  if (!selectedTemplateName) return;
  const idx = templateNames.indexOf(selectedTemplateName);
  const swapWith = idx + direction;
  if (swapWith < 0 || swapWith >= templateNames.length) return;
  const order = templateNames.slice();
  [order[idx], order[swapWith]] = [order[swapWith], order[idx]];
  try {
    await api('/api/templates/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order }),
    });
    await loadTemplateList(true);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function renameTemplate() {
  if (!selectedTemplateName) { toast('이름을 바꿀 템플릿을 선택하세요.', 'error'); return; }
  const newName = prompt(`'${selectedTemplateName}'의 새 이름을 입력하세요:`, selectedTemplateName);
  if (!newName || newName.trim() === '' || newName === selectedTemplateName) return;
  try {
    await api(`/api/templates/${encodeURIComponent(selectedTemplateName)}/rename`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    selectedTemplateName = newName.trim();
    await loadTemplateList(true);
    toast('이름이 변경되었습니다.', 'ok');
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteTemplate() {
  if (!selectedTemplateName) { toast('삭제할 템플릿을 선택하세요.', 'error'); return; }
  if (!confirm(`'${selectedTemplateName}' 템플릿을 삭제하시겠습니까?`)) return;
  try {
    await api(`/api/templates/${encodeURIComponent(selectedTemplateName)}`, { method: 'DELETE' });
    selectedTemplateName = null;
    await loadTemplateList(false);
    toast('삭제되었습니다.', 'ok');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ==========================================================================
   파일트리 생성 (ZIP 다운로드)
   ========================================================================== */
async function generateTree() {
  if (!selectedTemplateName) { toast('사용할 템플릿을 선택하세요.', 'error'); return; }
  const rootName = (document.getElementById('rootNameInput').value || selectedTemplateName).trim();
  if (!rootName) { toast('생성될 최상위 폴더 이름을 입력하세요.', 'error'); return; }

  const resultBox = document.getElementById('resultBox');
  resultBox.className = 'result-box';
  resultBox.textContent = `파일트리 생성 중...\n템플릿: ${selectedTemplateName}\n최상위 폴더: ${rootName}`;

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_name: selectedTemplateName, root_name: rootName }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `생성 실패 (${res.status})`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${rootName}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);

    resultBox.className = 'result-box ok';
    resultBox.textContent =
      `✅ 파일트리 생성 완료!\nZIP 파일(${rootName}.zip)이 다운로드되었습니다.\n압축을 풀면 템플릿 구조 그대로의 폴더/파일이 만들어집니다.`;
  } catch (e) {
    resultBox.className = 'result-box error';
    resultBox.textContent = `❌ 파일트리 생성 중 오류 발생: ${e.message}`;
  }
}

/* ==========================================================================
   템플릿 편집기
   ========================================================================== */
async function openEditor(name) {
  editingTemplateName = name || null;
  editorDirty = false;
  selectedNodeIds = [];
  expandedIds = new Set();
  lastClickedId = null;

  if (name) {
    try {
      const data = await api(`/api/templates/${encodeURIComponent(name)}`);
      editorTree = data.tree;
    } catch (e) {
      toast(e.message, 'error');
      return;
    }
  } else {
    editorTree = [];
  }

  expandedIds = new Set(collectAllIds(editorTree)); // 기본적으로 전부 펼침(원본과 동일)

  document.getElementById('editorTitle').textContent = editingTemplateName || '새 템플릿';
  document.getElementById('editorOverlay').classList.remove('hidden');
  renderTree();
  updateNodeButtons();
}

function closeEditor() {
  if (editorDirty && !confirm('저장하지 않은 변경사항이 있습니다. 닫으시겠습니까?')) return;
  document.getElementById('editorOverlay').classList.add('hidden');
  loadTemplateList(true);
}

function markDirty() { editorDirty = true; }

function updateNodeButtons() {
  const n = selectedNodeIds.length;
  document.getElementById('btnRenameNode').disabled = n !== 1;
  document.getElementById('btnDeleteNode').disabled = n === 0;
}

/* ---- 렌더링 ---- */
function renderTree() {
  const container = document.getElementById('treeContainer');
  container.innerHTML = '';
  container.appendChild(renderNodeList(editorTree, 0));

  container.ondragover = (e) => { e.preventDefault(); };
  container.ondrop = (e) => {
    if (e.target !== container) return; // 빈 여백에 드롭한 경우만
    e.preventDefault();
    handleDrop(null);
  };
}

function renderNodeList(nodes) {
  const ul = document.createElement('ul');
  ul.className = 'tree-ul';
  nodes.forEach(node => ul.appendChild(renderNodeItem(node)));
  return ul;
}

function renderNodeItem(node) {
  const li = document.createElement('li');
  li.className = 'tree-li';

  const row = document.createElement('div');
  row.className = 'tree-node';
  row.dataset.id = node.id;
  if (selectedNodeIds.includes(node.id)) row.classList.add('selected');
  row.draggable = true;

  const isFolder = node.type === 'folder';
  const expanded = expandedIds.has(node.id);

  const toggle = document.createElement('span');
  toggle.className = 'tree-toggle';
  toggle.textContent = isFolder ? (expanded ? '▼' : '▶') : '';
  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    if (!isFolder) return;
    if (expanded) expandedIds.delete(node.id); else expandedIds.add(node.id);
    renderTree();
  });
  row.appendChild(toggle);

  const icon = document.createElement('span');
  icon.className = 'tree-icon';
  icon.textContent = isFolder ? '📁' : '📄';
  row.appendChild(icon);

  const nameSpan = document.createElement('span');
  nameSpan.className = 'tree-name';
  nameSpan.textContent = node.name;
  row.appendChild(nameSpan);

  row.addEventListener('click', (e) => handleNodeClick(e, node.id));
  row.addEventListener('dblclick', (e) => {
    e.stopPropagation();
    if (isFolder) {
      if (expanded) expandedIds.delete(node.id); else expandedIds.add(node.id);
      renderTree();
    } else {
      selectedNodeIds = [node.id];
      lastClickedId = node.id;
      renderTree();
      updateNodeButtons();
    }
  });
  row.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    if (!selectedNodeIds.includes(node.id)) {
      selectedNodeIds = [node.id];
      renderTree();
      updateNodeButtons();
    }
    showContextMenu(e, node);
  });

  row.addEventListener('dragstart', (e) => {
    if (!selectedNodeIds.includes(node.id)) {
      selectedNodeIds = [node.id];
      renderTree();
      updateNodeButtons();
    }
    dragFromIds = selectedNodeIds.slice();
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', node.id);
  });
  row.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    row.classList.add('drag-over');
  });
  row.addEventListener('dragleave', () => row.classList.remove('drag-over'));
  row.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    row.classList.remove('drag-over');
    handleDrop(node);
  });

  li.appendChild(row);

  if (isFolder && expanded) {
    li.appendChild(renderNodeList(node.children || []));
  }
  return li;
}

function handleDrop(targetNode) {
  if (!dragFromIds || dragFromIds.length === 0) return;
  let toId = null;
  if (targetNode && targetNode.type === 'folder' && !dragFromIds.includes(targetNode.id)) {
    toId = targetNode.id;
  } else {
    toId = null; // 폴더가 아니거나 자기 자신이면 최상위로 이동 (원본 동작과 동일)
  }
  moveNodes(editorTree, dragFromIds, toId);
  markDirty();
  dragFromIds = null;
  renderTree();
  updateNodeButtons();
}

function handleNodeClick(e, id) {
  if (e.ctrlKey || e.metaKey) {
    if (selectedNodeIds.includes(id)) {
      selectedNodeIds = selectedNodeIds.filter(x => x !== id);
    } else {
      selectedNodeIds.push(id);
    }
  } else if (e.shiftKey && lastClickedId) {
    const allIds = collectAllIds(editorTree);
    const i1 = allIds.indexOf(lastClickedId);
    const i2 = allIds.indexOf(id);
    if (i1 >= 0 && i2 >= 0) {
      const [lo, hi] = i1 < i2 ? [i1, i2] : [i2, i1];
      selectedNodeIds = allIds.slice(lo, hi + 1);
    } else {
      selectedNodeIds = [id];
    }
  } else {
    selectedNodeIds = [id];
  }
  lastClickedId = id;
  renderTree();
  updateNodeButtons();
}

/* ---- 우클릭 메뉴 ---- */
function showContextMenu(e, node) {
  const menu = document.getElementById('contextMenu');
  menu.innerHTML = '';
  menu.style.left = e.clientX + 'px';
  menu.style.top = e.clientY + 'px';

  const mkItem = (label, fn) => {
    const b = document.createElement('button');
    b.textContent = label;
    b.addEventListener('click', () => { hideContextMenu(); fn(); });
    menu.appendChild(b);
  };

  mkItem('이름 바꾸기 (F2)', renameSelectedNode);
  mkItem('삭제', deleteSelectedNodes);
  if (node.type === 'folder') {
    mkItem('폴더 접기/펼치기', () => {
      if (expandedIds.has(node.id)) expandedIds.delete(node.id); else expandedIds.add(node.id);
      renderTree();
    });
  }
  menu.classList.remove('hidden');
}
function hideContextMenu() {
  document.getElementById('contextMenu').classList.add('hidden');
}
document.addEventListener('click', hideContextMenu);

/* ---- 노드 편집 동작 ---- */
function addFolderNode() {
  const name = prompt('폴더명을 입력하세요:');
  if (!name) return;
  const parentId = selectedNodeIds.length ? selectedNodeIds[0] : null;
  const node = { id: uid(), name, type: 'folder', children: [] };
  const ok = addNode(editorTree, parentId, node);
  if (!ok) { toast('선택한 항목이 폴더가 아니어서 추가할 수 없습니다. 선택을 해제하거나 폴더를 선택하세요.', 'error'); return; }
  if (parentId) expandedIds.add(parentId);
  markDirty();
  renderTree();
}

function addFileNode() {
  const name = prompt('파일명을 입력하세요:');
  if (!name) return;
  const parentId = selectedNodeIds.length ? selectedNodeIds[0] : null;
  const node = { id: uid(), name, type: 'file' };
  const ok = addNode(editorTree, parentId, node);
  if (!ok) { toast('선택한 항목이 폴더가 아니어서 추가할 수 없습니다. 선택을 해제하거나 폴더를 선택하세요.', 'error'); return; }
  if (parentId) expandedIds.add(parentId);
  markDirty();
  renderTree();
}

function renameSelectedNode() {
  if (selectedNodeIds.length !== 1) return;
  const node = findNode(editorTree, selectedNodeIds[0]);
  if (!node) return;
  const newName = prompt('새 이름을 입력하세요:', node.name);
  if (!newName || !newName.trim()) return;
  renameNodeById(editorTree, node.id, newName.trim());
  markDirty();
  renderTree();
}

function deleteSelectedNodes() {
  if (!selectedNodeIds.length) return;
  for (const id of selectedNodeIds) deleteNodeById(editorTree, id);
  selectedNodeIds = [];
  markDirty();
  renderTree();
  updateNodeButtons();
}

function moveSelectedUp() {
  if (selectedNodeIds.length !== 1) return;
  if (moveNodeUp(editorTree, selectedNodeIds[0])) { markDirty(); renderTree(); }
}
function moveSelectedDown() {
  if (selectedNodeIds.length !== 1) return;
  if (moveNodeDown(editorTree, selectedNodeIds[0])) { markDirty(); renderTree(); }
}

/* ---- 내 PC에서 불러오기 ---- */
async function importFiles(fileList) {
  const parentId = selectedNodeIds.length === 1 ? selectedNodeIds[0] : null;
  const parent = parentId ? findNode(editorTree, parentId) : null;
  const targetIsFolder = parent && parent.type === 'folder';

  let count = 0;
  for (const file of fileList) {
    try {
      const b64 = await fileToBase64(file);
      const node = { id: uid(), name: file.name, type: 'file', content_b64: b64 };
      addNode(editorTree, targetIsFolder ? parentId : null, node);
      count++;
    } catch (err) {
      console.error('파일 읽기 실패', file.name, err);
    }
  }
  if (count > 0) {
    markDirty();
    renderTree();
    toast(`${count}개 파일이 추가되었습니다.`, 'ok');
  }
}

async function importFolder(fileList) {
  // webkitRelativePath 예: "MyFolder/sub/file.txt"
  const parentId = selectedNodeIds.length === 1 ? selectedNodeIds[0] : null;
  const parent = parentId ? findNode(editorTree, parentId) : null;
  const targetIsFolder = parent && parent.type === 'folder';
  const rootChildren = targetIsFolder ? (parent.children = parent.children || []) : editorTree;

  const rootFolders = new Map(); // topName -> folderNode

  function getOrCreateFolder(parentArr, name, cache) {
    if (cache.has(name)) return cache.get(name);
    const existing = parentArr.find(n => n.type === 'folder' && n.name === name && n.__importBatch);
    if (existing) { cache.set(name, existing); return existing; }
    const node = { id: uid(), name, type: 'folder', children: [], __importBatch: true };
    parentArr.push(node);
    cache.set(name, node);
    return node;
  }

  let count = 0;
  const folderCacheStack = new Map(); // path -> {node, childCache}
  for (const file of Array.from(fileList)) {
    const relPath = file.webkitRelativePath || file.name;
    const parts = relPath.split('/').filter(Boolean);
    let currentArr = rootChildren;
    let pathKey = '';
    let cacheKeyMap = rootFolders;
    for (let i = 0; i < parts.length - 1; i++) {
      pathKey += '/' + parts[i];
      let entry = folderCacheStack.get(pathKey);
      if (!entry) {
        const folderNode = getOrCreateFolder(currentArr, parts[i], cacheKeyMap);
        entry = { node: folderNode, childCache: new Map() };
        folderCacheStack.set(pathKey, entry);
      }
      currentArr = entry.node.children;
      cacheKeyMap = entry.childCache;
    }
    try {
      const b64 = await fileToBase64(file);
      const fileName = parts[parts.length - 1];
      currentArr.push({ id: uid(), name: fileName, type: 'file', content_b64: b64 });
      count++;
    } catch (err) {
      console.error('파일 읽기 실패', relPath, err);
    }
  }

  // 내부 마킹 속성 제거
  (function clean(nodes) {
    nodes.forEach(n => { delete n.__importBatch; if (n.children) clean(n.children); });
  })(editorTree);

  if (parentId) expandedIds.add(parentId);
  if (count > 0) {
    markDirty();
    renderTree();
    toast(`${count}개 파일(폴더 구조 포함)이 추가되었습니다.`, 'ok');
  }
}

/* ---- 저장 ---- */
async function saveTemplate() {
  let name = editingTemplateName;
  if (!name) {
    name = prompt('템플릿 이름을 입력하세요:');
    if (!name || !name.trim()) return;
    name = name.trim();
  }
  try {
    if (editingTemplateName) {
      await api(`/api/templates/${encodeURIComponent(editingTemplateName)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tree: editorTree }),
      });
    } else {
      await api('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, tree: editorTree }),
      });
    }
    editorDirty = false;
    editingTemplateName = name;
    selectedTemplateName = name;
    document.getElementById('editorOverlay').classList.add('hidden');
    await loadTemplateList(true);
    toast('템플릿이 저장되었습니다.', 'ok');
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ==========================================================================
   이벤트 바인딩 & 초기화
   ========================================================================== */
function bindEvents() {
  document.getElementById('btnTplUp').addEventListener('click', () => moveTemplate(-1));
  document.getElementById('btnTplDown').addEventListener('click', () => moveTemplate(1));
  document.getElementById('btnNewTemplate').addEventListener('click', () => openEditor(null));
  document.getElementById('btnEditTemplate').addEventListener('click', () => {
    if (!selectedTemplateName) { toast('편집할 템플릿을 선택하세요.', 'error'); return; }
    openEditor(selectedTemplateName);
  });
  document.getElementById('btnRenameTemplate').addEventListener('click', renameTemplate);
  document.getElementById('btnDeleteTemplate').addEventListener('click', deleteTemplate);
  document.getElementById('btnGenerate').addEventListener('click', generateTree);

  document.getElementById('btnCloseEditor').addEventListener('click', closeEditor);
  document.getElementById('btnAddFolder').addEventListener('click', addFolderNode);
  document.getElementById('btnAddFile').addEventListener('click', addFileNode);
  document.getElementById('btnRenameNode').addEventListener('click', renameSelectedNode);
  document.getElementById('btnDeleteNode').addEventListener('click', deleteSelectedNodes);
  document.getElementById('btnMoveUp').addEventListener('click', moveSelectedUp);
  document.getElementById('btnMoveDown').addEventListener('click', moveSelectedDown);
  document.getElementById('btnSaveTemplate').addEventListener('click', saveTemplate);

  const folderInput = document.getElementById('folderInput');
  document.getElementById('btnImportFolder').addEventListener('click', () => folderInput.click());
  folderInput.addEventListener('change', async (e) => {
    if (e.target.files.length) await importFolder(e.target.files);
    folderInput.value = '';
  });

  const filesInput = document.getElementById('filesInput');
  document.getElementById('btnImportFiles').addEventListener('click', () => filesInput.click());
  filesInput.addEventListener('change', async (e) => {
    if (e.target.files.length) await importFiles(e.target.files);
    filesInput.value = '';
  });

  document.addEventListener('keydown', (e) => {
    const overlayOpen = !document.getElementById('editorOverlay').classList.contains('hidden');
    if (!overlayOpen) return;
    if (e.key === 'Escape') closeEditor();
    if (e.key === 'F2') renameSelectedNode();
    if (e.key === 'Delete') deleteSelectedNodes();
  });
}

(async function init() {
  bindEvents();
  try {
    await loadTemplateList(false);
  } catch (e) {
    toast('템플릿 목록을 불러오지 못했습니다: ' + e.message, 'error');
  }
})();
