import json
from datetime import datetime, timezone
from io import BytesIO
from flask import send_file
from app.ocr import extract_text

from bson import ObjectId
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app.models import (
    users_collection,
    documents_collection,
    access_requests_collection,
    metadata_fields_collection,
    fs
)

auth_bp = Blueprint("auth", __name__)


# --------------------------------
# 1. USER REGISTRATION API
# POST /api/auth/register
# --------------------------------

@auth_bp.route("/api/auth/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    division = data.get("division", "").strip()

    # Validate required fields
    if not name or not email or not password or not division:
        return jsonify({
            "status": "error",
            "message": "Name, email, password and division are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "status": "error",
            "message": "Password must contain at least 8 characters"
        }), 400

    # Check whether email already exists
    existing_user = users_collection.find_one({"email": email})

    if existing_user:
        return jsonify({
            "status": "error",
            "message": "Email already registered"
        }), 409

    # Hash password before storing
    hashed_password = generate_password_hash(password)

    user = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "division": division,
        "role": "user"
    }

    result = users_collection.insert_one(user)

    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": str(result.inserted_id),
            "name": name,
            "email": email,
            "division": division,
            "role": "user"
        }
    }), 201


# --------------------------------
# 2. USER LOGIN API
# POST /api/auth/login
# --------------------------------

@auth_bp.route("/api/auth/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    # Find user by email
    user = users_collection.find_one({"email": email})

    if not user or not check_password_hash(
        user.get("password", ""), password
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    # Generate JWT token
    access_token = create_access_token(
        identity=str(user["_id"])
    )

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "division": user["division"],
            "role": user["role"]
        }
    }), 200

# --------------------------------
# 3. DOCUMENT UPLOAD API
# POST /api/documents/upload
# --------------------------------



@auth_bp.route("/api/documents/upload", methods=["POST"])
@jwt_required()
def upload_document():

    # Get logged-in user's ID
    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    # Check uploaded file
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file provided"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "status": "error",
            "message": "No file selected"
        }), 400

    # Read dynamic metadata
    metadata_json = request.form.get("metadata", "{}")

    try:
        metadata = json.loads(metadata_json)

        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a JSON object")

    except (json.JSONDecodeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Invalid metadata JSON"
        }), 400

    # Keep title as a reserved system field
    title = metadata.get("title", file.filename)

    if not isinstance(title, str) or not title.strip():
        return jsonify({
            "status": "error",
            "message": "Title must be a non-empty string"
        }), 400

    # Get configured metadata field definitions
    configured_fields = list(metadata_fields_collection.find())

    configured_names = {
        field["field_name"]: field
        for field in configured_fields
    }

    # Reject fields that are not configured
    # The title field is reserved for the document title
    allowed_names = set(configured_names.keys()) | {"title"}

    unknown_fields = [
        key for key in metadata.keys()
        if key not in allowed_names
    ]

    if unknown_fields:
        return jsonify({
            "status": "error",
            "message": "Unconfigured metadata fields",
            "unknown_fields": unknown_fields
        }), 400

    # Check required fields
    missing_fields = []

    for field in configured_fields:
        field_name = field["field_name"]

        if field.get("required", False):
            value = metadata.get(field_name)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                missing_fields.append(field_name)

    if missing_fields:
        return jsonify({
            "status": "error",
            "message": "Required metadata fields are missing",
            "missing_fields": missing_fields
        }), 400

    # Validate metadata values according to their types
    for field in configured_fields:

        field_name = field["field_name"]

        if field_name not in metadata:
            continue

        value = metadata[field_name]
        field_type = field["field_type"]

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            continue

        if field_type == "text":
            valid = isinstance(value, str)

        elif field_type == "number":
            valid = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        elif field_type == "date":
            valid = False

            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                    valid = True
                except ValueError:
                    pass

        elif field_type == "dropdown":
            valid = (
                isinstance(value, str)
                and value in field.get("options", [])
            )

        else:
            valid = False

        if not valid:
            return jsonify({
                "status": "error",
                "message": "Invalid metadata value",
                "field": field_name,
                "expected_type": field_type,
                "received_value": value
            }), 400

    # Secure filename
    filename = secure_filename(file.filename)

    if not filename:
        return jsonify({
            "status": "error",
            "message": "Invalid filename"
        }), 400

    content_type = file.content_type or "application/octet-stream"

    # Read file bytes
    file_bytes = file.read()

    if not file_bytes:
        return jsonify({
            "status": "error",
            "message": "Uploaded file is empty"
        }), 400

    # Extract text using OCR
    try:
        extracted_text = extract_text(file_bytes, filename)
    except Exception as e:
        print("OCR extraction failed:", str(e))
        extracted_text = ""

    # Store file in GridFS
    file_id = fs.upload_from_stream(
        filename,
        BytesIO(file_bytes),
        metadata={
            "uploader_id": user_id,
            "division": user["division"],
            "content_type": content_type
        }
    )

    # Store document information
    document = {
        "file_id": file_id,
        "filename": filename,
        "title": title.strip(),
        "content_type": content_type,
        "uploader_id": user_id,
        "division": user["division"],
        "metadata": metadata,
        "extracted_text": extracted_text,
        "created_at": datetime.now(timezone.utc)
    }

    result = documents_collection.insert_one(document)

    return jsonify({
        "status": "success",
        "message": "Document uploaded successfully",
        "document": {
            "id": str(result.inserted_id),
            "file_id": str(file_id),
            "filename": filename,
            "division": user["division"],
            "metadata": metadata,
            "ocr_text_length": len(extracted_text),
            "ocr_status": (
                "Text extracted successfully"
                if extracted_text
                else "No text extracted"
            )
        }
    }), 201


