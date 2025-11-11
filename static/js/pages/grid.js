import { API_BASE, fetchJSON } from "../core/api.js";
import { crearPosterCard, crearBotonLista } from "../core/ui.js";

function crearCard(data) {
    const col = document.createElement("div");

    const link = document.createElement("a");
    link.href = `/peliculas/${data.id}`;
    link.classList.add("text-decoration-none", "text-reset");

    const card = crearPosterCard(data);
    const boton = crearBotonLista(data);
    card.appendChild(boton);

    link.appendChild(card);
    col.appendChild(link);

    return col;
}

async function cargarPeliculas() {
    const tipo = window.GRID_TIPO;
    try {
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
