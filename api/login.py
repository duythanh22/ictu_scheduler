# api/login

import requests
from bs4 import BeautifulSoup
import hashlib
from flask import Blueprint, request, jsonify, session
from notes.database import add_user  # Import các hàm từ module note

login_api = Blueprint('login_api', __name__)

# URL constants
url_login = "http://220.231.119.171/kcntt/login.aspx"


class CustomSession(requests.Session):
    def __init__(self, *args, **kwargs):
        super(CustomSession, self).__init__(*kwargs)
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })


client = CustomSession()


def get_all_form_elements(soup):
    return [tag for tag in soup.find_all(['select', 'textarea', 'input']) if tag.get('name')]


@login_api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    session_response = client.get(url_login)
    soup = BeautifulSoup(session_response.text, 'html.parser')
    body = {}
    for element in get_all_form_elements(soup.find(id="Form1")):
        key = element.get('name')
        value = element.get('value')
        if key == "txtUserName":
            value = username
        elif key == "txtPassword":
            value = hashlib.md5(password.encode()).hexdigest()
        if value:
            body[key] = value
    post_response = client.post(session_response.url, data=body)
    error_soup = BeautifulSoup(post_response.text, 'html.parser')
    error_info = error_soup.find(id="lblErrorInfo")
    if error_info and error_info.text:
        return jsonify({
            'error': True,
            'message': error_info.text
        })

    def get_cookie_sign_in_json():
        for cookie in client.cookies:
            if cookie.name == "SignIn":
                return {
                    'key': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'httpOnly': cookie.has_nonstandard_attr('HttpOnly'),
                    'hostOnly': cookie.domain_initial_dot,
                    'creation': cookie.expires,
                    'lastAccessed': cookie.expires,
                    'sameSite': 'Lax'  # Assuming 'Lax' as default
                }
        return None

    home_response = client.get("http://220.231.119.171/kcntt/Home.aspx")
    soup2 = BeautifulSoup(home_response.text, 'html.parser')
    student_info = soup2.find(id="PageHeader1_lblUserFullName")
    study_register_response = client.get("http://220.231.119.171/kcntt/StudyRegister/StudyRegister.aspx")
    soup3 = BeautifulSoup(study_register_response.text, 'html.parser')
    student_duration = soup3.find(id="lblDuration")
    if student_info and student_info.text:
        start_index = student_info.text.index('(')
        end_index = student_info.text.index(')')
        name = student_info.text[:start_index].strip()
        student_id = student_info.text[start_index + 1:end_index]

        add_user(student_id, name)  # Sử dụng hàm add_user từ module note

        session['user_id'] = student_id  # Save user_id in session
        session['name'] = name  # Save user's name in session
        session['token'] = get_cookie_sign_in_json()['value'] if get_cookie_sign_in_json() else None
        # with open('id.txt', 'w', encoding='utf-8') as f:
        #     f.write(str(student_id))
        return jsonify({
            'error': False,
            'message': "Đăng nhập thành công!",
            'name': name,
            'studentId': student_id,
            'studentDuration': student_duration.text if student_duration else None,
            'token': get_cookie_sign_in_json()['value'] if get_cookie_sign_in_json() else None
        })
    return jsonify({
        'error': True,
        'message': 'Đã có lỗi xảy ra, vui lòng thử lại sau'
    })


@login_api.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    session.pop('name', None)  # Remove name from session
    session.pop('token', None)  # Remove token from session
    return jsonify({'message': 'Logged out successfully!'})
