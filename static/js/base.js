document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (!sidebar || !sidebarToggle || !sidebarOverlay) {
        return;
    }

    function setExpanded(expanded) {
        sidebarToggle.setAttribute(
            "aria-expanded",
            expanded ? "true" : "false"
        );
    }

    function openSidebar() {
        sidebar.classList.add("sidebar-open");
        sidebarOverlay.classList.add("active");
        document.body.classList.add("sidebar-mobile-open");
        setExpanded(true);
    }

    function closeSidebar() {
        sidebar.classList.remove("sidebar-open");
        sidebarOverlay.classList.remove("active");
        document.body.classList.remove("sidebar-mobile-open");
        setExpanded(false);
    }

    sidebarToggle.addEventListener("click", function () {
        if (sidebar.classList.contains("sidebar-open")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    sidebarOverlay.addEventListener("click", closeSidebar);

    sidebar.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            if (window.innerWidth < 992) {
                closeSidebar();
            }
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeSidebar();
        }
    });

    window.addEventListener("resize", function () {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
});
