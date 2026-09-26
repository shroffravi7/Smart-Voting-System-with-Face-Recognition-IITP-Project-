import os
import json
import base64
from functools import wraps
from datetime import datetime, timezone

import cv2
import face_recognition
import numpy as np

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


# ============================================================
# APP CONFIGURATION
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "smart-voting-demo-change-this-secret-key"
)

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url
    or f"sqlite:///{os.path.join(BASE_DIR, 'data', 'voting.db')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# DATABASE MODELS
# ============================================================

class Voter(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    voter_id = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(160),
        unique=True,
        nullable=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    face_encoding = db.Column(
        db.Text,
        nullable=False
    )

    has_voted = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class Candidate(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    party = db.Column(
        db.String(120),
        nullable=True
    )

    symbol = db.Column(
        db.String(120),
        nullable=True
    )

    active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class Vote(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    voter_id = db.Column(
        db.Integer,
        db.ForeignKey("voter.id"),
        unique=True,
        nullable=False
    )

    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("candidate.id"),
        nullable=False
    )

    cast_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    voter = db.relationship(
        "Voter",
        backref=db.backref(
            "vote",
            uselist=False
        )
    )

    candidate = db.relationship(
        "Candidate",
        backref="votes"
    )


class Admin(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )


class AuditLog(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    action = db.Column(
        db.String(120),
        nullable=False
    )

    actor = db.Column(
        db.String(120),
        nullable=True
    )

    details = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# ============================================================
# ADMIN AUTH DECORATOR
# ============================================================

def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if "admin_id" not in session:
            return redirect(
                url_for("admin_login")
            )

        return view(*args, **kwargs)

    return wrapped


# ============================================================
# AUDIT LOG
# ============================================================

def log_event(
    action,
    actor=None,
    details=None
):

    db.session.add(
        AuditLog(
            action=action,
            actor=actor,
            details=details
        )
    )

    db.session.commit()


# ============================================================
# FACE IMAGE FUNCTIONS
# ============================================================

def decode_image(data_url):
    """
    Convert browser webcam base64 image
    into RGB numpy array.
    """

    if not data_url or "," not in data_url:
        raise ValueError(
            "Invalid image data."
        )

    raw = base64.b64decode(
        data_url.split(",", 1)[1]
    )

    image = cv2.imdecode(
        np.frombuffer(
            raw,
            np.uint8
        ),
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError(
            "Could not decode image."
        )

    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


def extract_encoding(image_rgb):

    locations = face_recognition.face_locations(
        image_rgb,
        model="hog"
    )

    if len(locations) != 1:

        raise ValueError(
            "Exactly one face must be visible. "
            "Keep only your face inside the frame."
        )

    encodings = face_recognition.face_encodings(
        image_rgb,
        locations
    )

    if not encodings:

        raise ValueError(
            "Could not create a face embedding."
        )

    return encodings[0]


def compare_face(
    stored_json,
    live_encoding,
    tolerance=0.48
):

    stored = np.array(
        json.loads(stored_json),
        dtype=np.float64
    )

    distance = float(
        face_recognition.face_distance(
            [stored],
            live_encoding
        )[0]
    )

    return (
        distance <= tolerance,
        distance
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    candidates = (
        Candidate.query
        .filter_by(active=True)
        .order_by(Candidate.id)
        .all()
    )

    return render_template(
        "index.html",
        candidates=candidates
    )


# ============================================================
# VOTER SIGN UP
# ============================================================

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    if request.method == "POST":

        voter_id = request.form.get(
            "voter_id",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower() or None

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        image = request.form.get(
            "image"
        )

        # Required fields
        if (
            not voter_id
            or not full_name
            or not email
            or not password
            or not image
        ):

            flash(
                "All registration fields and a face photo are required.",
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        # Password length
        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        # Password confirmation
        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        # Existing voter ID
        if Voter.query.filter_by(
            voter_id=voter_id
        ).first():

            flash(
                "Voter ID already exists. Please sign in.",
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        # Existing email
        if Voter.query.filter_by(
            email=email
        ).first():

            flash(
                "Email is already registered. Please sign in.",
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        # Face encoding
        try:

            encoding = extract_encoding(
                decode_image(image)
            )

        except ValueError as exc:

            flash(
                str(exc),
                "error"
            )

            return render_template(
                "auth/signup.html"
            )

        voter = Voter(
            voter_id=voter_id,
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(
                password
            ),
            face_encoding=json.dumps(
                encoding.tolist()
            )
        )

        db.session.add(voter)
        db.session.commit()

        log_event(
            "VOTER_SELF_REGISTERED",
            voter_id,
            f"email={email}"
        )

        flash(
            "Registration successful. Please sign in to continue.",
            "success"
        )

        return redirect(
            url_for("signin")
        )

    return render_template(
        "auth/signup.html"
    )


# ============================================================
# VOTER SIGN IN
# ============================================================

@app.route(
    "/signin",
    methods=["GET", "POST"]
)
def signin():

    if request.method == "POST":

        login = request.form.get(
            "login",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        voter = Voter.query.filter(
            (Voter.voter_id == login)
            |
            (Voter.email == login)
        ).first()

        if (
            voter
            and voter.password_hash
            and check_password_hash(
                voter.password_hash,
                password
            )
        ):

            if voter.has_voted:

                flash(
                    "This account has already cast its vote.",
                    "error"
                )

                return render_template(
                    "auth/signin.html"
                )

            session["voter_auth_id"] = voter.id

            log_event(
                "VOTER_SIGNED_IN",
                voter.voter_id
            )

            return redirect(
                url_for("verify_page")
            )

        flash(
            "Invalid voter ID/email or password.",
            "error"
        )

    return render_template(
        "auth/signin.html"
    )


# ============================================================
# SIGN OUT
# ============================================================

@app.route("/signout")
def signout():

    session.pop(
        "voter_auth_id",
        None
    )

    session.pop(
        "verified_voter_id",
        None
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# FACE VERIFICATION PAGE
# ============================================================

@app.route("/verify-page")
def verify_page():

    voter_pk = session.get(
        "voter_auth_id"
    )

    if not voter_pk:

        return redirect(
            url_for("signin")
        )

    voter = db.session.get(
        Voter,
        voter_pk
    )

    if not voter or voter.has_voted:

        session.pop(
            "voter_auth_id",
            None
        )

        return redirect(
            url_for("signin")
        )

    return render_template(
        "verify.html",
        voter=voter
    )


# ============================================================
# FACE VERIFICATION API
# ============================================================

@app.route(
    "/verify",
    methods=["POST"]
)
def verify():

    data = request.get_json(
        silent=True
    ) or {}

    image = data.get(
        "image"
    )

    voter_pk = session.get(
        "voter_auth_id"
    )

    if not voter_pk or not image:

        return jsonify(
            ok=False,
            message="Please sign in and provide a camera image."
        ), 400

    voter = db.session.get(
        Voter,
        voter_pk
    )

    if not voter:

        return jsonify(
            ok=False,
            message="Voter account not found."
        ), 404

    if voter.has_voted:

        return jsonify(
            ok=False,
            message="This voter has already cast a vote."
        ), 409

    try:

        live = extract_encoding(
            decode_image(image)
        )

        matched, distance = compare_face(
            voter.face_encoding,
            live
        )

    except ValueError as exc:

        return jsonify(
            ok=False,
            message=str(exc)
        ), 400

    if not matched:

        log_event(
            "FACE_VERIFICATION_FAILED",
            voter.voter_id,
            f"distance={distance:.4f}"
        )

        return jsonify(
            ok=False,
            message="Face verification failed. Please try again with good lighting."
        ), 401

    session["verified_voter_id"] = voter.id

    session["verified_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    log_event(
        "FACE_VERIFICATION_SUCCESS",
        voter.voter_id,
        f"distance={distance:.4f}"
    )

    return jsonify(
        ok=True,
        redirect=url_for("ballot")
    )


# ============================================================
# BALLOT
# ============================================================

@app.route("/ballot")
def ballot():

    voter_pk = session.get(
        "verified_voter_id"
    )

    if not voter_pk:

        return redirect(
            url_for("index")
        )

    voter = db.session.get(
        Voter,
        voter_pk
    )

    if not voter or voter.has_voted:

        session.pop(
            "verified_voter_id",
            None
        )

        return redirect(
            url_for("index")
        )

    candidates = (
        Candidate.query
        .filter_by(active=True)
        .order_by(Candidate.id)
        .all()
    )

    return render_template(
        "ballot.html",
        voter=voter,
        candidates=candidates
    )


# ============================================================
# CAST VOTE
# ============================================================

@app.route(
    "/vote",
    methods=["POST"]
)
def cast_vote():

    voter_pk = session.get(
        "verified_voter_id"
    )

    if not voter_pk:

        return jsonify(
            ok=False,
            message="Face verification is required."
        ), 401

    candidate_id = request.form.get(
        "candidate_id",
        type=int
    )

    voter = db.session.get(
        Voter,
        voter_pk
    )

    candidate = db.session.get(
        Candidate,
        candidate_id
    )

    if not voter:

        return jsonify(
            ok=False,
            message="Voter account not found."
        ), 404

    if not candidate or not candidate.active:

        return jsonify(
            ok=False,
            message="Invalid candidate selection."
        ), 400

    # Duplicate vote protection
    existing_vote = Vote.query.filter_by(
        voter_id=voter.id
    ).first()

    if voter.has_voted or existing_vote:

        return jsonify(
            ok=False,
            message="A vote has already been recorded for this voter."
        ), 409

    try:

        vote = Vote(
            voter_id=voter.id,
            candidate_id=candidate.id
        )

        voter.has_voted = True

        db.session.add(
            vote
        )

        db.session.add(
            AuditLog(
                action="VOTE_CAST",
                actor=voter.voter_id,
                details=f"candidate_id={candidate.id}"
            )
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify(
            ok=False,
            message="Vote could not be recorded safely."
        ), 500

    session.pop(
        "verified_voter_id",
        None
    )

    return jsonify(
        ok=True,
        message="Your vote has been recorded successfully."
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        admin = Admin.query.filter_by(
            username=username
        ).first()

        if (
            admin
            and check_password_hash(
                admin.password_hash,
                password
            )
        ):

            session["admin_id"] = admin.id

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid administrator credentials.",
            "error"
        )

    return render_template(
        "admin/login.html"
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_id",
        None
    )

    return redirect(
        url_for("admin_login")
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    voters = (
        Voter.query
        .order_by(
            Voter.created_at.desc()
        )
        .all()
    )

    candidates = (
        Candidate.query
        .order_by(
            Candidate.id
        )
        .all()
    )

    vote_count = Vote.query.count()

    registered_count = len(
        voters
    )

    voted_count = sum(
        1
        for voter in voters
        if voter.has_voted
    )

    pending_count = (
        registered_count
        - voted_count
    )

    candidate_rows = []

    for candidate in candidates:

        count = Vote.query.filter_by(
            candidate_id=candidate.id
        ).count()

        candidate_rows.append(
            {
                "candidate": candidate,
                "votes": count
            }
        )

    recent_logs = (
        AuditLog.query
        .order_by(
            AuditLog.created_at.desc()
        )
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        voters=voters,
        candidates=candidates,
        vote_count=vote_count,
        registered_count=registered_count,
        voted_count=voted_count,
        pending_count=pending_count,
        candidate_rows=candidate_rows,
        recent_logs=recent_logs
    )


# ============================================================
# ADMIN - REGISTER VOTER
# ============================================================

@app.route(
    "/admin/voters",
    methods=["POST"]
)
@admin_required
def register_voter():

    voter_id = request.form.get(
        "voter_id",
        ""
    ).strip()

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip() or None

    image = request.form.get(
        "image"
    )

    if (
        not voter_id
        or not full_name
        or not image
    ):

        flash(
            "Voter ID, name and registration photo are required.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    if Voter.query.filter_by(
        voter_id=voter_id
    ).first():

        flash(
            "Voter ID already exists.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    try:

        encoding = extract_encoding(
            decode_image(image)
        )

    except ValueError as exc:

        flash(
            str(exc),
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    voter = Voter(
        voter_id=voter_id,
        full_name=full_name,
        email=email,
        face_encoding=json.dumps(
            encoding.tolist()
        )
    )

    db.session.add(
        voter
    )

    db.session.commit()

    log_event(
        "VOTER_REGISTERED",
        session.get("admin_id"),
        f"voter_id={voter_id}"
    )

    flash(
        "Voter registered successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN - ADD CANDIDATE
# ============================================================

@app.route(
    "/admin/candidates",
    methods=["POST"]
)
@admin_required
def add_candidate():

    name = request.form.get(
        "name",
        ""
    ).strip()

    party = request.form.get(
        "party",
        ""
    ).strip() or None

    symbol = request.form.get(
        "symbol",
        ""
    ).strip() or None

    if not name:

        flash(
            "Candidate name is required.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    db.session.add(
        Candidate(
            name=name,
            party=party,
            symbol=symbol
        )
    )

    db.session.commit()

    log_event(
        "CANDIDATE_CREATED",
        str(session.get("admin_id")),
        name
    )

    flash(
        "Candidate added successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# RESULTS
# ============================================================

@app.route("/results")
@admin_required
def results():

    candidates = (
        Candidate.query
        .order_by(
            Candidate.id
        )
        .all()
    )

    rows = []

    total = Vote.query.count()

    for candidate in candidates:

        count = Vote.query.filter_by(
            candidate_id=candidate.id
        ).count()

        percentage = (
            round(
                count / total * 100,
                2
            )
            if total
            else 0
        )

        rows.append(
            {
                "name": candidate.name,
                "party": candidate.party,
                "symbol": candidate.symbol,
                "votes": count,
                "percentage": percentage
            }
        )

    return render_template(
        "admin/results.html",
        rows=rows,
        total=total
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    os.makedirs(
        os.path.join(
            BASE_DIR,
            "data"
        ),
        exist_ok=True
    )

    db.create_all()

    # --------------------------------------------------------
    # Existing database migration
    # --------------------------------------------------------

    try:

        from sqlalchemy import inspect, text

        columns = {
            column["name"]
            for column in inspect(
                db.engine
            ).get_columns("voter")
        }

        if "password_hash" not in columns:

            with db.engine.begin() as conn:

                conn.execute(
                    text(
                        "ALTER TABLE voter "
                        "ADD COLUMN password_hash VARCHAR(255)"
                    )
                )

    except Exception as exc:

        print(
            "Database migration notice:",
            exc
        )

    # --------------------------------------------------------
    # Create default admin
    # --------------------------------------------------------

    if not Admin.query.first():

        username = os.getenv(
            "ADMIN_USERNAME",
            "admin"
        )

        password = os.getenv(
            "ADMIN_PASSWORD",
            "admin123"
        )

        db.session.add(
            Admin(
                username=username,
                password_hash=generate_password_hash(
                    password
                )
            )
        )

        db.session.commit()

        print(
            "Default admin created."
        )

    # --------------------------------------------------------
    # DEMO CANDIDATES
    # --------------------------------------------------------
    #
    # These are completely fictional and are only for
    # educational/demo purposes.
    # --------------------------------------------------------

    if Candidate.query.count() == 0:

        demo_candidates = [

            (
                "Aarav Mehta",
                "Civic Progress Party (Demo)",
                "CP"
            ),

            (
                "Diya Sharma",
                "People First Party (Demo)",
                "PF"
            ),

            (
                "Kabir Singh",
                "Digital Future Party (Demo)",
                "DF"
            ),

            (
                "Anaya Verma",
                "Green Community Party (Demo)",
                "GC"
            ),

        ]

        for (
            name,
            party,
            symbol
        ) in demo_candidates:

            db.session.add(
                Candidate(
                    name=name,
                    party=party,
                    symbol=symbol
                )
            )

        db.session.commit()

        log_event(
            "DEMO_ELECTION_SEEDED",
            "system",
            "Fictional demo candidates and parties created."
        )

        print(
            "Demo candidates created successfully."
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

with app.app_context():

    init_db()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "0"
            ) == "1"
        )
    )