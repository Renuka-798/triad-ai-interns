
// ==========================================
// TRIAD DMS - DOCUMENT HUB
// ==========================================

// Get authentication token
const documentsToken = localStorage.getItem("dms_token");

// Redirect to login if token is missing
if (!documentsToken) {
    window.location.href = "index.html";
}

// Get HTML elements
const documentsTable = document.getElementById("documentsTable");
const documentCount = document.getElementById("documentCount");
const documentMessage = document.getElementById("documentMessage");


// ==========================================
// LOAD DOCUMENTS FROM FLASK API
// ==========================================

async function loadDocuments() {

    documentsTable.innerHTML = `
        <tr>
            <td colspan="4">Loading documents...</td>
        </tr>
    `;

    documentMessage.textContent = "";

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/documents`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${documentsToken}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {

            if (response.status === 401) {
                localStorage.removeItem("dms_token");
                window.location.href = "index.html";
                return;
            }

            throw new Error(
                data.message || "Unable to load documents"
            );
        }

        // Display total documents and division
        documentCount.textContent =
            `${data.total_documents} documents found in ${data.division} division`;

        // Clear previous table rows
        documentsTable.innerHTML = "";

        // Check whether documents exist
        if (!data.documents || data.documents.length === 0) {

            documentsTable.innerHTML = `
                <tr>
                    <td colspan="4">No documents available.</td>
                </tr>
            `;

            return;
        }

        // Display each document
        data.documents.forEach(doc => {

            // Create table row
            const row = document.createElement("tr");

            // Document name
            const nameCell = document.createElement("td");
            nameCell.textContent = doc.title || doc.filename;

            // Division
            const divisionCell = document.createElement("td");
            divisionCell.textContent = doc.division;

            // Uploaded date
            const dateCell = document.createElement("td");

            dateCell.textContent = doc.created_at
                ? new Date(doc.created_at).toLocaleDateString()
                : "Not available";

            // Action column
            const actionCell = document.createElement("td");

            // Download button
            const downloadButton = document.createElement("button");

            downloadButton.textContent = "Download";
            downloadButton.className = "approve-button";

            downloadButton.addEventListener("click", function () {

                downloadDocument(
                    doc.id,
                    doc.filename,
                    downloadButton
                );

            });

            actionCell.appendChild(downloadButton);

            // Append all cells to row
            row.appendChild(nameCell);
            row.appendChild(divisionCell);
            row.appendChild(dateCell);
            row.appendChild(actionCell);

            // Append row to table
            documentsTable.appendChild(row);

        });

    } catch (error) {

        documentsTable.innerHTML = `
            <tr>
                <td colspan="4">Unable to load documents.</td>
            </tr>
        `;

        documentCount.textContent = "Unable to load documents";

        documentMessage.textContent = error.message;
        documentMessage.style.color = "red";

    }

}


// ==========================================
// DOWNLOAD DOCUMENT FROM GRIDFS
// ==========================================

async function downloadDocument(documentId, filename, button) {

    button.disabled = true;
    button.textContent = "Downloading...";

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/documents/${documentId}/download`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${documentsToken}`
                }
            }
        );

        if (!response.ok) {

            let errorMessage = "Document download failed";

            try {
                const data = await response.json();
                errorMessage = data.message || errorMessage;
            } catch (e) {
                // Keep the default error message
            }

            if (response.status === 401) {
                localStorage.removeItem("dms_token");
                window.location.href = "index.html";
                return;
            }

            throw new Error(errorMessage);

        }

        // Convert API response into a downloadable file
        const blob = await response.blob();

        const downloadUrl = window.URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = filename || "downloaded_document";

        document.body.appendChild(link);

        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);

    } catch (error) {

        alert(error.message);

    } finally {

        button.disabled = false;
        button.textContent = "Download";

    }

}


// ==========================================
// LOGOUT FUNCTIONALITY
// ==========================================

document.getElementById("logoutButton").addEventListener("click", function () {

    localStorage.removeItem("dms_token");

    window.location.href = "index.html";

});


// ==========================================
// LOAD DOCUMENTS WHEN PAGE OPENS
// ==========================================

loadDocuments();
