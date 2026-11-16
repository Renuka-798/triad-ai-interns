
const uploadToken = localStorage.getItem("dms_token");

if (!uploadToken) {
    window.location.href = "index.html";
}

// Load dynamic metadata fields
async function loadMetadataFields() {
    const container = document.getElementById("dynamicFields");

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/metadata-fields`,
            {
                headers: {
                    "Authorization": `Bearer ${uploadToken}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to load metadata fields");
        }

        container.innerHTML = "";

        if (!data.fields || data.fields.length === 0) {
            container.textContent = "No additional metadata fields configured.";
            return;
        }

        data.fields.forEach(field => {
            const group = document.createElement("div");
            group.className = "form-group";

            const label = document.createElement("label");
            label.textContent = field.field_name +
                (field.required ? " *" : "");

            const input = document.createElement(
                field.field_type === "dropdown" ? "select" : "input"
            );

            input.id = "metadata_" + field.field_id;
            input.dataset.fieldName = field.field_name;
            input.dataset.fieldType = field.field_type;

            if (field.required) {
                input.required = true;
            }

            if (field.field_type === "dropdown") {
                const placeholder = document.createElement("option");
                placeholder.value = "";
                placeholder.textContent = "Select " + field.field_name;
                input.appendChild(placeholder);

                field.options.forEach(option => {
                    const optionElement = document.createElement("option");
                    optionElement.value = option;
                    optionElement.textContent = option;
                    input.appendChild(optionElement);
                });

            } else if (field.field_type === "date") {
                input.type = "date";

            } else if (field.field_type === "number") {
                input.type = "number";

            } else {
                input.type = "text";
                input.placeholder = "Enter " + field.field_name;
            }

            group.appendChild(label);
            group.appendChild(input);
            container.appendChild(group);
        });

    } catch (error) {
        container.textContent = error.message;
    }
}

// Upload document
document.getElementById("uploadForm").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        const message = document.getElementById("uploadMessage");
        const button = document.getElementById("submitUpload");

        const fileInput = document.getElementById("file");
        const title = document.getElementById("title").value.trim();
        const file = fileInput.files[0];

        if (!file) {
            message.textContent = "Please select a document.";
            message.style.color = "red";
            return;
        }

        const metadata = {
            title: title
        };

        const metadataInputs = document.querySelectorAll(
            "#dynamicFields input, #dynamicFields select"
        );

        metadataInputs.forEach(input => {
            const value = input.value;

            if (value !== "") {
                if (input.dataset.fieldType === "number") {
                    metadata[input.dataset.fieldName] = Number(value);
                } else {
                    metadata[input.dataset.fieldName] = value;
                }
            }
        });

        const formData = new FormData();
        formData.append("file", file);
        formData.append("metadata", JSON.stringify(metadata));

        button.disabled = true;
        button.textContent = "Uploading...";
        message.textContent = "Uploading document...";
        message.style.color = "#294b96";

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/documents/upload`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${uploadToken}`
                    },
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || "Upload failed");
            }

            message.textContent =
                "Document uploaded successfully! OCR extracted " +
                data.ocr_text_length + " characters.";

            message.style.color = "green";

            document.getElementById("uploadForm").reset();

        } catch (error) {
            message.textContent = error.message;
            message.style.color = "red";

        } finally {
            button.disabled = false;
            button.textContent = "Upload Document";
        }
    }
);

// Logout
document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("dms_token");
    window.location.href = "index.html";
});

// Initialize
loadMetadataFields();
