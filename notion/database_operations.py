from notion.notion_client import NotionClient

def upload_assignment_to_notion(assignment_data):
    notion_client = NotionClient()
    notion_client.upload_assignment(assignment_data)

def query_assignments_in_notion(filters):
    notion_client = NotionClient()
    return notion_client.query_assignments(filters)
