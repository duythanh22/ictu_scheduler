# app.py

from flask import Flask, render_template, session, redirect, url_for
from api.login import login_api
from api.schedule.route import schedule_api
from api.score.route import scores
from api.exam.route import lichthi
from notes.route import notes_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set secret key for session

# Register blueprints
app.register_blueprint(login_api, url_prefix='/api')
app.register_blueprint(schedule_api, url_prefix='/api')
app.register_blueprint(scores, url_prefix='/api')
app.register_blueprint(lichthi, url_prefix='/api')
app.register_blueprint(notes_bp, url_prefix='')

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/schedule')
def schedule():
    username = session.get('name')
    return render_template('schedule.html', username=username)

@app.route('/scores')
def scores_view():
    username = session.get('name')
    return render_template('score.html', username=username)

@app.route('/exam')
def exam():
    username = session.get('name')
    return render_template('exam.html', username=username)  # Adjust the template rendering if needed

@app.route('/notes')
def notes_view():
    if 'user_id' in session:
        username = session.get('name')
        return render_template('notes/notes.html', username=username)
    else:
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)