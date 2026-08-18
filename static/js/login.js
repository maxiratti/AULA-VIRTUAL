document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("id_password");
    const passwordToggle = document.getElementById("passwordToggle");

    if (!passwordInput || !passwordToggle) {
        return;
    }

    passwordToggle.addEventListener("click", function () {
        const icon = passwordToggle.querySelector("i");

        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            icon.classList.remove("bi-eye");
            icon.classList.add("bi-eye-slash");

            passwordToggle.setAttribute(
                "aria-label",
                "Ocultar contraseña"
            );
        } else {
            passwordInput.type = "password";
            icon.classList.remove("bi-eye-slash");
            icon.classList.add("bi-eye");

            passwordToggle.setAttribute(
                "aria-label",
                "Mostrar contraseña"
            );
        }
    });
});