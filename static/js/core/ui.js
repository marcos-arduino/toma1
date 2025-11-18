import { API_BASE } from './api.js';

export function crearBotonLista(data, { variant = 'icon' } = {}) {
  const boton = document.createElement('button');
  boton.classList.add('btn');
  if (variant === 'icon') {
    boton.classList.add('btn-add');
    boton.textContent = '+';
  } else {
    boton.classList.add('btn-outline-success');
    boton.textContent = 'Agregar a mi lista';
    boton.dataset.variant = 'full';
  }
  boton.dataset.id = data.id;
  boton.dataset.added = 'false';

  boton.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const id = boton.dataset.id;
    const added = boton.dataset.added === 'true';
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');

    // Si no hay sesión, abrir modal de login y salir
    if (!usuario || !usuario.id) {
      try {
        const modalEl = document.getElementById('modalLogin');
        if (modalEl && window.bootstrap?.Modal) {
          new bootstrap.Modal(modalEl).show();
        }
      } catch {}
      return;
    }

    try {
      if (!added) {
        const resp = await fetch(`${API_BASE}/mi-lista/${id}/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: usuario.id,
            titulo: data.title,
            poster_url: data.imageUrl,
          }),
        });
        if (resp.ok) {
          if (variant === 'icon') {
            boton.textContent = '✕';
            boton.classList.add('btn-danger');
          } else {
            boton.textContent = 'Quitar de mi lista';
            boton.classList.remove('btn-outline-success');
            boton.classList.add('btn-danger');
          }
          boton.dataset.added = 'true';
        } else {
          alert('Error al agregar la película');
        }
      } else {
        const resp = await fetch(`${API_BASE}/mi-lista/${id}/?user_id=${encodeURIComponent(usuario.id)}`, { method: 'DELETE' });
        if (resp.ok) {
          if (variant === 'icon') {
            boton.textContent = '+';
            boton.classList.remove('btn-danger');
          } else {
            boton.textContent = 'Agregar a mi lista';
            boton.classList.remove('btn-danger');
            boton.classList.add('btn-outline-success');
          }
          boton.dataset.added = 'false';
        } else {
          alert('Error al eliminar la película');
        }
      }
    } catch (err) {
      console.error('Error con la API:', err);
    }
  });

  return boton;
}

export function crearPosterCard(data, { withButton = false } = {}) {
  const card = document.createElement('div');
  card.classList.add('poster-card');

  const img = document.createElement('img');
  img.src = data.imageUrl || '/static/img/placeholder.png';
  img.classList.add('poster');
  img.alt = data.title || 'Imagen de la película';
  card.appendChild(img);

  const overlay = document.createElement('div');
  overlay.classList.add('card-img-overlay');

  const title = document.createElement('h5');
  title.classList.add('card-title');
  title.textContent = data.title || 'Sin título';
  overlay.appendChild(title);

  if (data.vote_average != null && data.vote_average !== 'N/D') {
    const rating = document.createElement('p');
    rating.classList.add('card-text');
    const score = typeof data.vote_average === 'number' && !isNaN(data.vote_average)
      ? data.vote_average.toFixed(1)
      : String(data.vote_average);
    rating.textContent = `⭐ ${score}`;
    overlay.appendChild(rating);
  }

  card.appendChild(overlay);

  if (withButton) {
    const boton = crearBotonLista(data);
    card.appendChild(boton);
  }

  return card;
}

export function initRatingWidget(rootId = 'ratingWidget', inputId = 'ratingInput') {
  const wrap = document.getElementById(rootId);
  if (!wrap) return;
  wrap.innerHTML = '';
  for (let i = 0; i < 10; i++) {
    const s = document.createElement('span');
    s.className = 'star';
    s.textContent = '★';
    wrap.appendChild(s);
  }
  const input = document.getElementById(inputId);
  let current = 0;
  const renderStars = (value) => {
    const stars = Array.from(wrap.querySelectorAll('.star'));
    stars.forEach((el, idx) => {
      const starIndex = idx + 1; // 1..10
      el.classList.remove('filled', 'half');
      if (value >= starIndex) {
        el.classList.add('filled');
      } else if (value + 0.5 === starIndex) {
        el.classList.add('half');
      }
    });
  };
  wrap.addEventListener('mousemove', (e) => {
    const target = e.target.closest('.star');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    const idx = Array.from(wrap.children).indexOf(target); // 0..9
    const half = (e.clientX - rect.left) < rect.width / 2 ? 0.5 : 1.0;
    const val = idx + half; // 0.5..10
    renderStars(val);
  });
  wrap.addEventListener('mouseleave', () => renderStars(current));
  wrap.addEventListener('click', (e) => {
    const target = e.target.closest('.star');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    const idx = Array.from(wrap.children).indexOf(target);
    const half = (e.clientX - rect.left) < rect.width / 2 ? 0.5 : 1.0;
    current = idx + half;
    if (input) input.value = current;
    renderStars(current);
  });
  renderStars(current);
}
