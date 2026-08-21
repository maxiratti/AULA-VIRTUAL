document.addEventListener("DOMContentLoaded", function () {
    const institucionSelect = document.getElementById("id_institucion");

    if (!institucionSelect) {
        return;
    }

    institucionSelect.addEventListener("change", function () {
        const form = institucionSelect.closest("form");

        if (!form) {
            return;
        }

        form.submit();
    });
});