# --------------------------------
# 4. GET DOCUMENTS API
# GET /api/documents
# --------------------------------

@auth_bp.route("/api/documents", methods=["GET"])
@jwt_required()
def get_documents():

    # Get logged-in user
    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    # Only retrieve documents from the user's division
    query = {
        "division": user["division"]
    }

    # Apply dynamic metadata filters
    for key, value in request.args.items():

        # Convert numeric filter values when possible
        if value.isdigit():
            value = int(value)

        query[f"metadata.{key}"] = value

    # Retrieve matching documents
    documents = documents_collection.find(query)

    result = []

    for doc in documents:

        result.append({
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "title": doc.get("title", doc["filename"]),
            "division": doc["division"],
            "metadata": doc.get("metadata", {}),
            "created_at": doc["created_at"].isoformat()
        })

    return jsonify({
        "status": "success",
        "total_documents": len(result),
        "division": user["division"],
        "documents": result
    }), 200

# --------------------------------
# 5. DOCUMENT DOWNLOAD API
# GET /api/documents/<doc_id>/download
# --------------------------------

@auth_bp.route(
    "/api/documents/<doc_id>/download",
    methods=["GET"]
)
@jwt_required()
def download_document(doc_id):

    # Validate document ID
    if not ObjectId.is_valid(doc_id):
        return jsonify({
            "status": "error",
            "message": "Invalid document ID"
        }), 400

    # Identify logged-in user
    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    # Find document
    document = documents_collection.find_one({
        "_id": ObjectId(doc_id)
    })

    if not document:
        return jsonify({
            "status": "error",
            "message": "Document not found"
        }), 404

    # Check division access
    if document["division"]!=user["division"]:
        approved_request=access_requests_collection.find_one({
            "document_id":ObjectId(doc_id),
            "requester_id":user_id,
            "status":"Approved"
        })
        if not approved_request:
            return jsonify({
                "status": "error",
                "message": "Access denied. Document belongs to another division."
            }), 403

    try:
        # Retrieve file from GridFS
        grid_out = fs.open_download_stream(
            document["file_id"]
        )

        file_data = grid_out.read()

        return send_file(
            BytesIO(file_data),
            mimetype=document.get(
                "content_type",
                "application/octet-stream"
            ),
            as_attachment=True,
            download_name=document["filename"]
        )

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to download document"
        }), 404
# --------------------------------
# 6. ACCESS REQUEST API
# POST /api/access/request
# --------------------------------

