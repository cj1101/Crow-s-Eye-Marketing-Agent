# Breadsmith Marketing Tool - Scheduling Functionality

## Overview
The scheduling functionality allows you to automate posting to Instagram and Facebook with customizable timing options. This guide explains how to ensure the scheduling tab is visible and functioning in the application.

## Running with Scheduling Enabled

### Method 1: Using the batch file
The easiest way to launch the application with scheduling enabled is to use the batch file:

```
run_with_schedule.bat
```

This script will:
1. Set up the necessary component links
2. Launch the application with scheduling enabled

### Method 2: Using Python directly

To run the application with scheduling enabled using Python:

```
python scheduling_links.py
python launch_app.py
```

Or simply:

```
python run.py
```

The updated `run.py` script automatically checks for and creates the necessary links.

## Using the Scheduling Functionality

### Accessing the Schedule Tab
1. Click the "📅 Schedule" button in the header
2. The application will switch to the "Schedule Posts" tab

### Creating a New Schedule
1. In the Schedule tab, click "Add Schedule"
2. Provide a name for your schedule
3. Choose between Basic and Advanced scheduling modes:
   - Basic: Single posting time for all days
   - Advanced: Different times for different days of the week
4. Set the number of posts per week
5. Configure the date range for the schedule
6. Click "Save Schedule"

### Managing Schedules
- Existing schedules appear in a list
- Click on a schedule to view or edit its details
- Right-click on a schedule for additional options (edit, delete)

## Troubleshooting

If the scheduling tab is not visible:

1. Check that the application is launched with the proper script
2. Verify that the component links were created successfully (ui/scheduling_panel.py, ui/scheduling_dialog.py, etc.)
3. Check the app_log.log file for any error messages
4. Try running the scheduling_links.py script manually before launching the application

## Technical Notes

The scheduling functionality relies on these key files:
- `src/ui/scheduling_panel.py` - Main UI panel for schedule management
- `src/ui/scheduling_dialog.py` - Dialog for creating/editing schedules
- `src/handlers/scheduling_handler.py` - Backend logic for scheduling posts
- `src/models/app_state.py` - Data model for storing schedule information

The `scheduling_links.py` script creates local copies of these files in the root folders to ensure proper importing. 