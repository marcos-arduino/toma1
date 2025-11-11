document.addEventListener("DOMContentLoaded", () => {
    const usuario = JSON.parse(localStorage.getItem("usuario") || "null");
    if (!usuario) {
        // Si no hay sesión, redirigir a inicio
        location.href = "/";
        return;
    }

    // Resolver base de API según entorno
    const API_BASE = document.querySelector('meta[name="api-base"]')?.content
        || (typeof window !== 'undefined' && window.API_BASE)
        || `${location.origin}/api`;

    // Datos básicos del usuario
    const nombreEl = document.getElementById("nombreUsuario");
    const bioEl = document.getElementById("bioUsuario");
    const fechaEl = document.getElementById("fechaRegistro");
    const listaReviews = document.getElementById("listaReviews");
    const favoritasEl = document.getElementById("numFavoritas");

    if (nombreEl) nombreEl.textContent = usuario.nombre || "Usuario";
    if (bioEl) bioEl.textContent = "";
    if (fechaEl) fechaEl.textContent = "";

    // Reseñas del usuario
    if (listaReviews && usuario.id) {
        listaReviews.innerHTML = "<div class='text-muted small'>Cargando reseñas...</div>";
        fetch(`${API_BASE}/users/${usuario.id}/reviews`)
            .then((r) => r.json())
            .then((data) => {
                if (!data || data.status !== "success") {
                    listaReviews.innerHTML = "<div class='text-muted small'>No se pudieron cargar tus reseñas.</div>";
                    return;
                }
                const items = data.data || [];
                if (items.length === 0) {
                    listaReviews.innerHTML = "<div class='text-muted small'>No has escrito ninguna reseña aún.</div>";
                    return;
                }
                listaReviews.innerHTML = "";
                items.forEach((rev) => {
                    const item = document.createElement("div");
                    item.className = "review-item mb-2";
                    const tituloPel = rev.titulo_pelicula || `Pelicula #${rev.id_pelicula}`;
                    const rating = (rev.rating != null ? Number(rev.rating).toFixed(1) : "-");
                    const fechaTxt = rev.fecha ? new Date(rev.fecha).toLocaleDateString() : "";
                    const titulo = (rev.titulo && rev.titulo.trim()) ? `<div class='small fw-semibold mt-1'>${rev.titulo.trim()}</div>` : "";
                    const comentario = (rev.comentario && rev.comentario.trim()) ? `<div class='mt-1'>${rev.comentario.trim().replace(/</g,'&lt;')}</div>` : "";
                    item.innerHTML = `
                        <div class="d-flex align-items-start gap-2">
                            <div class="review-rating">${rating} ★</div>
                            <div>
                                <div class="fw-semibold">${tituloPel}</div>
                                <div class="small muted">${fechaTxt}</div>
                                ${titulo}
                                ${comentario}
                            </div>
                        </div>`;
                    listaReviews.appendChild(item);
                });
            })
            .catch(() => {
                listaReviews.innerHTML = "<div class='text-muted small'>No se pudieron cargar tus reseñas.</div>";
            });
    }

    // Contar favoritas desde backend
    if (favoritasEl && usuario.id) {
        fetch(`${API_BASE}/mi-lista/${usuario.id}/`)
            .then((r) => r.json())
            .then((data) => {
                if (data && data.status === "success") {
                    favoritasEl.textContent = (data.total != null ? data.total : (data.data || []).length);
                } else {
                    favoritasEl.textContent = "0";
                }
            })
            .catch(() => {
                favoritasEl.textContent = "0";
            });
    }
});
