# Smart Voting System with Face Recognition

A **Flask-based educational voting prototype** that combines voter registration, password authentication, webcam-based facial verification, electronic voting, duplicate-vote prevention, and an administrator dashboard.

> **Important:** This project is an educational/capstone prototype. It is **not a certified or production-ready government election system**. Real-world deployment would require formal security audits, privacy and legal compliance, accessibility testing, liveness/anti-spoofing, secure infrastructure, independent verification, and election-specific certification.

---

## ✨ Features

### Voter Features

- Voter self-registration / Sign Up
- Voter Sign In using Voter ID or email
- Password hashing with Werkzeug
- Webcam-based face registration
- Live face verification before voting
- Electronic ballot interface
- One-vote-per-voter protection
- Automatic session cleanup after voting
- Mobile/LAN-friendly Flask server configuration

### Face Recognition

- OpenCV for image capture and processing
- `face_recognition` for face detection and facial embeddings
- Exactly-one-face validation during registration and verification
- Face-distance based matching
- Configurable matching tolerance in the application code

### Admin Features

- Administrator login
- Dashboard statistics
- Registered voter list
- Candidate management
- Vote results
- Audit log
- Demo election data

### Demo Election Data

The application automatically creates fictional demonstration candidates when the database has no candidates:

| Candidate | Party | Symbol |
|---|---|---|
| Aarav Mehta | Civic Progress Party (Demo) | CP |
| Diya Sharma | People First Party (Demo) | PF |
| Kabir Singh | Digital Future Party (Demo) | DF |
| Anaya Verma | Green Community Party (Demo) | GC |

These names and parties are **fictional demo data** created only for software demonstration.

---

## 🏗️ Technology Stack

- **Python 3.11**
- **Flask**
- **Flask-SQLAlchemy**
- **SQLAlchemy**
- **SQLite** for local development
- **PostgreSQL** supported through `DATABASE_URL`
- **OpenCV**
- **dlib / dlib-bin**
- **face-recognition**
- **NumPy**
- **Werkzeug**
- **HTML / CSS / JavaScript**
- Browser Web Camera API

---

## 📁 Project Structure

```text
smart-voting-system/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── data/
│   └── voting.db
│
├── docs/
│   ├── API.md
│   └── SECURITY.md
│
├── static/
│   ├── css/
│   └── js/
│
└── templates/
    ├── base.html
    ├── index.html
    ├── ballot.html
    ├── verify.html
    ├── auth/
    │   ├── signin.html
    │   └── signup.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        └── results.html
```

---

## 🔄 Application Flow

```text
                    ┌──────────────────┐
                    │   Welcome Page   │
                    └────────┬─────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
              Sign Up                 Sign In
                 │                       │
                 ▼                       ▼
          Register Voter          Password Check
                 │                       │
                 ▼                       ▼
          Capture Face            Face Verification
                 │                       │
                 └───────────┬───────────┘
                             ▼
                       Face Verified
                             │
                             ▼
                         Ballot Page
                             │
                             ▼
                        Select Candidate
                             │
                             ▼
                          Cast Vote
                             │
                             ▼
                    Duplicate Vote Check
                             │
                             ▼
                       Vote Recorded
```

---

## 🚀 Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/smart-voting-system.git
cd smart-voting-system
```

Replace `YOUR-USERNAME` and the repository name with your GitHub repository details.

### 2. Use Python 3.11

Python 3.11 is recommended for this project because the face-recognition/dlib dependency stack can be difficult to install on newer Python versions.

Check Python:

```bash
py -3.11 --version
```

Expected:

```text
Python 3.11.x
```

### 3. Create a virtual environment

Windows:

```powershell
py -3.11 -m venv .venv
```

If PowerShell activation is allowed:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by Windows policy, you can directly use:

```powershell
.\.venv\Scripts\python.exe
```

---

## 📦 Installing Dependencies on Windows

For this project, `dlib-bin` can be used when the normal `dlib` package cannot be built successfully.

Install the face-recognition stack:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install dlib-bin
.\.venv\Scripts\python.exe -m pip install face-recognition --no-deps
.\.venv\Scripts\python.exe -m pip install git+https://github.com/ageitgey/face_recognition_models
```

Install the Flask/application dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install Flask Flask-SQLAlchemy Werkzeug python-dotenv Pillow numpy opencv-python click
```

### SQLAlchemy Windows Application-Control Workaround

Some Windows environments can block SQLAlchemy's compiled extension with an error similar to:

```text
DLL load failed while importing _util_cy:
An Application Control policy has blocked this file.
```

If this occurs, reinstall SQLAlchemy from source with C extensions disabled:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall SQLAlchemy -y
$env:DISABLE_SQLALCHEMY_CEXT="1"
.\.venv\Scripts\python.exe -m pip install --no-binary=SQLAlchemy --no-cache-dir SQLAlchemy
```

Verify:

