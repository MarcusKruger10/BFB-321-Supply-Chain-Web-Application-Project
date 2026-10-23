(() => {
    const toggle = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("[data-side-menu]");
    const backdrop = document.querySelector("[data-menu-backdrop]");
    const closeButton = document.querySelector("[data-menu-close]");

    if (!toggle || !menu || !backdrop || !closeButton) {
        return;
    }

    const setOpen = (open) => {
        menu.classList.toggle("is-open", open);
        backdrop.classList.toggle("is-visible", open);
        document.body.classList.toggle("menu-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        menu.setAttribute("aria-hidden", String(!open));
        backdrop.setAttribute("aria-hidden", String(!open));
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    closeButton.addEventListener("click", () => setOpen(false));
    backdrop.addEventListener("click", () => setOpen(false));
    menu.addEventListener("click", (event) => {
        if (event.target instanceof Element && event.target.closest("a")) {
            setOpen(false);
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setOpen(false);
        }
    });
})();