@auth_bp.route("/api/access/request", methods=["POST"])
@jwt_required()
def request_access():

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    data = request.get_json(silent=True) or {}
    doc_id = data.get("doc_id", "")

    if not ObjectId.is_valid(doc_id):
        return jsonify({
            "status": "error",
            "message": "Valid doc_id is required"
        }), 400

    document = documents_collection.find_one({
        "_id": ObjectId(doc_id)
    })

    if not document:
        return jsonify({
            "status": "error",
            "message": "Document not found"
        }), 404

    # Same-division users already have access
    if document["division"] == user["division"]:
        return jsonify({
            "status": "error",
            "message": "You already have access to this document"
        }), 400

    # Check for an existing pending request
    existing = access_requests_collection.find_one({
        "document_id": ObjectId(doc_id),
        "requester_id": user_id,
        "status": "Pending"
    })

    if existing:
        return jsonify({
            "status": "error",
            "message": "Access request already pending"
        }), 409

    access_request = {
        "document_id": ObjectId(doc_id),
        "requester_id": user_id,
        "requester_division": user["division"],
        "owner_division": document["division"],
        "status": "Pending",
        "created_at": datetime.now(timezone.utc)
    }

    result = access_requests_collection.insert_one(
        access_request
    )

    return jsonify({
        "status": "success",
        "message": "Access request submitted successfully",
        "request_id": str(result.inserted_id),
        "status_of_request": "Pending"
    }), 201

# --------------------------------
# 7. APPROVE ACCESS REQUEST API
# POST /api/access/approve
# --------------------------------

@auth_bp.route("/api/access/approve", methods=["POST"])
@jwt_required()
def approve_access():

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    data = request.get_json(silent=True) or {}
    request_id = data.get("request_id", "")

    if not ObjectId.is_valid(request_id):
        return jsonify({
            "status": "error",
            "message": "Valid request_id is required"
        }), 400

    access_request = access_requests_collection.find_one({
        "_id": ObjectId(request_id)
    })

    if not access_request:
        return jsonify({
            "status": "error",
            "message": "Access request not found"
        }), 404

    # Only the document-owning division or an admin can approve
    if (
        user["division"] != access_request["owner_division"]
        and user["role"] != "admin"
    ):
        return jsonify({
            "status": "error",
            "message": "You are not authorized to approve this request"
        }), 403

    if access_request["status"] != "Pending":
        return jsonify({
            "status": "error",
            "message": "Request has already been processed"
        }), 400

    access_requests_collection.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": "Approved",
                "approved_by": user_id,
                "reviewed_at": datetime.now(timezone.utc)
            }
        }
    )

    return jsonify({
        "status": "success",
        "message": "Access request approved successfully",
        "request_id": request_id,
        "status_of_request": "Approved"
    }), 200
# --------------------------------
# 8. REJECT ACCESS REQUEST API
# POST /api/access/reject
# --------------------------------

@auth_bp.route("/api/access/reject", methods=["POST"])
@jwt_required()
def reject_access():

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    data = request.get_json(silent=True) or {}
    request_id = data.get("request_id", "")

    if not ObjectId.is_valid(request_id):
        return jsonify({
            "status": "error",
            "message": "Valid request_id is required"
        }), 400

    access_request = access_requests_collection.find_one({
        "_id": ObjectId(request_id)
    })

    if not access_request:
        return jsonify({
            "status": "error",
            "message": "Access request not found"
        }), 404

    if (
        user["division"] != access_request["owner_division"]
        and user["role"] != "admin"
    ):
        return jsonify({
            "status": "error",
            "message": "You are not authorized to reject this request"
        }), 403

    if access_request["status"] != "Pending":
        return jsonify({
            "status": "error",
            "message": "Request has already been processed"
        }), 400

    access_requests_collection.update_one(
        {"_id": ObjectId(request_id)},
        {
            "$set": {
                "status": "Rejected",
                "rejected_by": user_id,
                "reviewed_at": datetime.now(timezone.utc)
            }
        }
    )

    return jsonify({
        "status": "success",
        "message": "Access request rejected successfully"
    }), 200

# --------------------------------
# 9. ACCESS REQUESTS INBOX API
# GET /api/access/requests
# --------------------------------

