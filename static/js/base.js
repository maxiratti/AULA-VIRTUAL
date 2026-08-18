document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (!sidebar || !sidebarToggle || !sidebarOverlay) {
        return;
    }

    function openSidebar() {
        sidebar.classList.add("sidebar-open");
        sidebarOverlay.classList.add("active");
    }

    function closeSidebar() {
        sidebar.classList.remove("sidebar-open");
        sidebarOverlay.classList.remove("active");
    }

    sidebarToggle.addEventListener("click", function () {
        if (sidebar.classList.contains("sidebar-open")) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    sidebarOverlay.addEventListener("click", closeSidebar);

    window.addEventListener("resize", function () {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });
});