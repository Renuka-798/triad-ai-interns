
const token = localStorage.getItem("dms_token");

// Check whether the user is logged in
if (!token) {
    window.location.href = "index.html";
}

// Load documents from Flask
async function loadDocuments() {
    const table = document.getElementById("documentsTable");
    const message = document.getElementById("documentMessage");

    try {
        const response = await fetch(`${API_BASE_URL}/api/documents`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to load documents");
        }

        // Display document count and division
        document.getElementById("totalDocuments").textContent =
            data.total_documents;

        document.getElementById("userDivision").textContent =
            data.division;

        document.getElementById("searchResults").textContent =
            data.total_documents;

        // Handle empty document list
        if (data.documents.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="4">No documents found in your division.</td>
                </tr>
            `;
            return;
        }

        // Display documents
        table.innerHTML = "";

        data.documents.forEach(doc => {
            const row = document.createElement("tr");

            const nameCell = document.createElement("td");
            nameCell.textContent = doc.title;

            const divisionCell = document.createElement("td");
            divisionCell.textContent = doc.division;

            const dateCell = document.createElement("td");
            dateCell.textContent =
                new Date(doc.created_at).toLocaleDateString();

            const actionCell = document.createElement("td");

            const downloadButton = document.createElement("button");
            downloadButton.textContent = "Download";
            downloadButton.style.width = "auto";
            downloadButton.style.padding = "8px 12px";

            downloadButton.addEventListener("click", () => {
                downloadDocument(doc.id, downloadButton);
            });

            actionCell.appendChild(downloadButton);

            row.appendChild(nameCell);
            row.appendChild(divisionCell);
            row.appendChild(dateCell);
            row.appendChild(actionCell);

            table.appendChild(row);
        });

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";

        table.innerHTML = `
            <tr>
                <td colspan="4">Unable to load documents.</td>
            </tr>
        `;
    }
}

// Download a document
async function downloadDocument(documentId, button) {
    try {
        button.disabled = true;
        button.textContent = "Downloading...";

        const response = await fetch(
            `${API_BASE_URL}/api/documents/${documentId}/download`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || "Download failed");
        }

        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "document";

        document.body.appendChild(link);
        link.click();
        link.remove();

        window.URL.revokeObjectURL(url);

    } catch (error) {
        alert(error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Download";
    }
}

// Logout
document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("dms_token");
    window.location.href = "index.html";
});

// Upload button - we'll connect this in the next step
document.getElementById("uploadButton").addEventListener("click", function () {
    window.location.href = "upload.html";
});

// Load documents when dashboard opens
loadDocuments();
