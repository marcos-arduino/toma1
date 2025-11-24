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

async function cargarPeliculasFavoritas(idsPeliculas) {    
    try {
        const peliculasContainer = document.getElementById('peliculas');
        if (!peliculasContainer) {
            console.error('No se encontró el contenedor de películas');
            return;
        }
        
        peliculasContainer.innerHTML = '<div class="col-12 text-center py-3"><div class="spinner-border text-light" role="status"><span class="visually-hidden">Cargando...</span></div></div>';
        
        if (!Array.isArray(idsPeliculas) || idsPeliculas.length === 0) {
            mostrarMensajeListaVacia();
            return;
        }
        
        const promesas = idsPeliculas.map(async (id) => {
            try {
                const resp = await fetchJSON(`${API_BASE}/peliculas/${id}`);
                
                if (resp && resp.ok && resp.data) {
                    return resp.data.data || resp.data;
                } else {
                    console.error(`Error en la respuesta para ID ${id}`);
                    return null;
                }
            } catch (error) {
                console.error(`Error al cargar película ${id}:`, error);
                return null;
            }
        });
        
        const resultados = await Promise.all(promesas);
        const peliculas = resultados.filter(p => p !== null);
        
        peliculasContainer.innerHTML = '';
        
        if (peliculas.length === 0) {
            mostrarMensajeListaVacia();
            return;
        }
        
        peliculas.sort((a, b) => {
            const titleA = (a && a.title) || '';
            const titleB = (b && b.title) || '';
            return String(titleA).localeCompare(String(titleB));
        });
        
        peliculas.forEach(pelicula => {
            if (pelicula && pelicula.id) {
                const col = crearCard(pelicula);
                if (col) {
                    peliculasContainer.appendChild(col);
                }
            }
        });
        
    } catch (error) {
        console.error('Error al cargar películas favoritas:', error);
        const peliculasContainer = document.getElementById('peliculas');
        if (peliculasContainer) {
            peliculasContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar las películas favoritas. Intenta recargar la página.
                    </div>
                </div>
            `;
        }
    }
}

async function cargarPeliculas() {
    const tipo = window.GRID_TIPO;
    const tituloMap = {
        'popular': 'Películas Populares',
        'top_rated': 'Mejor Valoradas',
        'now_playing': 'En Cines',
        'favoritas': 'Mis Películas Favoritas'
    };
    
    const tituloElement = document.getElementById('tituloPeliculas');
    if (tituloElement) {
        tituloElement.textContent = tituloMap[tipo] || 'Películas';
    }
    
    if (tipo === 'favoritas') {
        try {
            const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
            if (!usuario || !usuario.id) {
                window.location.href = '/?redirect=' + encodeURIComponent('/peliculas/favoritas');
                return;
            }
            
            const respList = await fetchJSON(`${API_BASE}/mi-lista/${usuario.id}/`);
            if (respList.ok && respList.data && Array.isArray(respList.data.data)) {
                userListIds = new Set(respList.data.data.map(it => String(it.id)));
                if (userListIds.size > 0) {
                    await cargarPeliculasFavoritas(Array.from(userListIds));
                } else {
                    mostrarMensajeListaVacia();
                }
            } else {
                mostrarMensajeListaVacia();
            }
        } catch (e) {
            console.error('Error al cargar favoritos:', e);
            mostrarMensajeError('Error al cargar tus películas favoritas');
        }
        return;
    }
    
    try {
        const { ok, data } = await fetchJSON(`${API_BASE}/peliculas/${tipo}`);
        if (!ok) throw new Error("Error al obtener películas");
        const resultados = (data && data.data) || [];

        const lista = document.getElementById("peliculas");
        if (!lista) return;
        
        lista.innerHTML = "";
        resultados.forEach(pelicula => {
            const col = crearCard(pelicula);
            lista.appendChild(col);
        });
    } catch (error) {
        console.error('Error al cargar películas:', error);
        mostrarMensajeError('Error al cargar las películas');
    }
}

function mostrarMensajeListaVacia() {
    const peliculasContainer = document.getElementById('peliculas');
    if (peliculasContainer) {
        peliculasContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No tienes películas en tu lista de favoritos aún.
                </div>
                <a href="/peliculas/popular" class="btn btn-primary mt-3">
                    <i class="bi bi-film me-1"></i> Explorar películas
                </a>
            </div>
        `;
    }
}

function mostrarMensajeError(mensaje) {
    const peliculasContainer = document.getElementById('peliculas');
    if (peliculasContainer) {
        peliculasContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${mensaje}
                </div>
                <button onclick="window.location.reload()" class="btn btn-outline-light mt-3">
                    <i class="bi bi-arrow-clockwise me-1"></i> Reintentar
                </button>
            </div>
        `;
    }
}

window.addEventListener("DOMContentLoaded", cargarPeliculas);
