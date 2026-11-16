
const signupForm = document.getElementById("signupForm");

signupForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const division = document.getElementById("division").value;
    const password = document.getElementById("password").value;
    const confirmPassword =
        document.getElementById("confirmPassword").value;

    const message = document.getElementById("signupMessage");
    const button = document.getElementById("signupButton");

    if (password !== confirmPassword) {
        message.textContent = "Passwords do not match.";
        message.style.color = "red";
        return;
    }

    if (password.length < 8) {
        message.textContent = "Password must contain at least 8 characters.";
        message.style.color = "red";
        return;
    }

    button.disabled = true;
    button.textContent = "Creating Account...";
    message.textContent = "Please wait...";
    message.style.color = "#294b96";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/auth/register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password,
                    division: division
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Registration failed");
        }

        message.textContent =
            "Account created successfully! Please sign in.";

        message.style.color = "green";
        signupForm.reset();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";

    } finally {
        button.disabled = false;
        button.textContent = "Create Account";
    }
});
