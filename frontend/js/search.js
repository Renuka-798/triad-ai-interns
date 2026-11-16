
const searchToken = localStorage.getItem("dms_token");

if (!searchToken) {
    window.location.href = "index.html";
}

const searchForm = document.getElementById("searchForm");

searchForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const query = document.getElementById("searchQuery").value.trim();
    const message = document.getElementById("searchMessage");
    const resultCount = document.getElementById("resultCount");
    const container = document.getElementById("searchResultsContainer");
    const button = document.getElementById("searchButton");

    if (!query) {
        message.textContent = "Please enter a search term.";
        message.style.color = "red";
        return;
    }

    button.disabled = true;
    button.textContent = "Searching...";
    message.textContent = "";
    resultCount.textContent = "Searching documents...";
    container.innerHTML = "";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${searchToken}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Search failed");
        }

        resultCount.textContent =
            `${data.total_results} document(s) found`;

        if (data.results.length === 0) {
            container.textContent = "No matching documents found.";
            return;
        }

        data.results.forEach(doc => {
            const card = document.createElement("div");
            card.className = "search-result-card";

            const title = document.createElement("h3");
            title.textContent = doc.title || doc.filename;

            const filename = document.createElement("p");
            filename.textContent = `Filename: ${doc.filename}`;

            const division = document.createElement("p");
            division.textContent = `Division: ${doc.division}`;

            const created = document.createElement("p");
            created.textContent =
                `Uploaded: ${new Date(doc.created_at).toLocaleString()}`;

            const metadata = document.createElement("p");
            metadata.className = "metadata-list";

            const metadataText = Object.entries(doc.metadata || {})
                .map(([key, value]) => `${key}: ${value}`)
                .join(" | ");

            metadata.textContent = metadataText
                ? `Metadata: ${metadataText}`
                : "No metadata available";

            const downloadButton = document.createElement("button");
            downloadButton.textContent = "Download Document";

            downloadButton.addEventListener("click", () => {
                downloadSearchDocument(doc.document_id, downloadButton);
            });

            card.appendChild(title);
            card.appendChild(filename);
            card.appendChild(division);
            card.appendChild(created);
            card.appendChild(metadata);
            card.appendChild(downloadButton);

            container.appendChild(card);
        });

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
        resultCount.textContent = "Search could not be completed.";

    } finally {
        button.disabled = false;
        button.textContent = "Search Documents";
    }
});

// Download a search result
async function downloadSearchDocument(documentId, button) {
    try {
        button.disabled = true;
        button.textContent = "Downloading...";

        const response = await fetch(
            `${API_BASE_URL}/api/documents/${documentId}/download`,
            {
                headers: {
                    "Authorization": `Bearer ${searchToken}`
                }
            }
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || "Download failed");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "document";
        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);

    } catch (error) {
        alert(error.message);

    } finally {
        button.disabled = false;
        button.textContent = "Download Document";
    }
}

// Logout
document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("dms_token");
    window.location.href = "index.html";
});
