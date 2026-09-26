# Smart Voting System with Face Recognition

A professional educational prototype based on the project report **"Smart Voting System with Face Recognition"**.

The report describes a modular system with:
- facial biometric verification,
- a secure electronic voting interface,
- a relational database,
- Flask as the web framework,
- OpenCV/dlib/FaceNet-style face processing,
- duplicate-vote prevention,
- security and audit considerations.

> **Important:** This repository is a capstone/demo implementation, not a certified election system. Real elections require independently audited biometric systems, accessibility controls, legal compliance, strong privacy governance, secure infrastructure, verifiable audit mechanisms, and extensive field testing.

## Architecture

```text
Browser / Webcam
       |
       v
+---------------------+
| Flask Web Interface |
+----------+----------+
           |
           +-------------------+
           |                   |
           v                   v
 Face Verification        Voting Service
(OpenCV + face_recognition)     |
           |                   v
           +------------> SQLite DB
                             |
                 +-----------+-----------+
                 |                       |
              Voters                 Votes/Audit
```

## Main flow

1. Administrator registers a voter and captures one face image.
2. The system converts the face into an embedding and stores the embedding.
3. Voter enters their voter ID.
4. Browser captures a live webcam frame.
5. Server extracts a face embedding and compares it with the registered embedding.
6. Only a successfully verified voter can open the ballot.
7. A database uniqueness constraint prevents a second vote for the same voter.
8. An audit record is created for important actions.

## Project structure

```text
smart_voting_system/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── ballot.html
│   └── admin/
│       ├── login.html
│       ├── dashboard.html
│       └── results.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── camera.js
```

## Windows installation

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `face-recognition`/`dlib` fails to build on your machine, install a compatible pre-built dlib package for your Python version or use a Python version supported by your platform's available wheels.

### 3. Configure environment

Copy `.env.example` to `.env` and change the secret/admin password.

```powershell
copy .env.example .env
```

### 4. Start

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Admin:

```text
http://127.0.0.1:5000/admin/login
```

Default credentials are controlled by `.env`. Change them before use.

## Recommended development improvements

The report identifies liveness detection, scalability, accessibility, government-database integration, and field testing as future work. Before treating this as anything more than a classroom prototype, add:

- active/passive liveness detection;
- HTTPS and secure cookies;
- CSRF protection;
- rate limiting and account lockout;
- encrypted biometric storage with key management;
- database backups and recovery;
- role-based access control;
- tamper-evident audit logs;
- independent security testing;
- accessibility testing;
- privacy/retention policies;
- independent election/audit verification;
- high-load and failure testing.

## Testing checklist

- Register a voter with exactly one visible face.
- Verify the correct face.
- Verify a different face and confirm rejection.
- Attempt a second vote for the same voter and confirm rejection.
- Try an inactive/nonexistent candidate.
- Test malformed webcam payloads.
- Test camera permission denial.
- Test simultaneous vote attempts against the same voter.
- Test database backup/restore before changing production-like data.

## License

For academic/demo use. Add an appropriate open-source license before publishing as a reusable project.
