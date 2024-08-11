# note/database.py
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('notedb.sqlite')
    conn.row_factory = sqlite3.Row  # This allows fetching rows as dictionaries
    return conn

def add_user(student_id, name):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Kiểm tra xem student_id đã tồn tại chưa
        c.execute("SELECT 1 FROM users WHERE student_id = ?", (student_id,))
        if c.fetchone():
            # Nếu tồn tại, thông báo lỗi
            print("User already exists.")
            return

        # Nếu không tồn tại, thêm người dùng mới
        c.execute("INSERT INTO users (student_id, name) VALUES (?, ?)", (student_id, name))
        conn.commit()

def add_sample_note(student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            print("User not found. Cannot add sample note.")
            return
        user_id = user['id']
        note_title = "Sample Note"
        note_content = "Sample Text"
        c.execute("INSERT INTO notes (user_id, note_title, note_content) VALUES (?, ?, ?)",
                  (user_id, note_title, note_content))
        conn.commit()

# Hàm lấy thông tin ghi chú của người dùng
def get_user_notes(student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT id, name FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            print("User not found.")
            return None, [], []
        user_id, username = user['id'], user['name']
        notes = c.execute("SELECT note_title, note_content FROM notes WHERE user_id = ?", (user_id,)).fetchall()
        note_titles = [note['note_title'] for note in notes]
        note_contents = [note['note_content'] for note in notes]
        # print(user_id, note_titles, note_contents)
        return username, note_titles, note_contents

# Hàm lưu nội dung ghi chú
def save_note_content(note_title, note_content_updated, student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        # Xác định user_id
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            print("User not found. Cannot save note content.")
            return
        user_id = user['id']

        # Cập nhật nội dung ghi chú
        c.execute("UPDATE notes SET note_content = ? WHERE note_title = ? AND user_id = ?",
                  (note_content_updated, note_title, user_id))
        conn.commit()

# Hàm chuyển đổi ghi chú
def switch_note_content(cur_note_title, cur_note_content_updated, next_note_title, student_id):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Lấy user_id từ student_id
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            return "User ID not found", 404

        user_id = user['id']

        # Cập nhật nội dung ghi chú hiện tại
        c.execute("UPDATE notes SET note_content = ? WHERE note_title = ? AND user_id = ?",
                  (cur_note_content_updated, cur_note_title, user_id))

        # Lấy nội dung ghi chú tiếp theo
        next_note_content_row = c.execute("SELECT note_content FROM notes WHERE user_id = ? AND note_title = ?",
                                          (user_id, next_note_title)).fetchone()

        if next_note_content_row is None:
            return "No note found with the specified title.", 404

        next_note_content = next_note_content_row['note_content']

        conn.commit()

        return next_note_content

# Hàm tạo ghi chú mới
def create_new_note(cur_note_title, cur_note_content_updated, next_note_title, student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            print("User not found. Cannot create new note.")
            return
        user_id = user['id']

        if cur_note_title:
            c.execute("UPDATE notes SET note_content = ? WHERE note_title = ? AND user_id = ?",
                      (cur_note_content_updated, cur_note_title, user_id))
        c.execute("INSERT INTO notes (user_id, note_title, note_content) VALUES (?, ?, ?)",
                  (user_id, next_note_title, ""))
        conn.commit()

# Hàm chỉnh sửa tiêu đề ghi chú
def edit_note_title(cur_note_title, next_note_title, student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            return "User not found.", 404
        user_id = user['id']

        note_titles = [note['note_title'].upper() for note in c.execute(
            "SELECT note_title FROM notes WHERE user_id = ?", (user_id,)).fetchall()]
        if next_note_title.upper() in note_titles:
            return "Error: Title already exists", 400
        if next_note_title.replace(" ", "").replace("-", "").isalnum():
            c.execute("UPDATE notes SET note_title = ? WHERE note_title = ? AND user_id = ?",
                      (next_note_title, cur_note_title, user_id))
            conn.commit()
            return "Successfully edited note title", 200
        else:
            return "Error: Title must be alphanumeric", 400

# Hàm tải danh sách ghi chú
def setup_buttons(student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        note_titles = [note['note_title'] for note in c.execute(
            "SELECT note_title FROM notes WHERE user_id = (SELECT id FROM users WHERE student_id = ?)",
            (student_id,)).fetchall()]
        return note_titles

# Hàm xóa ghi chú
def delete_note_content(note_title, student_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        user = c.execute("SELECT id FROM users WHERE student_id = ?", (student_id,)).fetchone()
        if user is None:
            print("User not found. Cannot delete note.")
            return
        user_id = user['id']

        c.execute("DELETE FROM notes WHERE user_id = ? AND note_title = ?", (user_id, note_title))
        conn.commit()
