// ============================================================
// upload.js
// ============================================================

const API_BASE = "http://127.0.0.1:8000";
let selectedFile = null;

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { toast.hidden = true; }, 2500);
}

// ---------------- LOAD DEPARTMENTS + GROUPS ----------------

async function loadDepartments() {
  const res = await fetch(`${API_BASE}/api/departments`);
  const depts = await res.json();
  const sel = document.getElementById("docDept");
  depts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.dept_id;
    opt.textContent = d.dept_name;
    sel.appendChild(opt);
  });
}

async function loadUserGroupsIntoPermTable() {
  const res = await fetch(`${API_BASE}/api/user-groups`);
  const groups = await res.json();
  const body = document.getElementById("permTableBody");
  body.innerHTML = groups.map(g => `
    <tr>
      <td>${g.group_name}</td>
      <td><input type="checkbox" data-group-id="${g.group_id}" data-perm="edit"></td>
      <td><input type="checkbox" data-group-id="${g.group_id}" data-perm="view" checked></td>
    </tr>
  `).join("");
}

// ---------------- FILE PICKER ----------------

function setupFilePicker() {
  const input = document.getElementById("docFile");
  const btn = document.getElementById("btnChooseFile");
  const label = document.getElementById("fileName");

  btn.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    if (input.files.length) {
      selectedFile = input.files[0];
      label.textContent = selectedFile.name;
    } else {
      selectedFile = null;
      label.textContent = "No file chosen";
    }
  });
}

// ---------------- PERMISSIONS ----------------

function collectPermissions() {
  const rows = document.querySelectorAll("#permTableBody tr");
  const permissions = [];
  rows.forEach(row => {
    const editCb = row.querySelector('[data-perm="edit"]');
    const viewCb = row.querySelector('[data-perm="view"]');
    permissions.push({
      group_id: Number(editCb.dataset.groupId),
      can_edit: editCb.checked,
      can_view: viewCb.checked
    });
  });
  return permissions;
}

// ---------------- SUBMIT ----------------

async function handleSubmit(e) {
  e.preventDefault();

  const name = document.getElementById("docName").value.trim();
  const deptId = document.getElementById("docDept").value;

  if (!name || !deptId || !selectedFile) {
    showToast("Please fill document name, department, and choose a file.");
    return;
  }

  const submitBtn = document.getElementById("btnSubmit");
  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading...";

  const formData = new FormData();
  formData.append("document_name", name);
  formData.append("department_id", deptId);
  formData.append("uploaded_by", 1); // TODO: replace with logged-in admin's user_id once auth exists
  formData.append("permissions", JSON.stringify(collectPermissions()));
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`${API_BASE}/api/documents/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed: ${res.status}`);
    }
    document.getElementById("successModal").hidden = false;
    resetForm();
  } catch (err) {
    console.error(err);
    showToast(err.message || "Upload failed.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Upload";
  }
}

function resetForm() {
  document.getElementById("uploadForm").reset();
  document.getElementById("fileName").textContent = "No file chosen";
  selectedFile = null;
  document.querySelectorAll('[data-perm="view"]').forEach(cb => cb.checked = true);
  document.querySelectorAll('[data-perm="edit"]').forEach(cb => cb.checked = false);
}

// ---------------- MISC ----------------

function setupSidebarToggle() {
  const btn = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  btn?.addEventListener("click", () => sidebar.classList.toggle("open"));
}

function setupModalAndCancel() {
  document.getElementById("successOk").addEventListener("click", () => {
    document.getElementById("successModal").hidden = true;
    window.location.href = "documents.html";
  });
  document.getElementById("btnCancel").addEventListener("click", () => {
    window.location.href = "documents.html";
  });
}

async function initUploadPage() {
  setupSidebarToggle();
  setupFilePicker();
  setupModalAndCancel();
  document.getElementById("uploadForm").addEventListener("submit", handleSubmit);
  await Promise.all([loadDepartments(), loadUserGroupsIntoPermTable()]);
}

document.addEventListener("DOMContentLoaded", initUploadPage);
