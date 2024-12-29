import discord

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




# from datetime import datetime, timedelta
# import discord

# COURSE_COLORS = {
#     "CS598": discord.Color.blue(),
#     "CS411": discord.Color.green(),
#     "CS357": discord.Color.magenta(),
#     "PLPA": discord.Color.purple(),
#     "CS461": discord.Color.yellow(),
#     "CS442": discord.Color.dark_grey(),
# }

# def get_course_embed(course_name, title):
#     color = COURSE_COLORS.get(course_name, discord.Color.default())
#     return discord.Embed(title=title, color=color)

# def parse_date(due_date_str):
#     try:
#         return datetime.strptime(due_date_str, '%Y-%m-%d').date()
#     except ValueError:
#         return datetime.strptime(due_date_str, '%d-%m-%Y').date()
    
# def get_due_today(assignments):
#     today = datetime.now().date()
#     return [a for a in assignments if parse_date(a['due_date']) == today]

# def get_due_this_week(assignments):
#     today = datetime.now().date()
#     start_of_week = today - timedelta(days=today.weekday())
#     end_of_week = start_of_week + timedelta(days=6)
#     return [a for a in assignments if start_of_week <= parse_date(a['due_date']) <= end_of_week]

# def parse_date(date_str):
#     try:
#         return datetime.strptime(date_str, "%Y-%m-%d").date()
#     except ValueError:
#         return datetime.strptime(date_str, "%d-%m-%Y").date()

