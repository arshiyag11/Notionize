import os
import dotenv
from notion_client import Client

dotenv.load_dotenv()

class NotionClient:
    def __init__(self):
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("DATABASE_ID")

    def upload_assignment(self, assignment_data):
        """ Upload an assignment to Notion. """
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Assignment": {"title": [{"text": {"content": assignment_data['assignment']}}]},
                "Course": {"multi_select": [{"name": assignment_data['course']}]},
                "date": {"multi_select": [{"name": assignment_data['due_date']}]},
                "Complete": {"status": {"name": assignment_data['status']}},
                "Grade": {"number": assignment_data['grade']},
                "Weightage": {"number": assignment_data['weightage']}
            }
        }
        self.notion.pages.create(**payload)

    def query_assignments(self, filters):
        """ Query assignments in Notion database. """
        return self.notion.databases.query(database_id=self.database_id, filter=filters)
