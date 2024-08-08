from flask import Blueprint, jsonify
from api.login import client
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import requests

schedule_api = Blueprint('schedule_api', __name__)

url_study_register = "http://220.231.119.171/kcntt/StudyRegister/StudyRegister.aspx"
def parse_date_range(date_range):
    start, end = date_range.split(" -> ")
    start_day, start_month, start_year = start.split("/")
    end_day, end_month, end_year = end.split("/")
    start_date = f"{start_year}-{start_month.zfill(2)}-{start_day.zfill(2)}"
    end_date = f"{end_year}-{end_month.zfill(2)}-{end_day.zfill(2)}"
    return start_date, end_date

def is_today_in_range(date_range):
    try:
        start_date, end_date = parse_date_range(date_range)
        today = datetime.today().date()
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        return start <= today <= end
    except Exception as e:
        print(f"Error parsing date range: {e}")
        return False

def fetch_registration_schedule(client):
    try:
        response = client.get(url_study_register)
        response.raise_for_status()  # Raise an error for bad responses

        # Save the raw HTML response to a local file
        # with open('study_register_page.txt', 'w', encoding='utf-8') as file:
        #     file.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')

        course_select = soup.select_one('#drpCourse')
        if not course_select:
            return {'error': True, 'message': 'Course select element not found'}
        options = course_select.find_all('option')
        courses = [{'value': option['value'], 'text': option.text} for option in options if option.get('value')]
        if not courses:
            return {'error': True, 'message': 'No courses found'}

        registered_courses = []
        course_class_elements = soup.select('span[id^=gridRegistered_lblCourseClass_]')
        for element in course_class_elements:
            course_id = element['id'].split('_')[-1]
            course_class = element.text.strip()
            course_code = soup.select_one(f'#gridRegistered_lblCourseCode_{course_id}').text.strip()
            long_time = soup.select_one(f'#gridRegistered_lblLongTime_{course_id}').text.strip()
            location = soup.select_one(f'#gridRegistered_lblLocation_{course_id}').text.strip()
            instructor = soup.select_one(f'#gridRegistered_lblInstructor_{course_id}').text.strip()
            expectation_student = soup.select_one(f'#gridRegistered_lblExpectationStudent_{course_id}').text.strip()
            current_student = soup.select_one(f'#gridRegistered_lblCurrentStudent_{course_id}').text.strip()
            course_credit = soup.select_one(f'#gridRegistered_lblCourseCredit_{course_id}').text.strip()
            tuition = soup.select_one(f'#gridRegistered_lblTuition_{course_id}').text.strip()
            registered_courses.append({
                'course_class': course_class,
                'course_code': course_code,
                'long_time': long_time,
                'location': location,
                'instructor': instructor,
                'expectation_student': expectation_student,
                'current_student': current_student,
                'course_credit': course_credit,
                'tuition': tuition
            })
        # print(registered_courses)
        # with open('schedule_data.txt', 'w', encoding='utf-8') as f:
        #     f.write(str(registered_courses))
        return {'error': False, 'courses': courses, 'registered_courses': registered_courses}
    except requests.RequestException as e:
        print(f"Error fetching registration schedule: {e}")
        return {'error': True, 'message': str(e)}

def parse_date_range_v2(date_range):
    start, end = map(lambda x: datetime.strptime(x.strip(), "%d/%m/%Y"), date_range.split("đến"))
    return start, end

def parse_schedule(schedule):
    day_map = {
        "Thứ 2": "Monday",
        "Thứ 3": "Tuesday",
        "Thứ 4": "Wednesday",
        "Thứ 5": "Thursday",
        "Thứ 6": "Friday",
        "Thứ 7": "Saturday",
        "Chủ nhật": "Sunday"
    }
    pattern = r"(Thứ \d|Chủ nhật) tiết ([\d,]+)"
    matches = re.findall(pattern, schedule)
    return [(day_map[day], [int(t) for t in periods.split(',')]) for day, periods in matches]

def extract_course_info(data):
    extracted_info = []
    for course in data['registered_courses']:
        course_name = course['course_class']
        course_code = course['course_code']
        long_time = course['long_time']

        # Regex to find time blocks
        time_blocks = re.findall(r"Từ (\d{2}/\d{2}/\d{4}) đến (\d{2}/\d{2}/\d{4}):(?: \((\d+)\))?(.*?)(?=Từ|\Z)",
                                 long_time, re.DOTALL)

        # Parse instructor information
        instructor = course['instructor']
        instructor_match = re.search(r"(.+) \( Mã Meet: (.+?) link: (.+?) \)", instructor)
        if instructor_match:
            instructor_name = instructor_match.group(1)
            meet_code = instructor_match.group(2)
            meet_link = instructor_match.group(3)
        else:
            instructor_name = instructor.strip()
            meet_code = "N/A"
            meet_link = "N/A"

        # Parse location information
        location_full = course['location']
        location_blocks = re.findall(r"\((\d+(?:,\d+)*)\) ([^(]+)", location_full)
        if location_blocks:
            location_map = {}
            for block, loc in location_blocks:
                for num in map(int, block.split(',')):
                    location_map[num] = loc.strip()
        else:
            location_map = {1: location_full.strip()}

        # Extract course credit
        course_credit = course['course_credit']

        # Parse course schedule
        course_schedule = []
        for start_date, end_date, block_num, schedule in time_blocks:
            start, end = parse_date_range_v2(f"{start_date} đến {end_date}")
            parsed_schedule = parse_schedule(schedule)
            block_num = int(block_num) if block_num else 1
            current_date = start
            while current_date <= end:
                for day, periods in parsed_schedule:
                    if current_date.strftime("%A") == day:
                        location = location_map.get(block_num, location_map[1])
                        course_schedule.append((current_date, periods, location))
                current_date += timedelta(days=1)

        # Append extracted info
        extracted_info.append(
            (course_name, course_code, course_schedule, instructor_name, course_credit, meet_code, meet_link))

    return extracted_info

def organize_by_week(extracted_info):
    organized_data = {}
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for course_name, course_code, schedule, instructor, course_credit, meet_code, meet_link in extracted_info:
        for date, periods, location in schedule:
            week_number = date.isocalendar()[1]
            if week_number not in organized_data:
                organized_data[week_number] = {
                    'courses': [],
                    'start_date': date,
                    'end_date': date
                }
            organized_data[week_number]['courses'].append(
                (date, course_name, course_code, periods, instructor, location, course_credit, meet_code, meet_link)
            )
            organized_data[week_number]['start_date'] = min(organized_data[week_number]['start_date'], date)
            organized_data[week_number]['end_date'] = max(organized_data[week_number]['end_date'], date)

    # Sort courses by date and then by the order of days in a week
    for week in organized_data.values():
        week['courses'].sort(key=lambda x: (x[0], day_order.index(x[0].strftime("%A"))))

    return organized_data


@schedule_api.route('/schedule', methods=['GET'])
def get_schedule():
    schedule_data = fetch_registration_schedule(client)
    # with open('schedule_data.txt', 'w', encoding='utf-8') as f:
    #     f.write(str(schedule_data))
    if schedule_data['error']:
        return jsonify(schedule_data)

    extracted_info = extract_course_info(schedule_data)
    organized_schedule = organize_by_week(extracted_info)
    extracted_info = extract_course_info(schedule_data)
    with open('check2.txt', 'w', encoding='utf-8') as f:
        f.write(str(extracted_info))
    organized_schedule = organize_by_week(extracted_info)
    with open('check1.txt', 'w', encoding='utf-8') as f:
        f.write(str(organized_schedule))

    return jsonify({'error': False, 'schedule': organized_schedule})
