/* BookVoice OCR Studio — フロントエンド JS */
"use strict";

const API = "";  // 同一オリジン

// ─────────────────────────────────────────────
// 状態
// ─────────────────────────────────────────────
let state = {
  projects: [],
  currentProject: null,
  selectedPageId: null,
  driveConfigured: false,
};

// ─────────────────────────────────────────────
// 初期化
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  await refreshProjects();
  await checkDriveStatus();
  setupEventListeners();
});

function setupEventListeners() {
  // 新規プロジェクト
  document.getElementById("btn-new-project").addEventListener("click", () => {
    openModal("modal-new-project");
  });
  document.getElementById("form-new-project").addEventListener("submit", handleCreateProject);
  document.getElementById("btn-cancel-project").addEventListener("click", () => {
    closeModal("modal-new-project");
  });

  // ドロップゾーン
  const dropZone = document.getElementById("drop-zone");
  dropZone.addEventListener("click", () => document.getElementById("file-input").click());
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    handleFiles(e.dataTransfer.files);
  });
  document.getElementById("file-input").addEventListener("change", (e) => handleFiles(e.target.files));

  // ツールバーボタン
  document.getElementById("btn-ocr-all").addEventListener("click", () => runBatchOCR(false));
  document.getElementById("btn-tts-all").addEventListener("click", () => runBatchTTS(false));
  document.getElementById("btn-retry-errors").addEventListener("click", () => retryErrors());
  document.getElementById("btn-drive-all").addEventListener("click", () => uploadAllToDrive());
  document.getElementById("btn-delete-project").addEventListener("click", () => confirmDeleteProject());

  // 詳細パネル
  document.getElementById("btn-close-detail").addEventListener("click", closeDetailPanel);
  document.getElementById("btn-run-ocr").addEventListener("click", () => runPageOCR(state.selectedPageId));
  document.getElementById("btn-run-tts").addEventListener("click", () => runPageTTS(state.selectedPageId));
  document.getElementById("btn-save-text").addEventListener("click", () => saveText(state.selectedPageId));
  document.getElementById("btn-upload-drive").addEventListener("click", () => uploadPageToDrive(state.selectedPageId));
  document.getElementById("btn-download-audio").addEventListener("click", () => downloadAudio(state.selectedPageId));
  document.getElementById("btn-delete-page").addEventListener("click", () => deletePage(state.selectedPageId));
}

// ─────────────────────────────────────────────
// API ヘルパー
// ─────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "エラーが発生しました");
  }
  if (res.status === 204) return null;
  return res.json();
}

// ─────────────────────────────────────────────
// プロジェクト
// ─────────────────────────────────────────────
async function refreshProjects() {
  state.projects = await apiFetch("/projects");
  renderProjectList();
  if (state.currentProject) {
    const updated = state.projects.find(p => p.project_id === state.currentProject.project_id);
    if (updated) await selectProject(updated.project_id);
  }
}

function renderProjectList() {
  const list = document.getElementById("project-list");
  if (state.projects.length === 0) {
    list.innerHTML = `<div class="empty-state" style="padding:20px"><p>プロジェクトがありません</p></div>`;
    return;
  }
  list.innerHTML = state.projects.map(p => `
    <div class="project-item ${state.currentProject?.project_id === p.project_id ? 'active' : ''}"
         onclick="selectProject('${p.project_id}')">
      <div class="proj-title">${esc(p.title)}</div>
      <div class="proj-meta">${esc(p.author || "—")}</div>
      <div class="proj-stats">
        <span class="badge badge-blue">${p.page_count}ページ</span>
        <span class="badge badge-green">${p.done_count}完了</span>
        ${p.error_count > 0 ? `<span class="badge badge-red">${p.error_count}エラー</span>` : ""}
      </div>
    </div>
  `).join("");
}

async function selectProject(projectId) {
  const res = await apiFetch(`/projects/${projectId}`);
  state.currentProject = res;
  const pages = await apiFetch(`/projects/${projectId}/pages`);
  state.currentProjectPages = pages;
  renderProjectList();
  renderToolbar();
  renderPageGrid(pages);
  closeDetailPanel();
}

