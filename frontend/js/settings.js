
const settingsToken = localStorage.getItem("dms_token");

if (!settingsToken) {
    window.location.href = "index.html";
}

let editingFieldId = null;

const metadataForm = document.getElementById("metadataForm");
const fieldName = document.getElementById("fieldName");
const fieldType = document.getElementById("fieldType");
const fieldOptions = document.getElementById("fieldOptions");
const fieldRequired = document.getElementById("fieldRequired");
const optionsContainer = document.getElementById("optionsContainer");
const fieldsContainer = document.getElementById("metadataFieldsContainer");
const formMessage = document.getElementById("formMessage");
const fieldsMessage = document.getElementById("fieldsMessage");
const saveButton = document.getElementById("saveFieldButton");
const cancelButton = document.getElementById("cancelEditButton");
const formHeading = document.getElementById("formHeading");

// Common API headers
function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${settingsToken}`
    };
}

// Show dropdown options input only for dropdown fields
fieldType.addEventListener("change", function () {
    optionsContainer.style.display =
        fieldType.value === "dropdown" ? "block" : "none";
});

// Load metadata fields from MongoDB
async function loadMetadataFields() {
    fieldsContainer.textContent = "Loading metadata fields...";
    fieldsMessage.textContent = "";

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/metadata-fields`,
            {
                method: "GET",
                headers: getHeaders()
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to load metadata fields");
        }

        fieldsContainer.innerHTML = "";

        if (!data.fields || data.fields.length === 0) {
            fieldsContainer.textContent = "No metadata fields configured.";
            return;
        }

        data.fields.forEach(field => {
            const card = document.createElement("div");
            card.className = "request-card";

            const name = document.createElement("h3");
            name.textContent = field.field_name;

            const type = document.createElement("p");
            type.textContent = `Field Type: ${field.field_type}`;

            const required = document.createElement("p");
            required.textContent = `Required: ${field.required ? "Yes" : "No"}`;

            card.appendChild(name);
            card.appendChild(type);
            card.appendChild(required);

            if (field.field_type === "dropdown") {
                const options = document.createElement("p");
                options.textContent =
                    `Options: ${(field.options || []).join(", ")}`;
                card.appendChild(options);
            }

            const actions = document.createElement("div");
            actions.className = "request-actions";

            const editButton = document.createElement("button");
            editButton.textContent = "Edit";
            editButton.className = "approve-button";
            editButton.addEventListener("click", function () {
                editMetadataField(field);
            });

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";
            deleteButton.className = "reject-button";
            deleteButton.addEventListener("click", function () {
                deleteMetadataField(field.field_id, field.field_name);
            });

            actions.appendChild(editButton);
            actions.appendChild(deleteButton);
            card.appendChild(actions);

            fieldsContainer.appendChild(card);
        });

    } catch (error) {
        fieldsContainer.textContent = "";
        fieldsMessage.textContent = error.message;
        fieldsMessage.style.color = "red";
    }
}

// Add or update a metadata field
metadataForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = fieldName.value.trim();
    const type = fieldType.value;
    const required = fieldRequired.checked;

    const payload = {
        field_name: name,
        field_type: type,
        required: required
    };

    if (type === "dropdown") {
        payload.options = fieldOptions.value
            .split(",")
            .map(option => option.trim())
            .filter(option => option !== "");

        if (payload.options.length === 0) {
            formMessage.textContent =
                "Please enter at least one dropdown option.";
            formMessage.style.color = "red";
            return;
        }
    }

    const isEditing = editingFieldId !== null;

    const url = isEditing
        ? `${API_BASE_URL}/api/metadata-fields/${editingFieldId}`
        : `${API_BASE_URL}/api/metadata-fields`;

    const method = isEditing ? "PUT" : "POST";

    saveButton.disabled = true;
    saveButton.textContent = "Saving...";

    try {
        const response = await fetch(url, {
            method: method,
            headers: getHeaders(),
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to save metadata field");
        }

        formMessage.textContent = data.message || "Metadata field saved successfully!";
        formMessage.style.color = "green";

        resetForm();
        await loadMetadataFields();

    } catch (error) {
        formMessage.textContent = error.message;
        formMessage.style.color = "red";
    } finally {
        saveButton.disabled = false;
        saveButton.textContent = "Save Metadata Field";
    }
});

// Fill the form when Edit is clicked
function editMetadataField(field) {
    editingFieldId = field.field_id;

    fieldName.value = field.field_name;
    fieldType.value = field.field_type;
    fieldRequired.checked = field.required;

    fieldOptions.value = (field.options || []).join(", ");

    optionsContainer.style.display =
        field.field_type === "dropdown" ? "block" : "none";

    formHeading.textContent = "Edit Metadata Field";
    saveButton.textContent = "Update Metadata Field";
    cancelButton.style.display = "inline-block";

    formMessage.textContent = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Delete a metadata field
async function deleteMetadataField(fieldId, name) {
    const confirmed = window.confirm(
        `Are you sure you want to delete "${name}"?`
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/metadata-fields/${fieldId}`,
            {
                method: "DELETE",
                headers: getHeaders()
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to delete metadata field");
        }

        fieldsMessage.textContent =
            data.message || "Metadata field deleted successfully!";
        fieldsMessage.style.color = "green";

        if (editingFieldId === fieldId) {
            resetForm();
        }

        await loadMetadataFields();

    } catch (error) {
        fieldsMessage.textContent = error.message;
        fieldsMessage.style.color = "red";
    }
}

// Reset the form after saving or cancelling
function resetForm() {
    metadataForm.reset();
    editingFieldId = null;

    optionsContainer.style.display = "none";
    formHeading.textContent = "Add Metadata Field";
    saveButton.textContent = "Save Metadata Field";
    cancelButton.style.display = "none";
}

cancelButton.addEventListener("click", resetForm);

// Logout
document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("dms_token");
    window.location.href = "index.html";
});

// Initial load
loadMetadataFields();
