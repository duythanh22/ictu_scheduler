# notes/route.py

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from notes.database import *

notes_bp = Blueprint('notes', __name__)


@notes_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login_api.login'))

    if request.method == 'GET':
        try:
            # print(session["user_id"])
            username, note_titles, note_content = get_user_notes(session["user_id"])

            return render_template("notes/notes.html", note_content=note_content, note_titles=note_titles,
                                   username=username)
        except Exception as e:
            # app.logger.error(f"Error in GET /notes: {e}")
            return jsonify({"error": "Internal Server Error"}), 500

    else:
        try:
            note_type = request.form.get('type')
            if note_type == "save":
                note_title = request.form.get("note_title")
                note_content_updated = request.form.get("note_content_updated")

                save_note_content(note_title, note_content_updated, session["user_id"])
                return jsonify({"message": "Save successful"})

            elif note_type == "switch":
                cur_note_title = request.form.get("cur_note_title")
                cur_note_content_updated = request.form.get("cur_note_content_updated")
                next_note_title = request.form.get("next_note_title")
                next_note_content = switch_note_content(cur_note_title, cur_note_content_updated, next_note_title,
                                                        session["user_id"])
                return jsonify({"next_note_content": next_note_content, "next_note_title": next_note_title})

            elif note_type == "new_note":
                cur_note_title = request.form.get("cur_note_title")
                cur_note_content_updated = request.form.get("cur_note_content_updated")
                next_note_title = request.form.get("next_note_title")
                create_new_note(cur_note_title, cur_note_content_updated, next_note_title, session["user_id"])
                return jsonify({"message": "Successfully created new note", "next_note_title": next_note_title})

            elif note_type == "edit_title":
                cur_note_title = request.form.get("cur_note_title")
                next_note_title = request.form.get("next_note_title")
                message, status = edit_note_title(cur_note_title, next_note_title, session["user_id"])
                if status == 200:
                    return jsonify({"message": message, "next_note_title": next_note_title})
                else:
                    return jsonify({"error": message}), status

            elif note_type == "setup_buttons":
                note_titles = setup_buttons(session["user_id"])
                return jsonify({"message": "Loaded buttons", "note_titles": note_titles})

            elif note_type == "delete_note":
                note_to_delete = request.form.get("cur_note_title")
                delete_note_content(note_to_delete, session["user_id"])
                return jsonify({"message": "Deleted: " + note_to_delete})

            else:
                return jsonify({"error": "Invalid type"}), 400

        except KeyError as e:
            # app.logger.error(f"KeyError in POST /notes: {e}")
            return jsonify({"error": "Missing required field"}), 400

        except Exception as e:
            # app.logger.error(f"Error in POST /notes: {e}")
            return jsonify({"error": "Internal Server Error"}), 500