async function handleCreateProject(e) {
  e.preventDefault();
  const title = document.getElementById("new-title").value.trim();
  const author = document.getElementById("new-author").value.trim();
  const language = document.getElementById("new-language").value;
  if (!title) { showToast("書名を入力してください", "warning"); return; }
  try {
    const project = await apiFetch("/projects", {
      method: "POST",
      body: JSON.stringify({ title, author, language }),
    });
    closeModal("modal-new-project");
    document.getElementById("form-new-project").reset();
    await refreshProjects();
    await selectProject(project.project_id);
    showToast("プロジェクトを作成しました", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function confirmDeleteProject() {
  if (!state.currentProject) return;
  if (!confirm(`「${state.currentProject.title}」を削除しますか？\n画像・音声ファイルもすべて削除されます。`)) return;
  try {
    await apiFetch(`/projects/${state.currentProject.project_id}`, { method: "DELETE" });
    state.currentProject = null;
    state.currentProjectPages = [];
    state.selectedPageId = null;
    await refreshProjects();
    renderToolbar();
    renderPageGrid([]);
    closeDetailPanel();
    showToast("プロジェクトを削除しました");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ─────────────────────────────────────────────
// ページ
// ─────────────────────────────────────────────
async function handleFiles(files) {
  if (!state.currentProject) {
    showToast("先にプロジェクトを選択してください", "warning");
    return;
  }
  const images = Array.from(files).filter(f => f.type.startsWith("image/"));
  if (images.length === 0) {
    showToast("画像ファイルを選択してください", "warning");
    return;
  }
  showToast(`${images.length}枚をアップロード中...`);
  let success = 0;
  for (const file of images) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/projects/${state.currentProject.project_id}/pages`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      success++;
    } catch (err) {
      showToast(`${file.name}: ${err.message}`, "error");
    }
  }
  if (success > 0) {
    await selectProject(state.currentProject.project_id);
    showToast(`${success}枚のアップロード完了`, "success");
  }
}

function renderToolbar() {
  const p = state.currentProject;
  document.getElementById("project-title-display").textContent = p ? p.title : "プロジェクトを選択してください";
  const hasProject = !!p;
  ["btn-ocr-all", "btn-tts-all", "btn-retry-errors", "btn-drive-all", "btn-delete-project"].forEach(id => {
    document.getElementById(id).disabled = !hasProject;
  });
  document.getElementById("drop-zone").style.display = hasProject ? "" : "none";
}

function renderPageGrid(pages) {
  const grid = document.getElementById("page-grid");
  if (!pages || pages.length === 0) {
    grid.innerHTML = `<div class="empty-state">
      <div class="icon">📄</div>
      <p>画像をドロップしてページを追加してください</p>
    </div>`;
    updateStatusBar();
    return;
  }
  grid.innerHTML = pages.map(page => `
    <div class="page-card ${state.selectedPageId === page.page_id ? 'selected' : ''}"
         onclick="openPage('${page.page_id}')"
         data-page-id="${page.page_id}">
      <img src="/projects/${state.currentProject.project_id}/pages/${page.page_id}/image"
           onerror="this.style.display='none'"
           loading="lazy">
      <div class="card-footer">
        <span class="page-num">P.${page.order}</span>
        <span class="status-icons">
          <span class="status-dot ${page.ocr_status}" title="OCR: ${page.ocr_status}"></span>
          <span class="status-dot ${page.tts_status}" title="TTS: ${page.tts_status}"></span>
        </span>
      </div>
    </div>
  `).join("");
  updateStatusBar();
}

async function openPage(pageId) {
  state.selectedPageId = pageId;
  document.querySelectorAll(".page-card").forEach(c => {
    c.classList.toggle("selected", c.dataset.pageId === pageId);
  });
  const page = state.currentProjectPages.find(p => p.page_id === pageId);
  if (!page) return;
  renderDetailPanel(page);
  document.getElementById("detail-panel").classList.add("open");
}

function renderDetailPanel(page) {
  document.getElementById("detail-page-num").textContent = `ページ ${page.order}`;

  const img = document.getElementById("detail-image");
  img.src = `/projects/${state.currentProject.project_id}/pages/${page.page_id}/image`;
  img.onerror = () => { img.style.display = "none"; };

  document.getElementById("detail-ocr-text").value = page.ocr_text || "";

  // OCR ステータス
  document.getElementById("ocr-status-label").textContent = statusLabel(page.ocr_status);
  document.getElementById("ocr-status-label").className = `badge ${statusBadgeClass(page.ocr_status)}`;

  // TTS ステータス
  document.getElementById("tts-status-label").textContent = statusLabel(page.tts_status);
  document.getElementById("tts-status-label").className = `badge ${statusBadgeClass(page.tts_status)}`;

  // エラーメッセージ
  const errDiv = document.getElementById("detail-error");
  if (page.error_message) {
    errDiv.textContent = `エラー: ${page.error_message}`;
    errDiv.style.display = "";
  } else {
    errDiv.style.display = "none";
  }

  // ボタン状態
  document.getElementById("btn-download-audio").disabled = page.tts_status !== "done";
  document.getElementById("btn-upload-drive").disabled = page.tts_status !== "done";
}

function closeDetailPanel() {
  document.getElementById("detail-panel").classList.remove("open");
  state.selectedPageId = null;
  document.querySelectorAll(".page-card").forEach(c => c.classList.remove("selected"));
}

// ─────────────────────────────────────────────
// 画像表示エンドポイント（main.py に追加が必要）
// ─────────────────────────────────────────────

// ─────────────────────────────────────────────
// OCR
// ─────────────────────────────────────────────
async function runPageOCR(pageId) {
  if (!pageId || !state.currentProject) return;
  const btn = document.getElementById("btn-run-ocr");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>OCR実行中...`;
  try {
    const result = await apiFetch(
      `/projects/${state.currentProject.project_id}/pages/${pageId}/ocr`,
      { method: "POST" }
    );
    document.getElementById("detail-ocr-text").value = result.ocr_text;
    document.getElementById("ocr-status-label").textContent = statusLabel(result.ocr_status);
    document.getElementById("ocr-status-label").className = `badge ${statusBadgeClass(result.ocr_status)}`;
    if (result.error_message) {
      document.getElementById("detail-error").textContent = `エラー: ${result.error_message}`;
      document.getElementById("detail-error").style.display = "";
      showToast(result.error_message, "error");
    } else {
      document.getElementById("detail-error").style.display = "none";
      showToast("OCR 完了", "success");
    }
    await selectProject(state.currentProject.project_id);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "OCR 実行";
  }
}

async function runBatchOCR(errorsOnly) {
  if (!state.currentProject) return;
  const btn = document.getElementById("btn-ocr-all");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>OCR実行中...`;
  try {
    const results = await apiFetch(
      `/projects/${state.currentProject.project_id}/ocr/batch?retry_errors_only=${errorsOnly}`,
      { method: "POST" }
    );
    const errors = results.filter(r => r.ocr_status === "error").length;
    const done = results.filter(r => r.ocr_status === "done").length;
    showToast(`OCR 完了: ${done}件成功 ${errors > 0 ? errors + "件エラー" : ""}`,
              errors > 0 ? "warning" : "success");
    await selectProject(state.currentProject.project_id);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "全ページ OCR";
  }
}

// ─────────────────────────────────────────────
// TTS
// ─────────────────────────────────────────────
async function runPageTTS(pageId) {
  if (!pageId || !state.currentProject) return;
  const btn = document.getElementById("btn-run-tts");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>音声生成中...`;
  try {
    const result = await apiFetch(
      `/projects/${state.currentProject.project_id}/pages/${pageId}/tts`,
      { method: "POST" }
    );
    document.getElementById("tts-status-label").textContent = statusLabel(result.tts_status);
    document.getElementById("tts-status-label").className = `badge ${statusBadgeClass(result.tts_status)}`;
    if (result.error_message) {
      showToast(result.error_message, "error");
    } else {
      showToast("音声生成 完了", "success");
      document.getElementById("btn-download-audio").disabled = false;
      document.getElementById("btn-upload-drive").disabled = false;
    }
    await selectProject(state.currentProject.project_id);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "TTS 実行";
  }
}

async function runBatchTTS(errorsOnly) {
  if (!state.currentProject) return;
  const btn = document.getElementById("btn-tts-all");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>音声生成中...`;
  try {
    const results = await apiFetch(
      `/projects/${state.currentProject.project_id}/tts/batch?retry_errors_only=${errorsOnly}`,
      { method: "POST" }
    );
    const done = results.filter(r => r.tts_status === "done").length;
    const errors = results.filter(r => r.tts_status === "error").length;
    showToast(`TTS 完了: ${done}件成功 ${errors > 0 ? errors + "件エラー" : ""}`,
              errors > 0 ? "warning" : "success");
    await selectProject(state.currentProject.project_id);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "全ページ TTS";
  }
}

// ─────────────────────────────────────────────
// テキスト保存
// ─────────────────────────────────────────────
async function saveText(pageId) {
  if (!pageId || !state.currentProject) return;
  const text = document.getElementById("detail-ocr-text").value;
  try {
    await apiFetch(
      `/projects/${state.currentProject.project_id}/pages/${pageId}/text`,
      { method: "PATCH", body: JSON.stringify({ ocr_text: text }) }
    );
    showToast("テキストを保存しました", "success");
    await selectProject(state.currentProject.project_id);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ─────────────────────────────────────────────
// エラー再試行
// ─────────────────────────────────────────────
async function retryErrors() {
  if (!state.currentProject) return;
  showToast("エラーページを再実行中...");
  try {
    await apiFetch(
      `/projects/${state.currentProject.project_id}/ocr/batch?retry_errors_only=true`,
      { method: "POST" }
    );
    await apiFetch(
      `/projects/${state.currentProject.project_id}/tts/batch?retry_errors_only=true`,
      { method: "POST" }
    );
    await selectProject(state.currentProject.project_id);
    showToast("再実行完了", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ─────────────────────────────────────────────
// Drive
// ─────────────────────────────────────────────
async function checkDriveStatus() {
  try {
    const res = await apiFetch("/drive/status");
    state.driveConfigured = res.configured;
    const el = document.getElementById("drive-status");
    el.textContent = res.configured ? "Drive 接続済" : "Drive 未設定";
    el.className = `drive-status ${res.configured ? "on" : "off"}`;
  } catch (_) {}
}

async function uploadPageToDrive(pageId) {
  if (!pageId || !state.currentProject) return;
  const btn = document.getElementById("btn-upload-drive");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>アップロード中...`;
  try {
    const result = await apiFetch(
      `/projects/${state.currentProject.project_id}/pages/${pageId}/drive`,
      { method: "POST" }
    );
    showToast(result.message, result.status === "done" ? "success" : "error");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Drive 保存";
  }
}

async function uploadAllToDrive() {
  if (!state.currentProject) return;
  const btn = document.getElementById("btn-drive-all");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span>Drive 保存中...`;
  try {
    const results = await apiFetch(
      `/projects/${state.currentProject.project_id}/drive/batch`,
      { method: "POST" }
    );
    const done = results.filter(r => r.status === "done").length;
    showToast(`${done}件を Drive に保存しました`, "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "全て Drive 保存";
  }
}

// ─────────────────────────────────────────────
// ダウンロード・削除
// ─────────────────────────────────────────────
function downloadAudio(pageId) {
  if (!pageId || !state.currentProject) return;
  window.location.href = `/projects/${state.currentProject.project_id}/pages/${pageId}/audio`;
}

async function deletePage(pageId) {
  if (!pageId || !state.currentProject) return;
  if (!confirm("このページを削除しますか？")) return;
  try {
    await apiFetch(
      `/projects/${state.currentProject.project_id}/pages/${pageId}`,
      { method: "DELETE" }
    );
    closeDetailPanel();
    await selectProject(state.currentProject.project_id);
    showToast("ページを削除しました");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ─────────────────────────────────────────────
// ステータスバー
// ─────────────────────────────────────────────
function updateStatusBar() {
  const pages = state.currentProjectPages || [];
  const total = pages.length;
  const ocrDone = pages.filter(p => p.ocr_status === "done").length;
  const ttsDone = pages.filter(p => p.tts_status === "done").length;
  const errors = pages.filter(p => p.ocr_status === "error" || p.tts_status === "error").length;
  document.getElementById("status-bar").innerHTML = `
    <span>合計 ${total} ページ</span>
    <span>OCR 完了: ${ocrDone}</span>
    <span>音声 完了: ${ttsDone}</span>
    ${errors > 0 ? `<span style="color:var(--error)">エラー: ${errors}</span>` : ""}
  `;
}

// ─────────────────────────────────────────────
// モーダル
// ─────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add("open");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

// ─────────────────────────────────────────────
// トースト通知
// ─────────────────────────────────────────────
function showToast(msg, type = "") {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ─────────────────────────────────────────────
// ユーティリティ
// ─────────────────────────────────────────────
function esc(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function statusLabel(s) {
  return { pending: "未処理", processing: "処理中", done: "完了", error: "エラー" }[s] || s;
}

function statusBadgeClass(s) {
  return { pending: "badge-gray", processing: "badge-blue", done: "badge-green", error: "badge-red" }[s] || "badge-gray";
}
