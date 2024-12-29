# Notionize: Notion and Google Calendar Sync with Discord Integration

**Notionize** is a Python-based project designed to synchronize your **Notion Dashboard** with **Google Calendar**, offering enhanced functionality through a **Discord bot interface**. This tool is aimed at streamlining task and event management for students, particularly at **UIUC**, by integrating multiple platforms and providing simple, command-based interaction.

---

## Key Features

- **Two-way Synchronization**: Sync events between your Notion Dashboard and Google Calendar seamlessly.
- **CSV File Upload**: Easily upload CSV files to handle repetitive assignments across multiple weeks.
- **Discord Bot Integration**: Interact with your Notion and Google Calendar data directly through Discord.
- **Weekly To-Do List**: Automatically generate a weekly to-do list based on your calendar events.
- **Multiple Calendar Support**: Sync multiple Google Calendar accounts.
- **Flexible Event Handling**: Handle both date-only and date-time events.
- **Automatic Updates**: Events automatically update across platforms when modified.
- **Event Detail Extraction**: Extract details from Notion and add them to Google Calendar events.
- **Google Calendar Event Deletion**: Mark tasks as "Done" in Notion and automatically delete the corresponding Google Calendar events.
- **CLI Commands**: Add or delete events from both Notion and Google Calendar directly via command line.
- **Weekly To-Do List Display**: View your to-do list directly within Discord.

---

## Setup Process

### 1. Install Python
Ensure you have **Python 3.7+** installed. If not, download it from [python.org](https://www.python.org/downloads/).

### 2. Set Up Google Calendar API

1. Visit [Google Developers Console](https://console.developers.google.com/).
2. Create a new project.
3. Enable the **Google Calendar API** for your project.
4. Set up an **OAuth consent screen**.
5. Create **OAuth 2.0 Client ID credentials** and download the **client secret file** (`credentials.json`).

### 3. Set Up Notion API

1. Go to [Notion Developers](https://www.notion.so/my-integrations) and create a new integration.
2. Obtain the **Internal Integration Token** (API key).
3. Share your **Notion Database** with the integration.

### 4. Discord Bot Setup

1. Create a new application on the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a **bot** within the application.
3. Add the bot to your Discord server with the necessary permissions (e.g., send messages, manage events).
4. Obtain your **Discord bot token**.

### 5. Prepare the Python Script

1. Clone the repository or download the project code.
2. Install the required Python libraries by running:

```bash
pip install -r requirements.txt
```
## Configuring the Script

Configure the following settings in the main Python script (`config.py` or directly within the script):

- **API_KEY**: Your notion API key
- **DATABASE_ID**: The ID of your Notion database.
- **DISCORD_TOKEN**: Your Discord bot token.
- **DISCORD_WEBHOOK_URL**: Your discord webhook url.
- **GOOGLE_CREDENTIALS**: Path to your `credentials.json` file.

NOTE: use these as environment variables.

### 6. Configure Notion Database

Ensure that your **Notion database** is structured appropriately with columns such as:

- **Name**
- **Course**
- **Start Date**
- **End Date**
- **Complete**
- **Grade**
- **Weightage**
  
Once your database is set up, **share the database with the Notion integration** to enable synchronization.

---

## Running the Script

After configuring the settings, run the main Python script to initiate the bot and start the synchronization process:

```bash
python main.py
```
### Using the Discord Bot

Once the bot is running, you can use the ```!menu``` command to see all other useful commands. 

---

### Limitations

Platform Limitations: Currently, Canvas and PrairieLearn assignments cannot be fetched due to API integration complexities.
Stability: The project is in its initial development stage, so you may encounter occasional bugs or issues.

---

### Future Development
Integration with other popular student platforms like Canvas, PrairieLearn, and Gradescope.
Improved error handling and stability.
Expanded functionality for the Discord bot (e.g., notifications, reminders).
Support for more calendar services and task management platforms.

---

### Support and Contributions
This project is open for suggestions and improvements! If you have feedback, ideas, or want to contribute, feel free to submit issues or pull requests on the GitHub repository.
For any questions or inquiries, contact: arshiya5@illinois.edu

---
### License
This project is licensed under the MIT License – see the LICENSE file for details.
