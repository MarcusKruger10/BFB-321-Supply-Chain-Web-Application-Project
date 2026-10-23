// Demo-only login; replace this with real authentication before production.
const DEMO_USERNAME = "BFB321";
const DEMO_PASSWORD = "BFB321";

const loginForm = document.querySelector(".login-card form");
const loginError = document.getElementById("login-error");
if (!loginForm || !loginError) {
    throw new Error("The login form or error message is missing.");
}

loginForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    if (username === DEMO_USERNAME && password === DEMO_PASSWORD) {
        sessionStorage.setItem("loggedIn", "true");
        window.location.assign("/dashboard");
        return;
    }

    loginError.hidden = false;
});
