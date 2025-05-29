from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands
from dotenv import load_dotenv
from src.assignment_tracker import AssignmentTracker
from utils import parse_date
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from notion.notion_client import Client

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_account():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def add_to_google_calendar(assignment):
    service = authenticate_google_account()

    # Use your local timezone explicitly here:
    local_tz_name = "America/Los_Angeles"  
    local_tz = ZoneInfo(local_tz_name)
    
    start_date = datetime.fromisoformat(assignment['start date']['start']).replace(tzinfo=timezone.utc).astimezone(local_tz)
    end_date = datetime.fromisoformat(assignment['due date']['start']).replace(tzinfo=timezone.utc).astimezone(local_tz)

    event = {
        'summary': f"{assignment['assignment']} - {assignment['course'][0]['name']}",
        'description': f"Grade: {assignment['grade']}, Weightage: {assignment['weightage']}",
        'start': {
            'dateTime': start_date.isoformat(),
            'timeZone': local_tz_name,
        },
        'end': {
            'dateTime': end_date.isoformat(),
            'timeZone': local_tz_name,
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"An error occurred: {e}")


def format_date(date_str):
    try:
        return datetime.fromisoformat(date_str).strftime("%d %b %Y")
    except ValueError:
        return "Invalid date"
    
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tracker = AssignmentTracker()
load_dotenv()
NOTION_TOKEN = os.getenv('API_KEY')
NOTION_DATABASE_ID = os.getenv('DATABASE_ID')

notion = Client(auth=NOTION_TOKEN)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def menu(ctx):
    embed = discord.Embed(title="Assignment Tracker Commands", color=discord.Color.blue())
    embed.add_field(name="!menu", value="Shows a menu of commands", inline=False)
    embed.add_field(name="!due_today", value="Shows assignments due today", inline=False)
    embed.add_field(name="!due_this_week", value="Shows assignments due this week", inline=False)
    embed.add_field(name="!due_on <date>", value="Shows assignments due on a specific date (format: YYYY-MM-DD)", inline=False)
    embed.add_field(name="!due_in <course>", value="Shows assignments due for a specific course", inline=False)
    embed.add_field(name="!exam_in <course>", value="Shows exams for a specific course", inline=False)
    embed.add_field(name="!remaining", value="Displays all incomplete assignments", inline=False)
    embed.add_field(name="!course_grade <course>", value="Displays grades for a course, including assignments, weightages, and final score", inline=False)
    embed.add_field(name="!weekly_todo", value="Displays a weekly to-do list of assignments grouped by day", inline=False)
    embed.add_field(name="!upload_csv", value="Uploads assignments from a CSV file to Notion database", inline=False)
    embed.add_field(name="!sync_calendar", value="Syncs Notion assignments with Google Calendar", inline=False)
    embed.add_field(name="!shutdown", value="Shuts down the bot (owner-only)", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def due_in(ctx, *, course):
    tracker.fetch_assignments_from_notion()
    assignments = [a for a in tracker.assignments if any(c['name'].lower() == course.lower() for c in a['course'])]
    
    if assignments:
        embed = discord.Embed(title=f"Assignments in {course}", color=discord.Color.blue())
        for assignment in assignments:
            grade_info = f"Grade: {assignment['grade']}" if assignment.get('grade') is not None else ""
            weightage_info = f"Weightage: {assignment['weightage']}" if assignment.get('weightage') is not None else ""
            if 'due date' in assignment:
                due_date_str = assignment['due date']['start']
                try:
                    due_date = datetime.fromisoformat(due_date_str).strftime("%d %b %Y")
                except ValueError:
                    due_date = "Invalid date"
            else:
                due_date = "No due date available"
            embed.add_field(
                name=assignment['assignment'],
                value=f"Due on: {due_date}\n{grade_info}\n{weightage_info}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No assignments found for {course}.")


@bot.command()
async def exam_in(ctx, *, course):
    tracker.fetch_assignments_from_notion()
    exams = [a for a in tracker.assignments if any(c['name'].lower() == course.lower() for c in a['course']) and 'exam' in a['assignment'].lower()]
    if exams:
        for exam in exams:
            grade_info = f", Grade: {exam['grade']}" if exam.get('grade') is not None else ""
            weightage_info = f", Weightage: {exam.get('weightage')}" if exam.get('weightage') is not None else ""
            due_date = format_date(exam['due date']['start']) if 'due date' in exam else "No due date available"
            await ctx.send(f"Exam in {course}: {exam['assignment']} on {due_date}{grade_info}{weightage_info}")
    else:
        await ctx.send(f"No exams found for {course}.")

# Remaining assignments command
@bot.command()
async def remaining(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = [a for a in tracker.assignments if a['complete'] != 'Completed']
    if assignments:
        embed = discord.Embed(title="Remaining Assignments", color=discord.Color.red())
        for assignment in assignments:
            grade_info = f"Grade: {assignment.get('grade')}" if assignment.get('grade') is not None else ""
            weightage_info = f"Weightage: {assignment.get('weightage')}" if assignment.get('weightage') is not None else ""
            due_date = format_date(assignment['due date']['start']) if 'due date' in assignment else "No due date available"
            
            embed.add_field(
                name=assignment['assignment'],
                value=f"Course: {', '.join([course['name'] for course in assignment['course']])}\nDue: {due_date}\n{grade_info}\n{weightage_info}",
                inline=False
            )
        await ctx.send(embed=embed)
    else:
        await ctx.send("All assignments are completed.")

# Due today command
@bot.command()
async def due_today(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = tracker.get_due_today()
    if assignments:
        embed = discord.Embed(title="Assignments Due Today", color=discord.Color.blue())
        for assignment in assignments:
            grade_info = f"Grade: {assignment.get('grade')}" if assignment.get('grade') is not None else ""
            weightage_info = f"Weightage: {assignment.get('weightage')}" if assignment.get('weightage') is not None else ""
            due_date = format_date(assignment['due date']['start']) if 'due date' in assignment else "No due date available"
            
            embed.add_field(
                name=assignment['assignment'],
                value=f"Course: {', '.join([course['name'] for course in assignment['course']])}\nDue: {due_date}\n{grade_info}\n{weightage_info}",
                inline=False
            )
        await ctx.send(embed=embed)
    else:
        await ctx.send("No assignments are due today.")


@bot.command()
async def shutdown(ctx):
    if ctx.author.id == int(os.getenv("OWNER_ID")):
        await ctx.send("Shutting down the bot.")
        await bot.close()
    else:
        await ctx.send("You do not have permission to shut down the bot.")

@bot.command()
async def upload_csv(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please attach a CSV file to upload.")
        return
    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith('.csv'):
        await ctx.send("Please upload a CSV file.")
        return
    csv_content = await attachment.read()
    csv_path = 'temp_assignments.csv'
    with open(csv_path, 'wb') as f:
        f.write(csv_content)
    try:
        responses = tracker.read_csv(csv_path)
        success_count = responses.count(200)
        await ctx.send(f"CSV uploaded successfully. {success_count} assignments added to Notion.")
    except Exception as e:
        await ctx.send(f"An error occurred while processing the CSV: {str(e)}")
    finally:
        os.remove(csv_path)


@bot.command()
async def due_on(ctx, date_str: str):
    try:
        due_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await ctx.send("Invalid date format. Please use YYYY-MM-DD.")
        return

    tracker.fetch_assignments_from_notion()
    assignments = [a for a in tracker.assignments if parse_date(a['due date']['start']) == due_date]

    if assignments:
        embed = discord.Embed(title=f"Assignments Due on {date_str}", color=discord.Color.blue())
        for assignment in assignments:
            embed.add_field(
                name=assignment['assignment'],
                value=f"Course: {', '.join([course['name'] for course in assignment['course']])}\n"
                      f"Grade: {assignment.get('grade', 'N/A')}\n"
                      f"Weightage: {assignment.get('weightage', 'N/A')}",
                inline=False
            )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No assignments due on {date_str}.")

@bot.command()
async def due_this_week(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = tracker.get_due_this_week()
    
    if assignments:
        embed = discord.Embed(title="Assignments Due This Week", color=discord.Color.green())
        
        for assignment in assignments:
            due_date = format_date(assignment['due date']['start']) if 'due date' in assignment else "No due date available"
            embed.add_field(
                name=assignment['assignment'],
                value=f"Course: {', '.join([course['name'] for course in assignment['course']])}\n"
                      f"Due: {due_date}\n"  # Formatted due date
                      f"Grade: {assignment.get('grade', 'N/A')}\n"
                      f"Weightage: {assignment.get('weightage', 'N/A')}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("No assignments are due this week.")


@bot.command()
async def weekly_todo(ctx):
    tracker.fetch_assignments_from_notion()
    today = datetime.now().date()
    end_of_week = today + timedelta(days=6)

    print("End of week:", end_of_week)
    print("First due date:", tracker.assignments[0]['due date']['start'])
    assignments = [a for a in tracker.assignments if today <= parse_date(a['due date']['start']) <= end_of_week]
    assignments.sort(key=lambda a: (
            parse_date(a['due date']['start']), 
            -float(a.get('weightage', 0)) 
        ))
    if assignments:
        embed = discord.Embed(title="Weekly To-Do List", color=discord.Color.gold())
        for assignment in assignments:
            embed.add_field(
                name=assignment['assignment'],
                value=f"Course: {', '.join([course['name'] for course in assignment['course']])}\n"
                      f"Due: {format_date(assignment['due date']['start'])}\n" 
                      f"Status: {assignment['complete']}\n"
                      f"Grade: {assignment.get('grade', 'N/A')}\n"
                      f"Weightage: {assignment.get('weightage', 'N/A')}",
                inline=False
            )
        await ctx.send(embed=embed)
    else:
        await ctx.send("No assignments in the to-do list for this week.")


@bot.command()
async def course_grade(ctx, *, course):
    tracker.fetch_assignments_from_notion()
    course_assignments = [a for a in tracker.assignments if any(c['name'].lower() == course.lower() for c in a['course'])]
    
    if course_assignments:
        embed = discord.Embed(title=f"Grade for {course}", color=discord.Color.green())
        total_score = 0
        total_weightage = 0
        
        for assignment in course_assignments:
            name = assignment['assignment']
            grade = assignment.get('grade')
            weightage = assignment.get('weightage')
            
            if grade is not None and weightage is not None:
                reflected_score = grade * weightage
                total_score += reflected_score
                total_weightage += weightage
                
                embed.add_field(
                    name=name,
                    value=f"Grade: {grade}%\nWeightage: {weightage}%\nReflected Score: {reflected_score:.2f}",
                    inline=False
                )

        if total_weightage > 0:
            final_score = total_score
            embed.add_field(name="Final Score (out of overall course grade)", value=f"{final_score:.2f}%", inline=False)
        else:
            embed.add_field(name="Final Score", value="N/A (No graded assignments)", inline=False)

        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No assignments found for {course}.")

@bot.command()
async def sync_calendar(ctx):
    await ctx.send("Syncing Notion assignments with Google Calendar...")
    
    tracker.fetch_assignments_from_notion()
    for assignment in tracker.assignments:
        print("adding: ", assignment)
        add_to_google_calendar(assignment)
    
    await ctx.send("Sync complete! Check your Google Calendar for new events.")


def run_bot(token):
    bot.run(token)
