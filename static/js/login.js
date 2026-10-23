// Demo-only login; replace this with real authentication before production.
const DEMO_USERNAME = "BFB321";
const DEMO_PASSWORD = "BFB321";

const loginForm = document.querySelector(".login-card form");
const loginError = document.getElementById("login-error");
const dashboardLink = Array.from(
    document.querySelectorAll(".app-header .app-top-links a")
).find((link) => link.textContent.trim() === "Dashboard");

if (!loginForm || !loginError || !dashboardLink) {
    throw new Error("The login form, error message, or Dashboard link is missing.");
}

loginForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (username === DEMO_USERNAME && password === DEMO_PASSWORD) {
        window.location.assign(dashboardLink.href);
        return;
    }

    loginError.hidden = false;
});