@auth_bp.route("/api/access/requests", methods=["GET"])
@jwt_required()
def get_access_requests():

    # Get the logged-in user's ID
    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    # Show requests received by this user's division
    query = {
        "owner_division": user["division"]
    }

    # Optional status filter: Pending, Approved, or Rejected
    status_filter = request.args.get("status")

    if status_filter:
        allowed_statuses = ["Pending", "Approved", "Rejected"]

        if status_filter not in allowed_statuses:
            return jsonify({
                "status": "error",
                "message": "Invalid status filter"
            }), 400

        query["status"] = status_filter

    # Get requests, newest first
    access_requests = access_requests_collection.find(
        query
    ).sort("created_at", -1)

    result = []

    for access_request in access_requests:

        # Find the document associated with the request
        document = documents_collection.find_one({
            "_id": access_request["document_id"]
        })

        # Find the user who requested access
        requester = users_collection.find_one({
            "_id": ObjectId(access_request["requester_id"])
        })

        result.append({
            "request_id": str(access_request["_id"]),
            "document_id": str(access_request["document_id"]),
            "document_title": (
                document.get("title", document["filename"])
                if document else "Document not found"
            ),
            "requester_id": access_request["requester_id"],
            "requester_name": (
                requester.get("name", "Unknown user")
                if requester else "Unknown user"
            ),
            "requester_email": (
                requester.get("email", "")
                if requester else ""
            ),
            "requester_division": access_request["requester_division"],
            "owner_division": access_request["owner_division"],
            "status": access_request["status"],
            "created_at": access_request["created_at"].isoformat()
        })

    return jsonify({
        "status": "success",
        "division": user["division"],
        "total_requests": len(result),
        "requests": result
    }), 200

# --------------------------------
# ADVANCED DOCUMENT SEARCH API
# GET /api/search?q=<query>
# --------------------------------

def search_metadata(value, search_term):

    search_term = search_term.lower()

    if isinstance(value, dict):
        return any(
            search_metadata(v, search_term)
            for v in value.values()
        )

    elif isinstance(value, list):
        return any(
            search_metadata(item, search_term)
            for item in value
        )

    else:
        return search_term in str(value).lower()


@auth_bp.route("/api/search", methods=["GET"])
@jwt_required()
def search_documents():

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    # Get search query
    search_term = request.args.get("q", "").strip()

    if not search_term:
        return jsonify({
            "status": "error",
            "message": "Please provide a search query"
        }), 400

    # Find documents with approved cross-division access
    approved_requests = access_requests_collection.find({
        "requester_id": user_id,
        "status": "Approved"
    })

    approved_document_ids = [
        access_request["document_id"]
        for access_request in approved_requests
    ]

    # Restrict search to accessible documents
    access_filter = {
        "$or": [
            {"division": user["division"]},
            {"_id": {"$in": approved_document_ids}}
        ]
    }

    documents = documents_collection.find(
        access_filter
    ).sort("created_at", -1)

    results = []

    for document in documents:

        title = str(document.get("title", ""))
        filename = str(document.get("filename", ""))
        extracted_text = str(
            document.get("extracted_text", "")
        )
        metadata = document.get("metadata", {})

        # Search title, filename, OCR text and metadata
        matched = (
            search_term.lower() in title.lower()
            or search_term.lower() in filename.lower()
            or search_term.lower() in extracted_text.lower()
            or search_metadata(metadata, search_term)
        )

        if matched:

            results.append({
                "document_id": str(document["_id"]),
                "title": title,
                "filename": filename,
                "division": document["division"],
                "metadata": metadata,
                "extracted_text": extracted_text,
                "created_at": document["created_at"].isoformat()
            })

    return jsonify({
        "status": "success",
        "query": search_term,
        "total_results": len(results),
        "results": results
    }), 200


@auth_bp.route("/api/metadata-fields", methods=["GET"])
@jwt_required()
def get_metadata_fields():

    fields = list(metadata_fields_collection.find())

    result = []

    for field in fields:
        result.append({
            "field_id": str(field["_id"]),
            "field_name": field["field_name"],
            "field_type": field["field_type"],
            "options": field.get("options", []),
            "required": field.get("required", False)
        })

    return jsonify({
        "status": "success",
        "total_fields": len(result),
        "fields": result
    }), 200
