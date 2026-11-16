# TRIAD DMS – Intelligent Document Management System

A secure, centralized Document Management System designed to simplify document storage, retrieval, organization, and controlled sharing across different organizational divisions.

## 📌 Project Overview

TRIAD DMS is a web-based document management application developed using Python Flask and MongoDB. It provides a centralized platform where users can upload, manage, retrieve, and share documents securely.

The application incorporates JWT-based authentication, division-based document access, access request management, and OCR-based text extraction to improve document accessibility and management.

## 🎯 Project Objectives

- Centralize organizational document management.
- Provide secure document upload and retrieval.
- Implement controlled access to documents across divisions.
- Enable users to request access to restricted documents.
- Simplify document searching and filtering.
- Extract text from documents using Optical Character Recognition (OCR).

## ✨ Key Features

### 1. User Authentication

- User login and authentication.
- JWT-based authentication.
- Password hashing for secure credential storage.
- Protected application pages.

### 2. Document Management

- Upload and store documents.
- View uploaded document details.
- Download stored documents.
- Maintain document metadata.

### 3. MongoDB GridFS Storage

- Store documents using MongoDB GridFS.
- Handle document storage separately from document metadata.
- Retrieve stored files when required.

### 4. Division-Based Access Control

- Organize document access based on organizational divisions.
- Restrict access to documents according to permissions.
- Support controlled cross-division document access.

### 5. Access Request Management

- Request access to documents belonging to other divisions.
- Receive access requests.
- Approve or reject document access requests.
- Manage access request status.

### 6. OCR-Based Document Processing

- Extract text from supported documents.
- Use PyMuPDF for PDF processing.
- Use Tesseract OCR through pytesseract for text recognition.

### 7. Document Filtering

- Filter documents using metadata.
- Support dynamic JSON-based metadata filtering.
- Improve document retrieval and organization.

## 🛠️ Technology Stack

| Technology     | Purpose                       |
| -------------- | ----------------------------- |
| Python         | Backend programming           |
| Flask          | Backend web framework         |
| HTML5          | Frontend structure            |
| CSS3           | Frontend styling              |
| JavaScript     | Frontend functionality        |
| MongoDB Atlas  | Cloud database                |
| MongoDB GridFS | Document file storage         |
| PyMongo        | MongoDB connectivity          |
| JWT            | Authentication                |
| PyMuPDF        | PDF processing                |
| Tesseract OCR  | Text extraction               |
| Pillow         | Image processing              |
| Flask-CORS     | Cross-origin resource sharing |
| Git & GitHub   | Version control               |

## 🏗️ System Architecture

The application follows a frontend-backend architecture.

```text
             USER
               |
               v
       FRONTEND INTERFACE
        HTML / CSS / JS
               |
               v
          FLASK SERVER
               |
       +-------+-------+
       |               |
       v               v
  AUTHENTICATION   DOCUMENT APIs
   JWT Tokens           |
       |                |
       +-------+--------+
               |
               v
          MONGODB ATLAS
               |
        +------+------+
        |             |
        v             v
   DOCUMENTS       METADATA
     GRIDFS        COLLECTIONS
        |
        v
     OCR PROCESSING
   PyMuPDF / Tesseract
```

## 📂 Project Structure

```text
TRIAD_DMS/
│
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   └── ocr.py
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── document.html
│   ├── css/
│   └── js/
│
├── run.py
├── requirements.txt
├── .env
├── .gitignore
├── check_mongo.py
└── test_tls.py
```

*Note: Refer to the actual folders and files in the repository for the complete project structure.*

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.x
- MongoDB Atlas account
- Git
- Tesseract OCR installed on the system

### Step 1: Clone the Repository

```bash
git clone https://github.com/Renuka-798/triad-ai-interns.git
```

### Step 2: Navigate to the Project

```bash
cd triad-ai-interns
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root and configure the MongoDB connection string and other application configuration values required by the backend.

Never commit actual database credentials, JWT secrets, or passwords to GitHub.

### Step 6: Configure Tesseract OCR

Install Tesseract OCR and ensure its executable is accessible to the application.

### Step 7: Run the Application

```bash
python run.py
```

### Step 8: Access the Application

Open the application using:

```text
http://127.0.0.1:5000
```

## 🔐 Security Implementation

- JWT-based user authentication.
- Password hashing.
- Protected document management operations.
- Division-based access restrictions.
- Controlled document access requests.
- Environment-based configuration for sensitive credentials.

## 🚀 Future Enhancements

- Advanced document search.
- Document version control.
- Enhanced role-based permissions.
- Document activity and audit logs.
- AI-powered document classification.
- Improved OCR accuracy and multilingual document support.

## 👩‍💻 Developer

**Renuka Chokkam**

B.Tech – Computer Science and Engineering (AI & ML)

GitHub: [Renuka-798](https://github.com/Renuka-798)

Project Repository: [TRIAD AI Interns](https://github.com/Renuka-798/triad-ai-interns)

---

⭐ If you find this project interesting, consider giving the repository a star!
