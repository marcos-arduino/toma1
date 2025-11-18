import { API_BASE, fetchJSON } from "../core/api.js";
import { crearPosterCard, crearBotonLista } from "../core/ui.js";

function crearCard(data) {
    // Evitar renderizar películas vacías
    if (!data.title || !data.imageUrl) return null;

    const col = document.createElement("div");
    col.classList.add("col");

    const link = document.createElement("a");
    link.href = `/peliculas/${data.id}`;
    link.classList.add("text-decoration-none", "text-reset");

    // Reutilizamos el mismo componente de UI
    const card = crearPosterCard(data);
    // Botón de lista consistente
    const boton = crearBotonLista(data);
    card.appendChild(boton);

    link.appendChild(card);
    col.appendChild(link);

    return col;
}

async function cargarResultados() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q");

    const tituloBusqueda = document.getElementById("tituloBusqueda");
    const lista = document.getElementById("resultados");

    if (!query) {
        lista.innerHTML = "<p>Por favor, ingresa un término de búsqueda.</p>";
        return;
    }

    tituloBusqueda.textContent = `Resultados para: "${query}"`;
    lista.innerHTML = "<p>Cargando resultados...</p>";

    try {
        const { ok, data } = await fetchJSON(`${API_BASE}/buscar?q=${encodeURIComponent(query)}`);

        lista.innerHTML = "";

        if (ok && data && data.status === "success" && data.data.length > 0) {
            data.data.forEach((p) => {
                const card = crearCard(p);
                if (card) lista.appendChild(card);
            });
        } else {
            lista.innerHTML = "<p>No se encontraron resultados.</p>";
        }
    } catch (error) {
        console.error("Error al cargar resultados:", error);
        lista.innerHTML = "<p>Error al buscar películas.</p>";
    }
}

window.addEventListener("DOMContentLoaded", cargarResultados);