@auth_bp.route("/api/metadata-fields", methods=["POST"])
@jwt_required()
def add_metadata_field():

    user_id = get_jwt_identity()

    # Check whether the logged-in user is an admin
    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    if user.get("role") != "admin":
        return jsonify({
            "status": "error",
            "message": "Only admins can add metadata fields"
        }), 403

    # Read request data
    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Request body is required"
        }), 400

    field_name = data.get("field_name", "").strip()
    field_type = data.get("field_type", "").lower()
    options = data.get("options", [])
    required = data.get("required", False)

    # Validate field name
    if not field_name:
        return jsonify({
            "status": "error",
            "message": "Field name is required"
        }), 400

    # Validate field type
    allowed_types = ["text", "number", "date", "dropdown"]

    if field_type not in allowed_types:
        return jsonify({
            "status": "error",
            "message": "Invalid field type"
        }), 400

    # Validate required
    if not isinstance(required, bool):
        return jsonify({
            "status": "error",
            "message": "Required must be true or false"
        }), 400

    # Validate dropdown options
    if field_type == "dropdown":
        if not isinstance(options, list) or not options:
            return jsonify({
                "status": "error",
                "message": "Dropdown fields must have options"
            }), 400

        if not all(
            isinstance(option, str) and option.strip()
            for option in options
        ):
            return jsonify({
                "status": "error",
                "message": "Dropdown options must be non-empty strings"
            }), 400
    else:
        options = []

    # Check for duplicate field names (case-insensitive)
    existing_fields = metadata_fields_collection.find()

    for existing in existing_fields:
        if existing["field_name"].lower() == field_name.lower():
            return jsonify({
                "status": "error",
                "message": "This metadata field already exists"
            }), 409

    # Save field definition
    metadata_field = {
        "field_name": field_name,
        "field_type": field_type,
        "options": options,
        "required": required,
        "created_at": datetime.now(timezone.utc),
        "created_by": user_id
    }

    result = metadata_fields_collection.insert_one(metadata_field)

    return jsonify({
        "status": "success",
        "message": "Metadata field created successfully",
        "field": {
            "field_id": str(result.inserted_id),
            "field_name": field_name,
            "field_type": field_type,
            "options": options,
            "required": required
        }
    }), 201

@auth_bp.route("/api/metadata-fields/<field_id>", methods=["PUT"])
@jwt_required()
def update_metadata_field(field_id):

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    if user.get("role") != "admin":
        return jsonify({
            "status": "error",
            "message": "Only admins can update metadata fields"
        }), 403

    if not ObjectId.is_valid(field_id):
        return jsonify({
            "status": "error",
            "message": "Invalid field ID"
        }), 400

    field = metadata_fields_collection.find_one({
        "_id": ObjectId(field_id)
    })

    if not field:
        return jsonify({
            "status": "error",
            "message": "Metadata field not found"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Request body is required"
        }), 400

    field_name = data.get("field_name", field["field_name"]).strip()
    field_type = data.get("field_type", field["field_type"]).lower()
    options = data.get("options", field.get("options", []))
    required = data.get("required", field.get("required", False))

    if not field_name:
        return jsonify({
            "status": "error",
            "message": "Field name cannot be empty"
        }), 400

    allowed_types = ["text", "number", "date", "dropdown"]

    if field_type not in allowed_types:
        return jsonify({
            "status": "error",
            "message": "Invalid field type"
        }), 400

    if not isinstance(required, bool):
        return jsonify({
            "status": "error",
            "message": "Required must be true or false"
        }), 400

    if field_type == "dropdown":
        if not isinstance(options, list) or not options:
            return jsonify({
                "status": "error",
                "message": "Dropdown fields must have options"
            }), 400

        if not all(
            isinstance(option, str) and option.strip()
            for option in options
        ):
            return jsonify({
                "status": "error",
                "message": "Dropdown options must be non-empty strings"
            }), 400
    else:
        options = []

    duplicate = metadata_fields_collection.find_one({
        "field_name": {
            "$regex": "^" + __import__("re").escape(field_name) + "$",
            "$options": "i"
        },
        "_id": {"$ne": ObjectId(field_id)}
    })

    if duplicate:
        return jsonify({
            "status": "error",
            "message": "Another metadata field already uses this name"
        }), 409

    metadata_fields_collection.update_one(
        {"_id": ObjectId(field_id)},
        {
            "$set": {
                "field_name": field_name,
                "field_type": field_type,
                "options": options,
                "required": required,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return jsonify({
        "status": "success",
        "message": "Metadata field updated successfully"
    }), 200
@auth_bp.route("/api/metadata-fields/<field_id>", methods=["DELETE"])
@jwt_required()
def delete_metadata_field(field_id):

    user_id = get_jwt_identity()

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    if user.get("role") != "admin":
        return jsonify({
            "status": "error",
            "message": "Only admins can delete metadata fields"
        }), 403

    if not ObjectId.is_valid(field_id):
        return jsonify({
            "status": "error",
            "message": "Invalid field ID"
        }), 400

    result = metadata_fields_collection.delete_one({
        "_id": ObjectId(field_id)
    })

    if result.deleted_count == 0:
        return jsonify({
            "status": "error",
            "message": "Metadata field not found"
        }), 404

    return jsonify({
        "status": "success",
        "message": "Metadata field deleted successfully"
    }), 200