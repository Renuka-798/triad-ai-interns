
const requestToken = localStorage.getItem("dms_token");

if (!requestToken) {
    window.location.href = "index.html";
}

// Common API headers
function requestHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${requestToken}`
    };
}

// Submit a new access request
document.getElementById("requestForm").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        const docId = document.getElementById("documentId").value.trim();
        const message = document.getElementById("requestMessage");
        const button = document.getElementById("requestButton");

        button.disabled = true;
        button.textContent = "Submitting...";

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/access/request`,
                {
                    method: "POST",
                    headers: requestHeaders(),
                    body: JSON.stringify({
                        doc_id: docId
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "Request submission failed");
            }

            message.textContent = data.message;
            message.style.color = "green";

            document.getElementById("requestForm").reset();

        } catch (error) {
            message.textContent = error.message;
            message.style.color = "red";

        } finally {
            button.disabled = false;
            button.textContent = "Submit Access Request";
        }
    }
);

// Load requests received by the user's division
async function loadRequests() {
    const container = document.getElementById("requestsContainer");
    const message = document.getElementById("inboxMessage");

    const status = document.getElementById("statusFilter").value;

    container.textContent = "Loading requests...";
    message.textContent = "";

    let url = `${API_BASE_URL}/api/access/requests`;

    if (status) {
        url += `?status=${encodeURIComponent(status)}`;
    }

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${requestToken}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to load requests");
        }

        container.innerHTML = "";

        if (data.requests.length === 0) {
            container.textContent = "No access requests found.";
            return;
        }

        data.requests.forEach(item => {
            const card = document.createElement("div");
            card.className = "request-card";

            const title = document.createElement("h3");
            title.textContent = item.document_title;

            const requester = document.createElement("p");
            requester.textContent =
                `Requested by: ${item.requester_name} (${item.requester_email})`;

            const division = document.createElement("p");
            division.textContent =
                `Requester Division: ${item.requester_division}`;

            const date = document.createElement("p");
            date.textContent =
                `Requested On: ${new Date(item.created_at).toLocaleString()}`;

            const statusBadge = document.createElement("span");
            statusBadge.className = "status-badge";
            statusBadge.textContent = item.status;

            card.appendChild(title);
            card.appendChild(requester);
            card.appendChild(division);
            card.appendChild(date);
            card.appendChild(statusBadge);

            if (item.status === "Pending") {
                const actions = document.createElement("div");
                actions.className = "request-actions";

                const approveButton = document.createElement("button");
                approveButton.textContent = "Approve";
                approveButton.className = "approve-button";

                approveButton.addEventListener("click", () => {
                    processRequest(item.request_id, "approve", approveButton);
                });

                const rejectButton = document.createElement("button");
                rejectButton.textContent = "Reject";
                rejectButton.className = "reject-button";

                rejectButton.addEventListener("click", () => {
                    processRequest(item.request_id, "reject", rejectButton);
                });

                actions.appendChild(approveButton);
                actions.appendChild(rejectButton);

                card.appendChild(actions);
            }

            container.appendChild(card);
        });

    } catch (error) {
        container.textContent = "";
        message.textContent = error.message;
        message.style.color = "red";
    }
}

// Approve or reject a request
async function processRequest(requestId, action, button) {
    const message = document.getElementById("inboxMessage");

    button.disabled = true;
    button.textContent = "Processing...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/access/${action}`,
            {
                method: "POST",
                headers: requestHeaders(),
                body: JSON.stringify({
                    request_id: requestId
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to process request");
        }

        message.textContent = data.message;
        message.style.color = "green";

        await loadRequests();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
        button.disabled = false;
        button.textContent = action === "approve" ? "Approve" : "Reject";
    }
}

// Filter requests
document.getElementById("statusFilter").addEventListener(
    "change",
    loadRequests
);

// Logout
document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("dms_token");
    window.location.href = "index.html";
});

// Initial load
loadRequests();
