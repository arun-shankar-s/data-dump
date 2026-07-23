// ============================================================
// documents.js
// ============================================================

const API_BASE = "http://127.0.0.1:8000";
const PAGE_SIZE = 5;

const state = {
  page: 1,
  department: "",
  search: "",
  uploadedBy: "",
  fromDate: "",
  toDate: "",
  pendingDeleteId: null
};

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) +
    " " + d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { toast.hidden = true; }, 2500);
}

// ---------------- FILTER DROPDOWNS ----------------

async function loadFilterOptions() {
  const [depts, users] = await Promise.all([
    fetch(`${API_BASE}/api/departments`).then(r => r.json()),
    fetch(`${API_BASE}/api/users`).then(r => r.json())
  ]);

  const deptSel = document.getElementById("fDepartment");
  depts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.dept_id;
    opt.textContent = d.dept_name;
    deptSel.appendChild(opt);
  });

  const userSel = document.getElementById("fUploadedBy");
  users.forEach(u => {
    const opt = document.createElement("option");
    opt.value = u.user_id;
    opt.textContent = u.username;
    userSel.appendChild(opt);
  });
}

// ---------------- FETCH + RENDER DOCS ----------------

function buildQuery() {
  const params = new URLSearchParams();
  params.set("page", state.page);
  params.set("page_size", PAGE_SIZE);
  if (state.department) params.set("department_id", state.department);
  if (state.search) params.set("search", state.search);
  if (state.uploadedBy) params.set("uploaded_by", state.uploadedBy);
  if (state.fromDate) params.set("from_date", state.fromDate);
  if (state.toDate) params.set("to_date", state.toDate);
  return params.toString();
}

async function loadDocuments() {
  const body = document.getElementById("docsTableBody");
  body.innerHTML = `<tr class="empty-row"><td colspan="5">Loading...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}/api/documents?${buildQuery()}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = await res.json();
    renderTable(data.documents);
    renderFooter(data.total);
  } catch (err) {
    console.error(err);
    body.innerHTML = `<tr class="empty-row"><td colspan="5">Could not load documents. Check that the API is running.</td></tr>`;
    document.getElementById("entriesInfo").textContent = "";
    document.getElementById("pagination").innerHTML = "";
  }
}

function renderTable(docs) {
  const body = document.getElementById("docsTableBody");
  const docIconSvg = `<svg class="doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"/></svg>`;

  if (!docs.length) {
    body.innerHTML = `<tr class="empty-row"><td colspan="5">No documents found.</td></tr>`;
    return;
  }

  body.innerHTML = docs.map(d => `
    <tr>
      <td class="doc-name">${docIconSvg}${d.document_name}</td>
      <td>${d.department}</td>
      <td>${d.uploaded_by}</td>
      <td>${formatDate(d.upload_date)}</td>
      <td class="col-actions">
        <div class="row-actions">
          <button class="icon-action" title="View" data-view="${d.document_id}">
            <svg viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="icon-action" title="Download" data-download="${d.document_id}">
            <svg viewBox="0 0 24 24"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16"/></svg>
          </button>
          <button class="icon-action danger" title="Delete" data-delete="${d.document_id}">
            <svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0l-1 14a2 2 0 01-2 2H7a2 2 0 01-2-2L4 6"/></svg>
          </button>
        </div>
      </td>
    </tr>
  `).join("");

  body.querySelectorAll("[data-delete]").forEach(btn => {
    btn.addEventListener("click", () => openDeleteModal(btn.dataset.delete));
  });
  body.querySelectorAll("[data-download]").forEach(btn => {
    btn.addEventListener("click", () => {
      window.open(`${API_BASE}/api/documents/${btn.dataset.download}/download`, "_blank");
    });
  });
  body.querySelectorAll("[data-view]").forEach(btn => {
    btn.addEventListener("click", () => {
      window.open(`${API_BASE}/api/documents/${btn.dataset.view}/view`, "_blank");
    });
  });
}

function renderFooter(total) {
  const start = total === 0 ? 0 : (state.page - 1) * PAGE_SIZE + 1;
  const end = Math.min(state.page * PAGE_SIZE, total);
  document.getElementById("entriesInfo").textContent = `Showing ${start} to ${end} of ${total} entries`;

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pag = document.getElementById("pagination");
  let html = `<button class="page-btn" data-page="${state.page - 1}" ${state.page <= 1 ? "disabled" : ""}>&lt;</button>`;
  for (let p = 1; p <= totalPages; p++) {
    html += `<button class="page-btn ${p === state.page ? "active" : ""}" data-page="${p}">${p}</button>`;
  }
  html += `<button class="page-btn" data-page="${state.page + 1}" ${state.page >= totalPages ? "disabled" : ""}>&gt;</button>`;
  pag.innerHTML = html;

  pag.querySelectorAll("[data-page]").forEach(btn => {
    btn.addEventListener("click", () => {
      const p = Number(btn.dataset.page);
      if (p >= 1 && p <= totalPages) {
        state.page = p;
        loadDocuments();
      }
    });
  });
}

// ---------------- FILTER ACTIONS ----------------

function setupFilters() {
  document.getElementById("btnFilter").addEventListener("click", () => {
    state.department = document.getElementById("fDepartment").value;
    state.search = document.getElementById("fSearch").value.trim();
    state.uploadedBy = document.getElementById("fUploadedBy").value;
    state.fromDate = document.getElementById("fFromDate").value;
    state.toDate = document.getElementById("fToDate").value;
    state.page = 1;
    loadDocuments();
  });

  document.getElementById("btnReset").addEventListener("click", () => {
    document.getElementById("fDepartment").value = "";
    document.getElementById("fSearch").value = "";
    document.getElementById("fUploadedBy").value = "";
    document.getElementById("fFromDate").value = "";
    document.getElementById("fToDate").value = "";
    Object.assign(state, { department: "", search: "", uploadedBy: "", fromDate: "", toDate: "", page: 1 });
    loadDocuments();
  });

  document.getElementById("fSearch").addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("btnFilter").click();
  });
}

// ---------------- DELETE FLOW ----------------

function openDeleteModal(docId) {
  state.pendingDeleteId = docId;
  document.getElementById("deleteModal").hidden = false;
}

function closeDeleteModal() {
  state.pendingDeleteId = null;
  document.getElementById("deleteModal").hidden = true;
}

async function confirmDeleteDoc() {
  if (!state.pendingDeleteId) return;
  try {
    const res = await fetch(`${API_BASE}/api/documents/${state.pendingDeleteId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
    showToast("Document deleted successfully.");
    closeDeleteModal();
    loadDocuments();
  } catch (err) {
    console.error(err);
    showToast("Could not delete document.");
    closeDeleteModal();
  }
}

function setupModal() {
  document.getElementById("cancelDelete").addEventListener("click", closeDeleteModal);
  document.getElementById("confirmDelete").addEventListener("click", confirmDeleteDoc);
}

// ---------------- SIDEBAR TOGGLE ----------------

function setupSidebarToggle() {
  const btn = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  btn?.addEventListener("click", () => sidebar.classList.toggle("open"));
}

// ---------------- INIT ----------------

async function initDocumentsPage() {
  setupSidebarToggle();
  setupFilters();
  setupModal();
  await loadFilterOptions();
  await loadDocuments();
}

document.addEventListener("DOMContentLoaded", initDocumentsPage);
