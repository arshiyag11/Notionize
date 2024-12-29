import csv
from notion.database_operations import upload_assignment_to_notion

def read_csv(filepath):
    responses = []
    with open(filepath, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            assignment_data = {
                'assignment': row[0],
                'course': row[1],
                'due_date': row[2],
                'status': row[3],
                'grade': row[4] if row[4] else None,
                'weightage': row[5] if row[5] else None
            }
            upload_assignment_to_notion(assignment_data)
            responses.append(200)
    return responses
