document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const searchToggleBtn = document.getElementById('searchToggleBtn');
    
    // Función para manejar el cambio de tamaño de pantalla
    function handleResponsiveLayout() {
        if (window.innerWidth <= 260) {
            // Pantallas pequeñas: mostrar solo el botón de búsqueda
            searchForm.classList.add('d-none');
            searchToggleBtn.classList.remove('d-none');
        } else {
            // Pantallas más grandes: mostrar el campo de búsqueda completo
            searchForm.classList.remove('d-none');
            searchToggleBtn.classList.add('d-none');
        }
    }

    // Alternar visibilidad del campo de búsqueda
    searchToggleBtn.addEventListener('click', function() {
        searchForm.classList.toggle('d-none');
        if (!searchForm.classList.contains('d-none')) {
            searchInput.focus();
        }
    });

    // Manejar el envío del formulario
    searchForm.addEventListener('submit', function(e) {
        if (window.innerWidth <= 260) {
            // En pantallas pequeñas, ocultar el campo después de buscar
            searchForm.classList.add('d-none');
        }
    });

    // Manejar cambios en el tamaño de la ventana
    window.addEventListener('resize', handleResponsiveLayout);
    
    // Inicializar el estado
    handleResponsiveLayout();
});
