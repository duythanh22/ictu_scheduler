# api/score/route.py

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, session
from api.login import CustomSession

scores = Blueprint('scores', __name__)

client = CustomSession()

# Function to handle errors
def handle_error(message, status):
    return jsonify({'error': True, 'message': message}), status

@scores.route('/scores', methods=['GET'])
def get_scores():
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

        response = client.get('http://220.231.119.171/kcntt/StudentMark.aspx', headers=headers, cookies=cookies)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        data_score_detail = []
        data_score_sum = []

        table_score_detail = soup.find('table', {'id': 'tblMarkDetail'}) or soup.find('table', {'id': 'tblStudentMark'})
        table_score_sum = soup.find('table', {'id': 'tblSumMark'})

        if not table_score_detail or not table_score_sum:
            return handle_error('Table not found', 404)

        rows_detail = table_score_detail.find_all('tr')[2:]  # Skip the first two header rows
        rows_sum = table_score_sum.find_all('tr')[2:]  # Skip the first two header rows
        # print(registered_courses)
        # with open('check.txt', 'w', encoding='utf-8') as f:
        #     f.write(str(rows_sum))
        for row in rows_detail:
            cells = row.find_all('td')
            if len(cells) < 14:
                continue

            data_score_detail.append({
                'stt': cells[0].get_text(strip=True),
                'maHP': cells[1].get_text(strip=True),
                'tenHP': cells[2].get_text(strip=True),
                'soTC': cells[3].get_text(strip=True),
                'danhGia': cells[8].get_text(strip=True),
                'chuyenCan': cells[10].get_text(strip=True),
                'thi': cells[11].get_text(strip=True),
                'tongKet': cells[12].get_text(strip=True),
                'diemChu': cells[13].get_text(strip=True),
            })

        for row in rows_sum:
            cells = row.find_all('td')
            if len(cells) < 14:
                continue

            data_score_sum.append({
                'namHoc': cells[0].get_text(strip=True),
                'hocKy': cells[1].get_text(strip=True),
                'TBTL10': cells[2].get_text(strip=True),
                'TBTL4': cells[4].get_text(strip=True),
                'TC': cells[6].get_text(strip=True),
                'TBC10': cells[8].get_text(strip=True),
                'TBC4': cells[10].get_text(strip=True)
            })

        return jsonify({
            'error': False,
            'diemSoData': data_score_detail,
            'tongKetData': data_score_sum
        })
    except requests.RequestException as e:
        return handle_error(f'Failed to fetch scores: {str(e)}', 500)
