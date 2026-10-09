# Cloud Computing Service Portal

A full-stack cloud storage portal built with **Python Flask + SQLite + HTML/CSS/JavaScript**.

## Features

- User registration and secure password hashing
- Login/logout with Flask sessions
- Cloud-style dashboard
- File upload (up to 50 MB)
- File download
- File deletion
- Storage usage statistics
- Responsive modern UI
- SQLite database
- Ready for GitHub repository
- Ready for deployment on services that run Flask apps, such as Render

## Run locally in VS Code

### 1. Open the project folder

Open this folder in VS Code.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
.venv\Scripts\activate.bat
```

### 3. Install packages

```powershell
pip install -r requirements.txt
```

### 4. Start the server

```powershell
python app.py
```

Open:

http://127.0.0.1:5000

## GitHub

Create a GitHub repository and push the project files.

Do NOT upload:
- `.venv`
- `cloud_portal.db`
- files inside `uploads/`
- passwords or secret keys

## Deployment note

GitHub Pages only hosts static websites; it cannot run the Flask backend. For a working full-stack deployment, keep the code in GitHub and deploy the Flask application on a Python hosting service such as Render.

For production, use an external object-storage service (for example, S3-compatible storage) rather than the local `uploads` folder, because many cloud hosts use temporary filesystems.
