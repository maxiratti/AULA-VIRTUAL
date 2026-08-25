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

document.addEventListener("DOMContentLoaded", function () {
    const refreshMarker = document.getElementById("scheduled-class-refresh");

    if (!refreshMarker) {
        return;
    }

    const publishAt = refreshMarker.dataset.publishAt;

    if (!publishAt) {
        return;
    }

    const publishTime = new Date(publishAt).getTime();

    if (Number.isNaN(publishTime)) {
        return;
    }

    const delay = publishTime - Date.now();

    if (delay <= 0) {
        window.location.reload();
        return;
    }

    const MAX_TIMEOUT = 2147483647;

    if (delay <= MAX_TIMEOUT) {
        window.setTimeout(function () {
            window.location.reload();
        }, delay + 1000);
    }
});

