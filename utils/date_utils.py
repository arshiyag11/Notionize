from datetime import datetime, timedelta

def parse_date(date_str):
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

