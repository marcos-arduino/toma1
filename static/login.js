const AUTH_API = "http://127.0.0.1:5000/api/auth";

// --- LOGIN ---
const formLogin = document.getElementById("formLogin");
if (formLogin) formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const contrasena = document.getElementById("loginPass").value.trim();
    const msg = document.getElementById("loginMsg");
    msg.textContent = "";

    try {
        const res = await fetch(`${AUTH_API}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, contrasena }),
        });
        const data = await res.json();

        if (data.status === "success") {
            const token = data.token || "local-session";
            localStorage.setItem("token", token);
            localStorage.setItem("usuario", JSON.stringify(data.user));

            msg.classList.remove("text-danger");
            msg.classList.add("text-success");
            msg.textContent = "Bienvenido " + data.user.nombre + "!";

            setTimeout(() => location.reload(), 1000);
        } else {
            msg.textContent = data.message || "Error al iniciar sesión.";
        }
    } catch (error) {
        msg.textContent = "Error de conexión con el servidor.";
    }
});

// --- REGISTRO ---
const formRegister = document.getElementById("formRegister");
if (formRegister) formRegister.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nombre = document.getElementById("regNombre").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const contrasena = document.getElementById("regPass").value.trim();
    const msg = document.getElementById("registerMsg");
    msg.textContent = "";

    try {
        const res = await fetch(`${AUTH_API}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre, email, contrasena }),
        });
        const data = await res.json();

        if (data.status === "success") {
            msg.classList.remove("text-danger");
            msg.classList.add("text-success");
            msg.textContent = "Cuenta creada correctamente 🎉";
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById("modalRegister"));
                modal.hide();
                new bootstrap.Modal(document.getElementById("modalLogin")).show();
            }, 1500);
        } else {
            msg.textContent = data.message || "Error al registrarse.";
        }
    } catch (error) {
        msg.textContent = "Error de conexión con el servidor.";
    }
});
