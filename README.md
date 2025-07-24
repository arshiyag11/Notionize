# Notionize

A personal automation tool that fetches files and data from various platforms (like PrairieLearn) and seamlessly integrates them with your Notion calendar and Google Calendar.

## Overview

Notionize streamlines your workflow by automatically pulling important files, assignments, and schedule data from educational platforms and organizing them in your preferred calendar systems. Never miss a deadline or lose track of important files again.

## Features

- **Multi-Platform File Fetching**: Automatically retrieves files from supported platforms including PrairieLearn
- **CSV Data Processing**: Import and process CSV files containing schedule or assignment data
- **Dual Calendar Integration**: Syncs events and deadlines to both Notion Calendar and Google Calendar
- **Automated Workflow**: Set it and forget it - keeps your calendars updated automatically

## Installation

```bash
git clone https://github.com/yourusername/notionize.git
cd notionize
pip install -r requirements.txt
```

## Configuration

1. **Set up API credentials**:
   - Create a `.env` file in the root directory
   - Add your API keys and credentials:
   ```env
   NOTION_TOKEN=your_notion_integration_token
   NOTION_DATABASE_ID=your_calendar_database_id
   GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
   PRAIRIELEARN_API_KEY=your_prairielearn_key
   ```

2. **Configure platform settings**:
   - Copy `config.example.json` to `config.json`
   - Update the configuration with your specific platform URLs and preferences

## Usage

### Basic Usage

```bash
# Fetch from all configured platforms and sync to calendars
python notionize.py

# Fetch from specific platform only
python notionize.py --platform prairielearn

# Process CSV file and add to calendars
python notionize.py --csv path/to/your/schedule.csv
```

### CSV Format

Your CSV files should include the following columns:
- `title` - Event/assignment title
- `date` - Due date (YYYY-MM-DD format)
- `time` - Time (HH:MM format, optional)
- `description` - Additional details (optional)
- `category` - Event category/type (optional)

Example:
```csv
title,date,time,description,category
Assignment 1,2024-03-15,23:59,Data structures homework,homework
Midterm Exam,2024-03-20,14:00,CS 101 midterm,exam
```

### Advanced Options

```bash
# Dry run - see what would be synced without making changes
python notionize.py --dry-run

# Sync only to Notion (skip Google Calendar)
python notionize.py --notion-only

# Sync only to Google Calendar (skip Notion)
python notionize.py --google-only

# Set custom date range for fetching
python notionize.py --start-date 2024-03-01 --end-date 2024-03-31
```

## Supported Platforms

- **PrairieLearn**: Fetches assignments, quizzes, and exam schedules
- **CSV Files**: Import custom schedule data
- *More platforms coming soon*

## Calendar Integration

### Notion Calendar
- Creates calendar entries in your specified Notion database
- Includes file attachments when available
- Maintains links back to original platform content

### Google Calendar
- Syncs to your primary Google Calendar (configurable)
- Includes event descriptions with platform links
- Sets appropriate reminders for deadlines

## Scheduling

Set up automatic syncing using cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Run every hour
0 * * * * /path/to/python /path/to/notionize/notionize.py

# Run twice daily at 8 AM and 8 PM
0 8,20 * * * /path/to/python /path/to/notionize/notionize.py
```

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Double-check your API credentials in the `.env` file
- Ensure your Notion integration has the correct permissions
- Verify Google Calendar API is enabled in Google Cloud Console

**"Platform connection timeout"**
- Check your internet connection
- Verify platform URLs in `config.json` are correct
- Some platforms may have rate limiting - try running with delays

**"CSV parsing errors"**
- Ensure CSV follows the expected format
- Check for special characters or encoding issues
- Use UTF-8 encoding for CSV files

### Debug Mode

Run with verbose logging to troubleshoot issues:
```bash
python notionize.py --debug
```

## Contributing

This is a personal project, but feel free to fork and adapt it for your own needs! If you add support for additional platforms or improve the CSV processing, I'd love to hear about it.

## License

MIT License - see LICENSE file for details.

## Changelog

### v1.0.0
- Initial release
- PrairieLearn integration
- CSV file processing
- Notion and Google Calendar sync

---

*Built for personal productivity and academic organization*
