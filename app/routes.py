import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db, bcrypt
from app.models import User, MeetingSummary
from app.summarizer import process_meeting

main = Blueprint('main', __name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def allowed_audio(filename):
    allowed = current_app.config['ALLOWED_AUDIO_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


# ── Auth routes ────────────────────────────────────────────────────────────────

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('register.html')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.login'))


# ── Main routes ────────────────────────────────────────────────────────────────

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        input_type = request.form.get('input_type', 'transcript')
        title = request.form.get('title', 'Untitled Meeting').strip() or 'Untitled Meeting'

        # Create summary record
        meeting = MeetingSummary(
            user_id=current_user.id,
            title=title,
            input_type=input_type,
            status='processing'
        )
        db.session.add(meeting)
        db.session.commit()

        try:
            audio_path = None
            transcript_text = None

            if input_type == 'audio':
                audio_file = request.files.get('audio_file')
                if not audio_file or audio_file.filename == '':
                    raise ValueError("No audio file uploaded.")
                if not allowed_audio(audio_file.filename):
                    raise ValueError("File type not allowed. Use mp3, wav, ogg, m4a, or flac.")

                filename = secure_filename(f"{meeting.id}_{audio_file.filename}")
                audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(audio_path)
                meeting.original_filename = audio_file.filename

            elif input_type == 'transcript':
                transcript_text = request.form.get('transcript_text', '').strip()
                if not transcript_text:
                    raise ValueError("Transcript text cannot be empty.")

            # Run pipeline
            result = process_meeting(
                input_type=input_type,
                audio_path=audio_path,
                transcript_text=transcript_text
            )

            # Save results
            meeting.transcript = result['transcript']
            meeting.summary = result['summary']
            meeting.action_items = json.dumps(result['action_items'])
            meeting.key_decisions = json.dumps(result['key_decisions'])
            meeting.status = 'done'
            db.session.commit()

            return redirect(url_for('main.result', meeting_id=meeting.id))

        except Exception as e:
            meeting.status = 'error'
            meeting.error_message = str(e)
            db.session.commit()
            flash(f'Processing failed: {str(e)}', 'error')
            return redirect(url_for('main.index'))

    return render_template('index.html')


@main.route('/result/<int:meeting_id>')
@login_required
def result(meeting_id):
    meeting = MeetingSummary.query.filter_by(id=meeting_id, user_id=current_user.id).first_or_404()

    action_items = []
    key_decisions = []

    if meeting.action_items:
        try:
            action_items = json.loads(meeting.action_items)
        except Exception:
            pass

    if meeting.key_decisions:
        try:
            key_decisions = json.loads(meeting.key_decisions)
        except Exception:
            pass

    return render_template('result.html',
                           meeting=meeting,
                           action_items=action_items,
                           key_decisions=key_decisions)


@main.route('/history')
@login_required
def history():
    meetings = MeetingSummary.query.filter_by(user_id=current_user.id)\
        .order_by(MeetingSummary.created_at.desc()).all()
    return render_template('history.html', meetings=meetings)


@main.route('/delete/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    meeting = MeetingSummary.query.filter_by(id=meeting_id, user_id=current_user.id).first_or_404()
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted.', 'success')
    return redirect(url_for('main.history'))
