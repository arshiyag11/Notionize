from datetime import datetime, timedelta

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return datetime.strptime(date_str, "%d-%m-%Y").date()

def get_due_today(assignments):
    today = datetime.now().date()
    return [a for a in assignments if parse_date(a['due_date']) == today]

def get_due_this_week(assignments):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return [a for a in assignments if start_of_week <= parse_date(a['due_date']) <= end_of_week]
