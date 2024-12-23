from datetime import datetime
import discord
from discord.ext import commands
from src.assignment_tracker import AssignmentTracker
from utils import parse_date, get_due_today, get_due_this_week, COURSE_COLORS, get_course_embed

# intents = discord.Intents.default()
# intents.message_content = True
# bot = commands.Bot(command_prefix="!", intents=intents)
# tracker = AssignmentTracker()

# @bot.event
# async def on_ready():
#     print(f'Logged in as {bot.user}')

# @bot.command()
# async def menu(ctx):
#     # ... (keep all bot commands as they are)

# # ... (include all other bot commands)

# def run_bot(token):
#     bot.run(token)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tracker = AssignmentTracker()

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
    embed.add_field(name="!shutdown", value="Shuts down the bot (owner-only)", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def due_today(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = tracker.get_due_today()
    if assignments:
        for assignment in assignments:
            grade_info = f", Grade: {assignment['grade']}" if assignment['grade'] is not None else ""
            weightage_info = f", Weightage: {assignment['weightage']}" if assignment['weightage'] is not None else ""
            await ctx.send(f"Assignment Due Today: {assignment['assignment']} in {', '.join([course['name'] for course in assignment['course']])}{grade_info}{weightage_info}")
    else:
        await ctx.send("No assignments are due today.")

@bot.command()
async def due_this_week(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = tracker.get_due_this_week()
    if assignments:
        for assignment in assignments:
            grade_info = f", Grade: {assignment['grade']}" if assignment['grade'] is not None else ""
            weightage_info = f", Weightage: {assignment['weightage']}" if assignment['weightage'] is not None else ""
            await ctx.send(f"Assignment Due This Week: {assignment['assignment']} in {', '.join([course['name'] for course in assignment['course']])}{grade_info}{weightage_info}")
    else:
        await ctx.send("No assignments are due this week.")

@bot.command()
async def due_on(ctx, date):
    tracker.fetch_assignments_from_notion()
    try:
        due_date = datetime.strptime(date, '%Y-%m-%d').date()
        assignments = [a for a in tracker.assignments if tracker.parse_date(a['due_date'][0]['name']) == due_date]
        if assignments:
            for assignment in assignments:
                grade_info = f", Grade: {assignment['grade']}" if assignment['grade'] is not None else ""
                weightage_info = f", Weightage: {assignment['weightage']}" if assignment['weightage'] is not None else ""
                await ctx.send(f"Assignment due on {date}: {assignment['assignment']} in {', '.join([course['name'] for course in assignment['course']])}{grade_info}{weightage_info}")
        else:
            await ctx.send(f"No assignments due on {date}.")
    except ValueError:
        await ctx.send("Invalid date format. Please use YYYY-MM-DD.")

@bot.command()
async def due_in(ctx, *, course):
    tracker.fetch_assignments_from_notion()
    assignments = [a for a in tracker.assignments if any(c['name'].lower() == course.lower() for c in a['course'])]
    if assignments:
        embed = get_course_embed(course, f"Assignments in {course}")
        for assignment in assignments:
            grade_info = f", Grade: {assignment['grade']}" if assignment['grade'] is not None else ""
            weightage_info = f", Weightage: {assignment['weightage']}" if assignment['weightage'] is not None else ""
            embed.add_field(name=assignment['assignment'], value=f"Due on: {assignment['due_date'][0]['name']}{grade_info}{weightage_info}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No assignments found for {course}.")

@bot.command()
async def exam_in(ctx, *, course):
    tracker.fetch_assignments_from_notion()
    exams = [a for a in tracker.assignments if any(c['name'].lower() == course.lower() for c in a['course']) and 'exam' in a['assignment'].lower()]
    if exams:
        for exam in exams:
            grade_info = f", Grade: {exam['grade']}" if exam['grade'] is not None else ""
            weightage_info = f", Weightage: {exam['weightage']}" if exam['weightage'] is not None else ""
            await ctx.send(f"Exam in {course}: {exam['assignment']} on {exam['due_date'][0]['name']}{grade_info}{weightage_info}")
    else:
        await ctx.send(f"No exams found for {course}.")

@bot.command()
async def remaining(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = [a for a in tracker.assignments if a['complete'] != 'Completed']
    if assignments:
        embed = discord.Embed(title="Remaining Assignments", color=discord.Color.red())
        for assignment in assignments:
            grade_info = f", Grade: {assignment['grade']}" if assignment['grade'] is not None else ""
            weightage_info = f", Weightage: {assignment['weightage']}" if assignment['weightage'] is not None else ""
            embed.add_field(name=assignment['assignment'], value=f"Course: {', '.join([course['name'] for course in assignment['course']])}{grade_info}{weightage_info}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("All assignments are completed.")

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
async def weekly_todo(ctx):
    tracker.fetch_assignments_from_notion()
    assignments = tracker.get_due_this_week()
    if assignments:
        embed = discord.Embed(title="Weekly To-Do List", color=discord.Color.blue())
        assignments_by_date = {}
        for assignment in assignments:
            due_date = tracker.parse_date(assignment['due_date'][0]['name'])
            if due_date not in assignments_by_date:
                assignments_by_date[due_date] = []
            assignments_by_date[due_date].append(assignment)
        task_index = 1
        for date, daily_assignments in sorted(assignments_by_date.items()):
            day_name = date.strftime("%A")
            field_value = ""
            for assignment in daily_assignments:
                course = assignment['course'][0]['name']
                status = "[ ]" if assignment['complete'] != 'Complete' else "[✅]"
                grade_info = f", Grade: {assignment['grade']}" if 'grade' in assignment and assignment['grade'] is not None else ""
                weightage_info = f", Weightage: {assignment['weightage']}" if 'weightage' in assignment and assignment['weightage'] is not None else ""
                field_value += f"{task_index}. {status} {assignment['assignment']} ({course}){grade_info}{weightage_info}\n"
                task_index += 1
            embed.add_field(name=f"{day_name} ({date.strftime('%Y-%m-%d')})", value=field_value, inline=False)
        message = await ctx.send(embed=embed)
        for _ in range(task_index - 1):
            await message.add_reaction("✅")
        tracker.todo_message_id = message.id
    else:
        await ctx.send("No assignments are due this week.")


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
            final_score = (total_score / total_weightage)
            embed.add_field(name="Final Score", value=f"{final_score:.2f}%", inline=False)
        else:
            embed.add_field(name="Final Score", value="N/A (No graded assignments)", inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No assignments found for {course}.")


def run_bot(token):
    bot.run(token)
