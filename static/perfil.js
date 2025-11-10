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
    if (bioEl) bioEl.textContent = usuario.email ? `Email: ${usuario.email}` : "";
    if (fechaEl) fechaEl.textContent = "N/D";

    // Reseñas del usuario
    if (listaReviews && usuario.id) {
        listaReviews.innerHTML = "<li class='list-group-item'>Cargando reseñas...</li>";
        fetch(`${API_BASE}/users/${usuario.id}/reviews`)
            .then((r) => r.json())
            .then((data) => {
                if (!data || data.status !== "success") {
                    listaReviews.innerHTML = "<li class='list-group-item'>No se pudieron cargar tus reseñas.</li>";
                    return;
                }
                const items = data.data || [];
                if (items.length === 0) {
                    listaReviews.innerHTML = "<li class='list-group-item'>No has escrito ninguna reseña aún.</li>";
                    return;
                }
                listaReviews.innerHTML = "";
                items.forEach((rev) => {
                    const li = document.createElement("li");
                    li.className = "list-group-item";
                    const tituloPel = rev.titulo_pelicula || `Pelicula #${rev.id_pelicula}`;
                    const rating = (rev.rating != null ? Number(rev.rating).toFixed(1) : "-");
                    const titulo = (rev.titulo && rev.titulo.trim()) ? ` – ${rev.titulo.trim()}` : "";
                    const comentario = (rev.comentario && rev.comentario.trim()) ? `<div class='text-muted small mt-1'>${rev.comentario.trim()}</div>` : "";
                    li.innerHTML = `<strong>${tituloPel}</strong> (${rating}/10)${titulo}${comentario}`;
                    listaReviews.appendChild(li);
                });
            })
            .catch(() => {
                listaReviews.innerHTML = "<li class='list-group-item'>No se pudieron cargar tus reseñas.</li>";
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
