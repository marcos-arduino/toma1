import { API_BASE } from "../core/api.js";

const ADMIN_API = `${API_BASE}/admin`;
const AUDIT_API = `${API_BASE}/audit`;

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem("usuario") || "null");
    } catch {
        return null;
    }
}

async function validateAdminAccess() {
    const usuario = getCurrentUser();
    const msg = document.getElementById("adminAccessMsg");
    msg.classList.remove("text-success");
    msg.classList.add("text-danger");

    if (!usuario) {
        msg.textContent = "Debes iniciar sesión primero.";
        return;
    }
    if (!usuario.es_admin) {
        msg.textContent = "Tu usuario no es administrador.";
        return;
    }

    const keyInput = document.getElementById("adminKeyInput");
    const adminKey = keyInput.value.trim();
    if (!adminKey) {
        msg.textContent = "Ingresa la clave de admin.";
        return;
    }

    try {
        const res = await fetch(`${ADMIN_API}/validate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_id: usuario.id, admin_key: adminKey }),
        });
        const data = await res.json();

        if (data.status === "success") {
            sessionStorage.setItem("adminAuthorized", "true");
            msg.classList.remove("text-danger");
            msg.classList.add("text-success");
            msg.textContent = "Acceso concedido.";

            document.getElementById("admin-access-section").classList.add("d-none");
            document.getElementById("admin-content").classList.remove("d-none");

            await Promise.all([loadUsers(), loadLogs()]);
        } else {
            msg.textContent = data.message || "Clave inválida.";
        }
    } catch (error) {
        msg.textContent = "Error de conexión con el servidor.";
    }
}

async function loadUsers() {
    const usuario = getCurrentUser();
    const tbody = document.getElementById("usersTableBody");
    tbody.innerHTML = "<tr><td colspan='7' class='text-center py-3'>Cargando...</td></tr>";

    try {
        const url = `${ADMIN_API}/usuarios?admin_id=${encodeURIComponent(usuario.id)}`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.status !== "success") {
            tbody.innerHTML = `<tr><td colspan='7' class='text-center text-danger py-3'>${data.message || "Error al cargar usuarios"}</td></tr>`;
            return;
        }

        if (!data.data.length) {
            tbody.innerHTML = "<tr><td colspan='7' class='text-center py-3'>No hay usuarios.</td></tr>";
            return;
        }

        tbody.innerHTML = "";
        data.data.forEach((u) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.nombre}</td>
                <td>${u.email}</td>
                <td>${u.es_admin ? "Sí" : "No"}</td>
                <td>${u.activo ? "Sí" : "No"}</td>
                <td>${u.fecha_registro || ""}</td>
                <td>
                    ${u.activo && !u.es_admin
                        ? `<button class="btn btn-sm btn-outline-danger" data-user-id="${u.id}">Desactivar</button>`
                        : "-"}
                </td>
            `;
            const btn = tr.querySelector("button[data-user-id]");
            if (btn) {
                btn.addEventListener("click", () => desactivarUsuario(u.id));
            }
            tbody.appendChild(tr);
        });
    } catch (error) {
        tbody.innerHTML = "<tr><td colspan='7' class='text-center text-danger py-3'>Error de conexión.</td></tr>";
    }
}

async function desactivarUsuario(userId) {
    const usuario = getCurrentUser();
    if (!confirm(`¿Seguro que quieres desactivar al usuario #${userId}?`)) return;

    try {
        const res = await fetch(`${ADMIN_API}/usuarios/${userId}/desactivar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_id: usuario.id }),
        });
        const data = await res.json();
        if (data.status === "success") {
            await loadUsers();
        } else {
            alert(data.message || "No se pudo desactivar el usuario.");
        }
    } catch (error) {
        alert("Error de conexión con el servidor.");
    }
}

async function loadLogs() {
    const tbody = document.getElementById("logsTableBody");
    tbody.innerHTML = "<tr><td colspan='6' class='text-center py-3'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${AUDIT_API}/logs?limit=100`);
        const data = await res.json();
        if (data.status !== "success") {
            tbody.innerHTML = `<tr><td colspan='6' class='text-center text-danger py-3'>${data.message || "Error al cargar logs"}</td></tr>`;
            return;
        }

        if (!data.data.length) {
            tbody.innerHTML = "<tr><td colspan='6' class='text-center py-3'>No hay registros.</td></tr>";
            return;
        }

        tbody.innerHTML = "";
        data.data.forEach((log) => {
            const tr = document.createElement("tr");
            const fecha = log.timestamp || log.created_at || "";
            tr.innerHTML = `
                <td>${log.id}</td>
                <td>${fecha}</td>
                <td>${log.event_type}</td>
                <td>${log.severity}</td>
                <td>${log.user_email || log.user_id || ""}</td>
                <td>${log.action_description}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        tbody.innerHTML = "<tr><td colspan='6' class='text-center text-danger py-3'>Error de conexión.</td></tr>";
    }
}

function init() {
    const btnAccess = document.getElementById("btnAdminAccess");
    if (btnAccess) {
        btnAccess.addEventListener("click", validateAdminAccess);
    }

    const btnReloadUsers = document.getElementById("btnReloadUsers");
    if (btnReloadUsers) {
        btnReloadUsers.addEventListener("click", loadUsers);
    }

    const btnReloadLogs = document.getElementById("btnReloadLogs");
    if (btnReloadLogs) {
        btnReloadLogs.addEventListener("click", loadLogs);
    }

    const usuario = getCurrentUser();
    const isAuthorized = sessionStorage.getItem("adminAuthorized") === "true";
    if (usuario && usuario.es_admin && isAuthorized) {
        document.getElementById("admin-access-section").classList.add("d-none");
        document.getElementById("admin-content").classList.remove("d-none");
        loadUsers();
        loadLogs();
    }
}

document.addEventListener("DOMContentLoaded", init);
