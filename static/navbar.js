document.addEventListener("DOMContentLoaded", () => {
    const btnLogin = document.getElementById("btn-login");
    const userMenu = document.getElementById("user-menu");
    const btnLogout = document.getElementById("btn-logout");
    const userMenuButton = userMenu?.querySelector(".dropdown-toggle");

    const token = localStorage.getItem("token");
    const usuario = JSON.parse(localStorage.getItem("usuario") || "null");

    if (token && usuario) {
        btnLogin.classList.add("d-none");
        userMenu.classList.remove("d-none");
        if (userMenuButton) userMenuButton.textContent = usuario.nombre || "Mi cuenta";
    } else {
        btnLogin.classList.remove("d-none");
        userMenu.classList.add("d-none");
    }

    if (btnLogout) {
        btnLogout.addEventListener("click", (e) => {
            e.preventDefault();
            localStorage.removeItem("token");
            localStorage.removeItem("usuario");
            location.reload();
        });
    }
});
