import asyncio
import json
import os
from httplib2 import Credentials
import requests
import csv
import dotenv
from notion_client import Client
from firebase_admin import credentials, messaging, initialize_app, get_app
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import logging

from utils.date_utils import parse_date

COURSE_COLORS = {
    "CS598": discord.Color.blue(),
    "CS411": discord.Color.green(),
    "CS357": discord.Color.magenta(),
    "PLPA": discord.Color.purple(),
    "CS461": discord.Color.yellow(),
    "CS442": discord.Color.dark_grey(),
}

def get_course_embed(course_name, title):
    color = COURSE_COLORS.get(course_name, discord.Color.default())
    return discord.Embed(title=title, color=color)

class AssignmentTracker:
    def __init__(self):
        dotenv.load_dotenv()
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

    def generate_payload(self, assignment, course, start_date, end_date, cp, grade, weightage):
        valid_statuses = {
            'Not Started': 'Not started',
            'In Progress': 'In progress',
            'Completed': 'Complete',
        }
        notion_status = valid_statuses.get(cp, "Not started")
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                'Name': {'title': [{'text': {'content': str(assignment)}}]},
                'Course': {'multi_select': [{'name': str(course)}]},
                'Start Date': {'date': {'start': start_date}},
                'End Date': {'date': {'start': end_date}},
                'Complete': {'status': {'name': notion_status}},
                'Grade': {'number': float(grade)} if grade and grade != 'Not Started' else None,
                'Weightage': {'number': float(weightage)} if weightage else None,
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
            next(csv_reader)
            for row in csv_reader:
                assignment = row[0].strip()
                course = row[1].strip()
                start_date = row[2].strip()
                end_date = row[3].strip()
                cp = row[4].strip()
                grade = row[5].strip()
                weightage = row[6].strip()
                repeat_assignment = row[7].strip()
                repeat_weeks = int(row[8].strip()) if repeat_assignment.lower() == 'yes' else 1

                # Check if the assignment already exists in the database
                existing_assignments = self.notion.databases.query(
                    database_id=self.database_id,
                    filter={
                        "and": [
                            {"property": "Name", "title": {"equals": assignment}},
                            {"property": "Course", "multi_select": {"contains": course}},
                            {"property": "End Date", "date": {"equals": end_date}}
                        ]
                    }
                ).get("results")

                # Handle repeat assignments
                if repeat_assignment.lower() == 'yes':
                    repeated_assignments = self.generate_repeating_assignments(
                        assignment, course, start_date, end_date, weightage, repeat_weeks)
                    
                    for repeated_assignment in repeated_assignments:
                        # Check if the repeated assignment already exists
                        repeated_existing = self.notion.databases.query(
                            database_id=self.database_id,
                            filter={
                                "and": [
                                    {"property": "Name", "title": {"equals": repeated_assignment['Assignment Name']}},
                                    {"property": "Course", "multi_select": {"contains": repeated_assignment['Course']}},
                                    {"property": "End Date", "date": {"equals": repeated_assignment['End Date']}}
                                ]
                            }
                        ).get("results")

                        if not repeated_existing:
                            payload = self.generate_payload(
                                repeated_assignment['Assignment Name'], 
                                repeated_assignment['Course'],
                                repeated_assignment['Start Date'],
                                repeated_assignment['End Date'],
                                cp,
                                grade,
                                weightage
                            )
                            try:
                                response = requests.post(url, headers=self.headers, data=json.dumps(payload))
                                responses.append(response.status_code)
                                if response.status_code == 200:
                                    print(f'{repeated_assignment["Assignment Name"]} successfully uploaded to Notion')
                                    self.send_discord_notification(
                                        f"Assignment Uploaded: {repeated_assignment['Assignment Name']} - {repeated_assignment['Course']}, Date: {repeated_assignment['End Date']}, Grade: {grade}, Weightage: {weightage}"
                                    )
                                else:
                                    print("Error:", response.status_code, response.text)
                            except Exception as e:
                                print(f"Exception occurred while uploading row: {str(e)}")
                        else:
                            print(f"Skipping duplicate entry: {repeated_assignment['Assignment Name']} - {repeated_assignment['Course']}, Date: {repeated_assignment['End Date']}")
                elif not existing_assignments:
                    payload = self.generate_payload(assignment, course, start_date, end_date, cp, grade, weightage)
                    try:
                        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
                        responses.append(response.status_code)
                        if response.status_code == 200:
                            print(f'{assignment} successfully uploaded to Notion')
                            self.send_discord_notification(
                                f"Assignment Uploaded: {assignment} - {course}, Date: {end_date}, Grade: {grade}, Weightage: {weightage}"
                            )
                        else:
                            print("Error:", response.status_code, response.text)
                    except Exception as e:
                        print(f"Exception occurred while uploading row: {str(e)}")
                else:
                    print(f"Skipping duplicate entry: {assignment} - {course}, Date: {end_date}")
        return responses
    
    def fetch_assignments_from_notion(self):
        query = self.notion.databases.query(database_id=self.database_id)
        self.assignments = []
        for page in query['results']:
            assignment = {
                'assignment': page['properties']['Name']['title'][0]['text']['content'],
                'course': page['properties']['Course']['multi_select'],
                'start date': page['properties']['Start Date']['date'],
                'due date': page['properties']['End Date']['date'],
                'complete': page['properties']['Complete']['status']['name'],
                'grade': page['properties']['Grade']['number'] if 'Grade' in page['properties'] and page['properties']['Grade']['number'] is not None else None,
                'weightage': page['properties']['Weightage']['number'] if 'Weightage' in page['properties'] and page['properties']['Weightage']['number'] is not None else None
            }
            self.assignments.append(assignment)


    def setup_google_calendar(self):
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(requests.Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        self.calendar_service = build('calendar', 'v3', credentials=creds)

    # def add_to_google_calendar(self, assignment):
    #     event = {
    #         'summary': f"{assignment['assignment']} - {assignment['course'][0]['name']}",
    #         'description': f"Grade: {assignment['grade']}, Weightage: {assignment['weightage']}",
    #         'start': {
    #             'date': assignment['start date'][0]['name'],
    #             'timeZone': 'America/Chicago',
    #         },
    #         'end': {
    #             'date': assignment['due date'][0]['name'],
    #             'timeZone': 'America/Chicago',
    #         },
    #     }
    #     event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
    #     print(f"Event created: {event.get('htmlLink')}")
    def add_to_google_calendar(self, assignment):
        # Check for existing events
        start_time = assignment['start date']['start']
        end_time = assignment['due date']['start']
        events_result = self.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            q=assignment['assignment']  # Search for events with the same title
        ).execute()
        existing_events = events_result.get('items', [])

        # If no matching event is found, create a new one
        if not existing_events:
            event = {
                'summary': f"{assignment['assignment']} - {assignment['course'][0]['name']}",
                'description': f"Grade: {assignment['grade']}, Weightage: {assignment['weightage']}",
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'America/Chicago',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'America/Chicago',
                },
            }
            event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created: {event.get('htmlLink')}")
        else:
            print(f"Event already exists: {assignment['assignment']}")


    

    def generate_repeating_assignments(self, assignment_name, course, start_date, end_date, weightage, repeat_weeks):
        """
        Generate multiple assignments for repeated weeks but do not include 'Repeat Assignment' or 'Repeat Weeks' in the payload.
        """
        assignments = []
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        for i in range(repeat_weeks):
            # Adjust dates for each week
            assignment_start = start_datetime + timedelta(weeks=i)
            assignment_end = end_datetime + timedelta(weeks=i)
            assignments.append({
                "Assignment Name": assignment_name + str(i+1),
                "Course": course,
                "Start Date": assignment_start.strftime('%Y-%m-%d %H:%M:%S'),
                "End Date": assignment_end.strftime('%Y-%m-%d %H:%M:%S'),
                "Complete": "Not Started",
                "Grade": 0,  # Default or user-defined grade
                "Weightage": weightage,  # Default weightage or from CSV
            })
        return assignments

    def parse_date(self, date_str):
        date_str = date_str.split('T')[0]
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD or DD-MM-YYYY.")


    def get_due_today(self):
        """Return a list of assignments that are due today."""
        today = datetime.now().date()
        return [assignment for assignment in self.assignments if self.parse_date(assignment['due date']['start']) == today]


    def get_due_this_week(self):
        start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return [a for a in self.assignments if start_of_week <= parse_date(a['due date']['start']) <= end_of_week]