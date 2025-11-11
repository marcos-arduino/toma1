import { API_BASE, fetchJSON } from "../core/api.js";
import { crearPosterCard, crearBotonLista } from "../core/ui.js";

let userListIds = null;

function setEstadoInicialBoton(boton, estado) {
    if (!boton) return;
    if (estado) {
        boton.dataset.added = 'true';
        boton.textContent = '✕';
        boton.classList.add('btn-danger');
    }
}

function crearCard(data) {
    const link = document.createElement("a");
    link.href = `/peliculas/${data.id}`;
    link.classList.add("text-decoration-none", "text-reset");

    const card = crearPosterCard(data);
    const boton = crearBotonLista(data);
    if (userListIds && userListIds.has(String(data.id))) setEstadoInicialBoton(boton, true);
    card.appendChild(boton);

    link.appendChild(card);
    return link;
}

async function cargarCategoria(tipo, destinoId) {
    try {
        const { ok, data } = await fetchJSON(`${API_BASE}/peliculas/${tipo}`);
        if (!ok) throw new Error("Error al obtener películas");
        const datos = (data && data.data) || [];
        const cont = document.getElementById(destinoId);
        cont.innerHTML = "";
        datos.forEach(p => cont.appendChild(crearCard(p)));
    } catch (e) {
        console.error("Error cargando", tipo, e);
    }
}

function setupArrows() {
    document.querySelectorAll('.nav-arrow').forEach(btn => {
        const targetSel = btn.getAttribute('data-target');
        const scroller = document.querySelector(targetSel);
        if (!scroller) return;
        const dir = btn.classList.contains('nav-prev') ? -1 : 1;
        btn.addEventListener('click', () => {
            const step = scroller.clientWidth * 0.9;
            scroller.scrollBy({ left: dir * step, behavior: 'smooth' });
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    (async () => {
        try {
            const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
            if (usuario && usuario.id) {
                const { ok, data } = await fetchJSON(`${API_BASE}/mi-lista/${usuario.id}/`);
                if (ok && data && Array.isArray(data.data)) {
                    userListIds = new Set(data.data.map(it => String(it.id)));
                }
            }
        } catch {}
        cargarCategoria('popular', 'carousel-popular');
        cargarCategoria('top_rated', 'carousel-top');
        cargarCategoria('now_playing', 'carousel-now');
        setupArrows();
    })();
});
