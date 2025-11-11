import { API_BASE, fetchJSON } from "../core/api.js";
import { formatDateDMY } from "../core/utils.js";
import { initRatingWidget } from "../core/ui.js";

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
            const item = document.createElement('div');
            item.className = 'review-item';
            item.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <div class="review-rating">${Number(r.rating).toFixed(1)} ★</div>
                    <div>
                        <div class="fw-semibold">${r.titulo || '(Sin título)'}<\/div>
                        <div class="small muted">por ${r.usuario || 'Anónimo'} · ${formatDateDMY(r.fecha)}<\/div>
                        <div class="mt-1">${(r.comentario || '').replace(/</g,'&lt;')}<\/div>
                    <\/div>
                <\/div>`;
            list.appendChild(item);
        });
    } catch (e) {
        console.error('reviews error', e);
    }
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
}

window.addEventListener("DOMContentLoaded", initPelicula);
