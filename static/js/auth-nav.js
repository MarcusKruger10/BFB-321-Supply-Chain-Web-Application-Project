(() => {
    const authLink = document.querySelector("[data-auth-toggle]");
    if (!authLink) {
        return;
    }

    const isLoggedIn = sessionStorage.getItem("loggedIn") === "true";
    authLink.textContent = isLoggedIn ? "Log Out" : "Log In";
    authLink.href = "/login";

    authLink.addEventListener("click", () => {
        if (sessionStorage.getItem("loggedIn") === "true") {
            sessionStorage.removeItem("loggedIn");
            authLink.textContent = "Log In";
        }
    });
})();
