import { API_BASE, fetchJSON } from "../core/api.js";
import { crearPosterCard, crearBotonLista } from "../core/ui.js";

let userListIds = null;

function setEstadoInicialBoton(boton, esta) {
    if (!boton) return;
    if (esta) {
        boton.dataset.added = 'true';
        boton.textContent = '✕';
        boton.classList.add('btn-danger');
    }
}

function crearCard(data) {
    const col = document.createElement("div");

    const link = document.createElement("a");
    link.href = `/peliculas/${data.id}`;
    link.classList.add("text-decoration-none", "text-reset");

    const card = crearPosterCard(data);
    const boton = crearBotonLista(data);
    if (userListIds && userListIds.has(String(data.id))) setEstadoInicialBoton(boton, true);
    card.appendChild(boton);

    link.appendChild(card);
    col.appendChild(link);

    return col;
}

async function cargarPeliculas() {
    const tipo = window.GRID_TIPO;
    try {
        // cargar lista del usuario una sola vez
        if (userListIds === null) {
            try {
                const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
                if (usuario && usuario.id) {
                    const respList = await fetchJSON(`${API_BASE}/mi-lista/${usuario.id}/`);
                    if (respList.ok && respList.data && Array.isArray(respList.data.data)) {
                        userListIds = new Set(respList.data.data.map(it => String(it.id)));
                    } else {
                        userListIds = new Set();
                    }
                } else {
                    userListIds = new Set();
                }
            } catch { userListIds = new Set(); }
        }

        const { ok, data } = await fetchJSON(`${API_BASE}/peliculas/${tipo}`);
        if (!ok) throw new Error("Error al obtener películas");
        const resultados = (data && data.data) || [];

        document.getElementById("tituloPeliculas").textContent = tipo.replace("_", " ").toUpperCase();

        const lista = document.getElementById("peliculas");
        lista.innerHTML = "";

        resultados.forEach((p) => lista.appendChild(crearCard(p)));
    } catch (err) {
        console.error("Error:", err);
    }
}

window.addEventListener("DOMContentLoaded", cargarPeliculas);