```powershell
.\.venv\Scripts\python.exe -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

---

## ▶️ Run the Application

From the folder containing `app.py`:

```powershell
.\.venv\Scripts\python.exe app.py
```

The application is configured to listen on:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

The server also uses:

```python
host="0.0.0.0"
```

so it can be accessed from another device on the same local network when the PC firewall and network configuration allow it.

---

## 📱 Open on a Mobile Phone

To test the application from a phone:

1. Connect the phone and PC to the same Wi-Fi network.
2. Start the Flask application.
3. On Windows, run:

```powershell
ipconfig
```

4. Find the PC's Wi-Fi **IPv4 Address**, for example:

```text
192.168.1.105
```

5. On the phone browser open:

```text
http://192.168.1.105:5000
```

Replace the example IP with your PC's actual IPv4 address.

### Camera Permission

The browser must be allowed to use the camera.

For local development, camera behavior can differ between browsers and addresses. For public deployment, use HTTPS so browser camera permissions work correctly.

---

## 👤 Voter Registration

The normal voter flow is:

1. Open the application.
2. Select **Sign Up**.
3. Enter:
   - Voter ID
   - Full Name
   - Email
   - Password
   - Confirm Password
4. Capture/register the face using the webcam.
5. Submit registration.
6. Sign in using Voter ID or email.
7. Complete face verification.
8. Open the ballot.
9. Select one candidate.
10. Submit the vote.

---

## 🔐 Duplicate Vote Protection

The application uses multiple application/database checks:

- `Voter.has_voted`
- Unique `Vote.voter_id`
- Existing vote lookup before inserting a new vote
- Verified voter session
- Transaction rollback on database errors

After a successful vote, the verified voter session is cleared.

---

## 🛠️ Admin Dashboard

The administrator can access:

```text
/admin/login
```

Default development credentials are created when no administrator exists:

```text
Username: admin
Password: admin123
```

### ⚠️ Change these credentials before any non-demo deployment.

Use environment variables:

```text
ADMIN_USERNAME=your-admin-name
ADMIN_PASSWORD=your-strong-password
SECRET_KEY=your-long-random-secret
```

---

## 📊 Database

### Local Development

The default database is:

```text
data/voting.db
```

SQLite is useful for local testing and demonstrations.

### Hosted Deployment

For a hosted deployment, use a persistent relational database such as PostgreSQL rather than relying on a local SQLite file on an ephemeral server filesystem.

Set:

```text
DATABASE_URL=your-database-connection-string
```

The application reads `DATABASE_URL` automatically.

---

## 🌐 Deployment

The project can be adapted for a production WSGI server such as Gunicorn.

Example:

```bash
gunicorn app:app
```

For a managed hosting service, configure the service with a Python 3.11 runtime, install dependencies, set environment variables, and use a persistent database.

### Production Environment Variables

```text
SECRET_KEY=<strong-random-secret>
ADMIN_USERNAME=<admin-username>
ADMIN_PASSWORD=<strong-password>
DATABASE_URL=<postgresql-connection-string>
FLASK_DEBUG=0
```

Never commit real passwords, secret keys, database credentials, or biometric data to GitHub.

---

## 🔒 Security Notes

This project stores facial embeddings and voting-related information. Treat biometric data as sensitive.

Before real-world use, additional work would be required for:

- Liveness / anti-spoofing
- Stronger authentication
- Encryption at rest
- Secure key management
- HTTPS
- Rate limiting
- CSRF protection
- Secure session configuration
- Database hardening
- Privacy and consent requirements
- Accessibility
- Independent security auditing
- Election-specific auditability
- Secure backups
- Disaster recovery
- Legal/regulatory compliance
- Formal testing and certification

The project report also identifies liveness detection, scalability, accessibility, government database integration, privacy considerations, and field testing as areas for future work.

---

## 🧪 Testing Checklist

Before demonstrating the project:

- [ ] Create a voter account
- [ ] Register a face
- [ ] Sign out
- [ ] Sign in using Voter ID
- [ ] Sign in using email
- [ ] Verify face
- [ ] Open ballot
- [ ] Select a demo candidate
- [ ] Submit vote
- [ ] Confirm vote appears in results
- [ ] Try voting a second time
- [ ] Test invalid password
- [ ] Test failed face verification
- [ ] Test multiple candidates
- [ ] Test admin login
- [ ] Check dashboard statistics
- [ ] Check audit logs
- [ ] Test mobile browser access

---

## 📚 Project Documentation

Additional documentation:

```text
docs/API.md
docs/SECURITY.md
```

These files contain API/security information for the project.

---

## 🎓 Project Purpose

The project demonstrates how computer vision, facial recognition, web application development, databases, authentication, and electronic voting concepts can be combined into a single educational prototype.

The accompanying project report describes the use of Python, OpenCV, dlib/FaceNet-style facial embeddings, Flask, and SQLite/MySQL as the main technologies and discusses future improvements such as liveness detection, scalability, accessibility, government database integration, privacy, and field testing.

---

## ⚠️ Disclaimer

This software is provided for **educational, research, and demonstration purposes**.

It should **not** be used to conduct an actual public election or to make real electoral decisions without appropriate legal authorization, independent security review, privacy protections, accessibility validation, operational controls, and formal certification.

---

## 👨‍💻 Author

**Smart Voting System with Face Recognition**

Educational / Capstone Project

---

## 📄 License

Add the license appropriate for your repository before publishing. If this is an academic project, you may also keep the repository private or specify the institution/project-specific usage terms.
