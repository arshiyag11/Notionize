# import os
# import dotenv
# import requests
# import csv
# import json
# from datetime import datetime, timedelta
# from notion_client import Client
# from firebase_admin import credentials, messaging, initialize_app, get_app
# from src.utils import parse_date, COURSE_COLORS

# class AssignmentTracker:
#     def __init__(self):
#         self.headers = {
#             'Authorization': f'Bearer {os.getenv("API_KEY")}',
#             'Content-Type': 'application/json',
#             'Notion-Version': '2022-06-28'
#         }
#         self.notion = Client(auth=os.getenv("API_KEY"))
#         self.database_id = os.getenv("DATABASE_ID")
#         self.firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
#         if not self.firebase_credentials_path:
#             raise ValueError("FIREBASE_CREDENTIALS_PATH is not set in the environment or is incorrect.")
#         try:
#             self.app = get_app()
#         except ValueError:
#             cred = credentials.Certificate(self.firebase_credentials_path)
#             self.app = initialize_app(cred)
#         self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
#         self.assignments = []

#     def generate_payload(self, assignment, course, due_date, cp, grade=None, weightage=None):
#         valid_statuses = {
#             'Not Started': 'Not started',
#             'In Progress': 'In progress',
#             'Completed': 'Complete',
#         }
#         notion_status = valid_statuses.get(cp, "Not started")
#         payload = {
#             "parent": {"database_id": self.database_id},
#             "properties": {
#                 'Assignment': {'title': [{'text': {'content': str(assignment)}}]},
#                 'Course': {'multi_select': [{'name': str(course)}]},
#                 'Due Date': {'multi_select': [{'name': str(due_date)}]} if due_date else [],
#                 'Complete': {'status': {'name': notion_status}},
#                 'Grade': {'number': float(grade)} if grade is not None else None,
#                 'Weightage': {'number': float(weightage)} if weightage is not None else None,
#             }
#         }
#         return payload

#     def send_discord_notification(self, message):
#         payload = {"content": message}
#         try:
#             response = requests.post(self.discord_webhook_url, json=payload)
#             if response.status_code == 204:
#                 print("Discord notification sent successfully.")
#             else:
#                 print(f"Error sending Discord notification: {response.status_code}")
#         except Exception as e:
#             print(f"Error sending Discord notification: {str(e)}")

#     def read_csv(self, filepath):
#         url = 'https://api.notion.com/v1/pages'
#         responses = []
#         with open(filepath, mode='r', newline='') as file:
#             csv_reader = csv.reader(file)
#             for r in csv_reader:
#                 assignment, course, due_date, cp, grade, weightage = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip() if len(r) > 4 else None, r[5].strip() if len(r) > 5 else None
#                 existing_assignments = self.notion.databases.query(
#                     database_id=self.database_id,
#                     filter={
#                         "and": [
#                             {"property": "Assignment", "title": {"equals": assignment}},
#                             {"property": "Course", "multi_select": {"contains": course}},
#                             {"property": "Due Date", "multi_select": {"contains": due_date}}
#                         ]
#                     }
#                 ).get("results")
#                 if not existing_assignments:
#                     payload = self.generate_payload(assignment, course, due_date, cp, grade, weightage)
#                     try:
#                         response = requests.post(url, headers=self.headers, data=json.dumps(payload))
#                         responses.append(response.status_code)
#                         if response.status_code == 200:
#                             print(f'{assignment} successfully uploaded to Notion')
#                             self.send_discord_notification(
#                                 f"Assignment Uploaded: {assignment} - {course}, Due Date: {due_date}, Grade: {grade}, Weightage: {weightage}"
#                             )
#                         else:
#                             print("Error:", response.status_code, response.text)
#                     except Exception as e:
#                         print(f"Exception occurred while uploading row: {str(e)}")
#                 else:
#                     print(f"Skipping duplicate entry: {assignment} - {course}, Due Date: {due_date}")
#         return responses

#     def get_due_today(self):
#         today = datetime.now().date()
#         return [a for a in self.assignments if self.parse_date(a['due_date'][0]['name']) == today]

#     def get_due_this_week(self):
#         today = datetime.now().date()
#         start_of_week = today - timedelta(days=today.weekday())
#         end_of_week = start_of_week + timedelta(days=6)
#         return [a for a in self.assignments if start_of_week <= self.parse_date(a['due_date'][0]['name']) <= end_of_week]

#     def parse_date(self, due_date_str):
#         try:
#             return datetime.strptime(due_date_str, '%Y-%m-%d').date()
#         except ValueError:
#             return datetime.strptime(due_date_str, '%d-%m-%Y').date()

