import { API_BASE, fetchJSON } from "../core/api.js";
import { formatDateDMY } from "../core/utils.js";
import { initRatingWidget, crearBotonLista } from "../core/ui.js";

const movieId = window.MOVIE_ID;

async function cargarPelicula() {
    try {
        const { ok, data } = await fetchJSON(`${API_BASE}/peliculas/${movieId}`);
        if (!ok || !data || data.status !== "success") {
            const cont = document.getElementById("pelicula");
            if (cont) cont.innerHTML = "<p class='text-danger'>Error al cargar la película.</p>";
            return;
        }
        const p = data.data;
        document.getElementById("titulo").textContent = p.title;
        document.getElementById("descripcion").textContent = p.overview;
        document.getElementById("fecha").textContent = formatDateDMY(p.release_date);
        document.getElementById("duracion").textContent = p.runtime;
        document.getElementById("generos").textContent = p.genres.join(", ");
        document.getElementById("puntuacion").textContent = p.vote_average;
        document.getElementById("imagen").src = p.imageUrl;
        if (p.backdropUrl) {
            const hero = document.querySelector('.movie-hero');
            if (hero) {
                hero.style.setProperty('--backdrop-url', `url('${p.backdropUrl}')`);
            }
        }
        if (Array.isArray(p.cast) && p.cast.length) {
            document.getElementById("elenco").textContent = p.cast.slice(0,3).join(", ");
        }

        // plataformas
        const proveedoresContainer = document.getElementById('proveedores');
        const plataformasSection = document.getElementById('plataformas');
        
        if (p.providers && p.providers.flatrate && p.providers.flatrate.length > 0) {
            proveedoresContainer.innerHTML = p.providers.flatrate
                .map(provider => `
                    <img src="${provider.logo}" 
                         alt="${provider.name}" 
                         title="${provider.name}" 
                         class="provider-logo" 
                         style="height: 30px; width: auto; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                `).join('');
        } else {
            // Mostrar mensaje si no hay proveedores
            proveedoresContainer.innerHTML = `
                <div class="muted">
                    No hay información sobre disponibilidad en plataformas en Argentina
                </div>
            `;
        }
        // Botón de agregar a mi lista (variant full)
        const wrap = document.getElementById('addToListWrap');
        if (wrap) {
            wrap.innerHTML = '';
            const btn = crearBotonLista({ id: p.id, title: p.title, imageUrl: p.imageUrl }, { variant: 'full' });
            wrap.appendChild(btn);
            // Setear estado inicial según si ya está en la lista
            try {
                const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
                if (usuario && usuario.id) {
                    const { ok, data } = await fetchJSON(`${API_BASE}/mi-lista/${usuario.id}/`);
                    if (ok && data && Array.isArray(data.data)) {
                        const yaEsta = data.data.some(item => String(item.id) === String(p.id));
                        if (yaEsta) {
                            // replicar lógica de estado "added"
                            btn.dataset.added = 'true';
                            btn.textContent = 'Quitar de mi lista';
                            btn.classList.remove('btn-outline-success');
                            btn.classList.add('btn-danger');
                        }
                    }
                }
            } catch {}
        }
    } catch (err) {
        console.error("Error cargando película:", err);
    }
}

async function cargarReviews() {
    try {
        const { ok, data } = await fetchJSON(`${API_BASE}/reviews/${movieId}`);
        if (!ok || !data) return;
        const list = document.getElementById('reviewsList');
        list.innerHTML = '';
        (data.data || []).forEach(r => {
            const item = renderReviewItem(r);
            list.appendChild(item);
        });
    } catch (e) {
        console.error('reviews error', e);
    }
}

function renderReviewItem(r) {
    const item = document.createElement('div');
    item.className = 'review-item';
    item.innerHTML = `
        <div class="d-flex align-items-start gap-2">
            <div class="review-rating">${Number(r.rating).toFixed(1)} ★<\/div>
            <div>
                <div class="fw-semibold">${r.titulo || '(Sin título)'}<\/div>
                <div class="small muted">por ${r.usuario || 'Anónimo'} · ${formatDateDMY(r.fecha)}<\/div>
                <div class="mt-1">${(r.comentario || '').replace(/</g,'&lt;')}<\/div>
            <\/div>
        <\/div>`;
    return item;
}

function initFormReview() {
    const form = document.getElementById('formReview');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
        if (!usuario) {
            const modal = new bootstrap.Modal(document.getElementById('modalLogin'));
            modal.show();
            return;
        }
        const rating = parseFloat(document.getElementById('ratingInput').value || '0');
        const titulo = document.getElementById('reviewTitle').value.trim();
        const comentario = document.getElementById('reviewBody').value.trim();
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn.textContent;
        const originalClasses = btn.className;
        btn.disabled = true;
        try {
            const res = await fetch(`${API_BASE}/reviews/${movieId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: usuario.id, rating, titulo, comentario })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                btn.className = 'btn btn-success';
                btn.textContent = 'Reseña publicada';
                form.reset();
                document.getElementById('ratingInput').value = '0';
                initRatingWidget();
                cargarReviews();
            } else {
                btn.className = 'btn btn-danger';
                btn.textContent = (data && data.message) ? data.message : 'Error al publicar';
            }
        } catch (err) {
            btn.className = 'btn btn-danger';
            btn.textContent = 'Error de red';
        }
        setTimeout(() => { btn.className = originalClasses; btn.textContent = originalText; btn.disabled = false; }, 800);
    });
}

function initPelicula() {
    cargarPelicula();
    initRatingWidget();
    initFormReview();
    cargarReviews();

    // Realtime reviews via Socket.IO
    try {
        const socket = window.appSocket || (typeof io !== 'undefined' ? io() : null);
        if (!socket) {
            console.warn('Socket.IO no disponible en pagina de pelicula');
            return;
        }

        console.log('initPelicula: escuchando evento nueva_review para movieId=', movieId, 'socketId=', socket.id);

        socket.on('nueva_review', (data) => {
            console.log('Evento nueva_review recibido:', data);
            if (!data || typeof data.movie_id === 'undefined') return;
            if (String(data.movie_id) !== String(movieId)) {
                console.log('nueva_review es de otra pelicula, se ignora');
                return;
            }

            const list = document.getElementById('reviewsList');
            if (!list) {
                console.warn('reviewsList no encontrado en DOM');
                return;
            }

            const review = {
                rating: data.rating,
                titulo: data.titulo,
                comentario: data.comentario,
                usuario: data.usuario || 'Anónimo',
                fecha: new Date().toISOString(),
            };

            const item = renderReviewItem(review);
            list.prepend(item);
        });
    } catch (e) {
        console.error('Error configurando Socket.IO para reviews:', e);
    }
}

window.addEventListener("DOMContentLoaded", initPelicula);
