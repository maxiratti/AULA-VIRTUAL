document.addEventListener("DOMContentLoaded", function () {
    const tipo = document.getElementById("id_tipo");

    const fieldTexto = document.getElementById("fieldTexto");
    const fieldArchivo = document.getElementById("fieldArchivo");
    const fieldUrl = document.getElementById("fieldUrl");

    if (!tipo) {
        return;
    }

    function actualizarCampos() {
        const valor = tipo.value;

        fieldTexto.style.display = "none";
        fieldArchivo.style.display = "none";
        fieldUrl.style.display = "none";

        if (valor === "TEXTO") {
            fieldTexto.style.display = "block";
        }

        if (valor === "ARCHIVO") {
            fieldArchivo.style.display = "block";
        }

        if (
            valor === "ENLACE"
            || valor === "VIDEO"
            || valor === "EMBEBIDO"
        ) {
            fieldUrl.style.display = "block";
        }
    }

    tipo.addEventListener(
        "change",
        actualizarCampos
    );

    actualizarCampos();
});