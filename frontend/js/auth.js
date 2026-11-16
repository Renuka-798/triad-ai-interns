
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const message = document.getElementById("message");
        const loginButton = document.getElementById("loginButton");

        message.textContent = "Signing in...";
        message.style.color = "#294b96";
        loginButton.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "Login failed");
            }

            const token = data.access_token || data.token;

            if (!token) {
                throw new Error("Login succeeded, but no authentication token was returned.");
            }

            localStorage.setItem("dms_token", token);

            message.textContent = "Login successful! Redirecting...";
            message.style.color = "green";

            window.location.href = "dashboard.html";

        } catch (error) {
            message.textContent = error.message;
            message.style.color = "red";
        } finally {
            loginButton.disabled = false;
        }
    });
}
