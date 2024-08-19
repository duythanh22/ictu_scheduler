# api/score/route.py

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, session
from api.login import CustomSession

import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from collections import Counter

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
        with open('check_score.txt', 'w', encoding='utf-8') as f:
            f.write(str(data_score_sum))
        # Create charts
        charts = create_charts(data_score_detail, data_score_sum)

        return jsonify({
            'error': False,
            'diemSoData': data_score_detail,
            'tongKetData': data_score_sum,
            'charts': charts
        })
    except requests.RequestException as e:
        return handle_error(f'Failed to fetch scores: {str(e)}', 500)


def create_charts(data_score_detail, data_score_sum):
    # Create a figure with three vertically stacked subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 20))
    plt.subplots_adjust(hspace=0.5)

    # Pie chart for letter grade distribution
    diemchu_counts = Counter(item['diemChu'] for item in data_score_detail)
    labels = [f'{label} ({count})' for label, count in diemchu_counts.items()]
    sizes = list(diemchu_counts.values())

    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax1.set_title('Phân bố điểm theo điểm chữ', fontsize=16, pad=20, fontweight='bold')

    # Prepare data for GPA charts
    semesters = []
    semester_gpas = []
    yearly_gpas = []
    cumulative_gpas = []

    for item in data_score_sum:
        if item['hocKy'] in ['1', '2']:
            if item['TBC4']:  # Kiểm tra nếu 'TBC4' không bị trống
                semesters.append(f"{item['namHoc']} - HK{item['hocKy']}")
                semester_gpas.append(float(item['TBC4']))
        elif item['hocKy'] == 'Cả Năm':
            if item['TBC4']:  # Kiểm tra nếu 'TBC4' không bị trống
                yearly_gpas.append(float(item['TBC4']))
        elif item['namHoc'] == 'Toàn khóa':
            if item['TBC4']:  # Kiểm tra nếu 'TBC4' không bị trống
                overall_gpa = float(item['TBC4'])

    # Calculate cumulative GPA
    cumulative_gpas = np.cumsum(semester_gpas) / np.arange(1, len(semester_gpas) + 1)

    # Plot semester and yearly GPA trends
    ax2.plot(semesters, semester_gpas, marker='o', linestyle='-', color='#1f77b4', linewidth=2, label='GPA Học Kỳ')
    ax2.plot(semesters[1::2], yearly_gpas, marker='s', linestyle='--', color='#ff7f0e', linewidth=2, label='GPA Cả Năm')
    ax2.set_xlabel('Học Kỳ', fontsize=14, fontweight='bold')
    ax2.set_ylabel('GPA (Thang 4.0)', fontsize=14, fontweight='bold')
    ax2.set_title('Xu hướng GPA học kỳ và cả năm', fontsize=16, pad=20, fontweight='bold')
    ax2.set_xticks(range(len(semesters)))
    ax2.set_xticklabels(semesters, rotation=45, ha='right')
    ax2.legend(loc='upper left', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Plot cumulative GPA trend
    ax3.plot(semesters, cumulative_gpas, marker='o', linestyle='-', color='#2ca02c', linewidth=2, label='GPA Tích Lũy')
    ax3.axhline(y=overall_gpa, color='red', linestyle='--', linewidth=2, label='GPA Toàn Khóa')
    ax3.set_xlabel('Học Kỳ', fontsize=14, fontweight='bold')
    ax3.set_ylabel('GPA (Thang 4.0)', fontsize=14, fontweight='bold')
    ax3.set_title('Xu hướng GPA tích lũy', fontsize=16, pad=20, fontweight='bold')
    ax3.set_xticks(range(len(semesters)))
    ax3.set_xticklabels(semesters, rotation=45, ha='right')
    ax3.legend(loc='upper left', fontsize=12)
    ax3.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()

    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)

    # Convert PNG image to base64 string
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png).decode('utf-8')

    buffer.close()
    plt.close()

    return graph
