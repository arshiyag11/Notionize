import os
from dotenv import load_dotenv
from src.assignment_tracker import AssignmentTracker
from src.discord_bot import run_bot


def main():
    load_dotenv('config/.env')
    tracker = AssignmentTracker()
    tracker.read_csv("data/assignments.csv")
    run_bot(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()

