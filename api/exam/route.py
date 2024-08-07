import requests
from bs4 import BeautifulSoup
from http.cookies import SimpleCookie
from flask import Blueprint, request, jsonify, session
from api.login import CustomSession

lichthi = Blueprint('lichthi', __name__)
client = CustomSession()

# Function to handle errors
def handle_error(message, status):
    return jsonify({'error': True, 'message': message}), status

@lichthi.route('/exam', methods=['GET'])
def get_exam_schedule():
    try:
        # Check if user is logged in by verifying the session
        if 'name' not in session or 'token' not in session:
            return handle_error('User not logged in', 401)

        # Get the token from session if available
        token = session.get('token')
        if not token:
            return handle_error('No valid token found in session', 401)

        # Prepare cookies
        cookies = {
            'SignIn': token
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = client.get('http://220.231.119.171/kcntt/StudentViewExamList.aspx', headers=headers, cookies=cookies)
        response.raise_for_status()
        # print(response)
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', {'id': 'tblCourseList'})

        if not table:
            return handle_error("Table 'tblCourseList' not found", 404)

        data = []
        rows = table.find_all('tr')[1:]  # Skip the header row

        for row in rows:
            cells = row.find_all('td')
            rowData = [cell.get_text(strip=True) for cell in cells]

            if rowData and rowData[0]:  # Ensure stt is not empty
                stt, maHP, tenHP, soTC, ngayThi, caThi, hinhThucThi, soBaoDanh, phongThi, ghiChu = rowData
                data.append({
                    'stt': stt,
                    'maHP': maHP,
                    'tenHP': tenHP,
                    'soTC': soTC,
                    'ngayThi': ngayThi,
                    'caThi': caThi,
                    'hinhThucThi': hinhThucThi,
                    'soBaoDanh': soBaoDanh,
                    'phongThi': phongThi,
                    'ghiChu': ghiChu,
                })
        # with open('check_exam.txt', 'w', encoding='utf-8') as f:
        #     f.write(str(data))
        return jsonify({'error': False, 'lichthiData': data})

    except requests.RequestException as e:
        return handle_error('Error fetching exam schedule data after login', 500)