#     def fetch_assignments_from_notion(self):
#         query = self.notion.databases.query(database_id=self.database_id)
#         self.assignments = []
#         for page in query['results']:
#             assignment = {
#                 'assignment': page['properties']['Assignment']['title'][0]['text']['content'],
#                 'course': page['properties']['Course']['multi_select'],
#                 'due_date': page['properties']['Due Date']['multi_select'],
#                 'complete': page['properties']['Complete']['status']['name'],
#                 'grade': page['properties']['Grade']['number'] if 'Grade' in page['properties'] and page['properties']['Grade']['number'] is not None else None,
#                 'weightage': page['properties']['Weightage']['number'] if 'Weightage' in page['properties'] and page['properties']['Weightage']['number'] is not None else None
#             }
#             self.assignments.append(assignment)



import os
import requests
import csv
import json
from datetime import datetime, timedelta
from notion_client import Client
from notion_client.errors import APIResponseError
from firebase_admin import credentials, messaging, initialize_app, get_app
from utils import parse_date, get_due_today, get_due_this_week, COURSE_COLORS, get_course_embed

class AssignmentTracker:
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {os.getenv("API_KEY")}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        self.notion = Client(auth=os.getenv("API_KEY"))
        self.database_id = os.getenv("DATABASE_ID")
        self.firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if not self.firebase_credentials_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH is not set in the environment or is incorrect.")
        try:
            self.app = get_app()
        except ValueError:
            cred = credentials.Certificate(self.firebase_credentials_path)
            self.app = initialize_app(cred)
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.assignments = []

    def generate_payload(self, assignment, course, due_date, cp, grade=None, weightage=None):
        valid_statuses = {
            'Not Started': 'Not started',
            'In Progress': 'In progress',
            'Completed': 'Complete',
        }
        notion_status = valid_statuses.get(cp, "Not started")
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                'Assignment': {'title': [{'text': {'content': str(assignment)}}]},
                'Course': {'multi_select': [{'name': str(course)}]},
                'Due Date': {'date': {'start': str(due_date)}} if due_date else None,
                'Complete': {'status': {'name': notion_status}},
                'Grade': {'number': float(grade)} if grade is not None else None,
                'Weightage': {'number': float(weightage)} if weightage is not None else None,
            }
        }
        return payload

    def send_discord_notification(self, message):
        payload = {"content": message}
        try:
            response = requests.post(self.discord_webhook_url, json=payload)
            if response.status_code == 204:
                print("Discord notification sent successfully.")
            else:
                print(f"Error sending Discord notification: {response.status_code}")
        except Exception as e:
            print(f"Error sending Discord notification: {str(e)}")

    def read_csv(self, filepath):
        url = 'https://api.notion.com/v1/pages'
        responses = []
        with open(filepath, mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            for r in csv_reader:
                assignment, course, due_date, cp, grade, weightage = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip() if len(r) > 4 else None, r[5].strip() if len(r) > 5 else None
                existing_assignments = self.notion.databases.query(
                    database_id=self.database_id,
                    filter={
                        "and": [
                            {"property": "Assignment", "title": {"equals": assignment}},
                            {"property": "Course", "multi_select": {"contains": course}},
                            {"property": "Due Date", "multi_select": {"contains": due_date}}
                        ]
                    }
                )
                # .get("results")
                if not existing_assignments:
                    payload = self.generate_payload(assignment, course, due_date, cp, grade, weightage)
                    try:
                        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
                        responses.append(response.status_code)
                        if response.status_code == 200:
                            print(f'{assignment} successfully uploaded to Notion')
                            self.send_discord_notification(
                                f"Assignment Uploaded: {assignment} - {course}, Due Date: {due_date}, Grade: {grade}, Weightage: {weightage}"
                            )
                        else:
                            print("Error:", response.status_code, response.text)
                    except Exception as e:
                        print(f"Exception occurred while uploading row: {str(e)}")
                else:
                    print(f"Skipping duplicate entry: {assignment} - {course}, Due Date: {due_date}")
        return responses


    def get_due_today(self):
        today = datetime.now().date()
        return [a for a in self.assignments if parse_date(a['due_date']['start']) == today]

    def get_due_this_week(self):
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return [a for a in self.assignments if start_of_week <= parse_date(a['due_date']['start']) <= end_of_week]

    def fetch_assignments_from_notion(self):
        try:
            query = self.notion.databases.query(database_id=self.database_id)
            self.assignments = []
            for page in query['results']:
                assignment = {
                    'assignment': page['properties']['Assignment']['title'][0]['text']['content'],
                    'course': page['properties']['Course']['multi_select'],
                    'due_date': page['properties']['Due Date']['date'],
                    'complete': page['properties']['Complete']['status']['name'],
                    'grade': page['properties']['Grade']['number'] if 'Grade' in page['properties'] and page['properties']['Grade']['number'] is not None else None,
                    'weightage': page['properties']['Weightage']['number'] if 'Weightage' in page['properties'] and page['properties']['Weightage']['number'] is not None else None
                }
                self.assignments.append(assignment)
        except APIResponseError as e:
            print(f"API Error: {e.code} - {e.message}")
        except Exception as e:
            print(f"Error fetching assignments: {str(e)}")
