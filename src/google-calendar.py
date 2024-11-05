#!/bin/env python

import time
import os
import subprocess
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime

server_running  = os.environ['MYNOTES_RUNNING']

# Load your service account credentials
credentials = service_account.Credentials.from_service_account_file(os.environ['GOOGLE_CREDENTIALS'])

# Build the Calendar API service
service = build('calendar', 'v3', credentials=credentials)

# Keep track of existing events by their ID and summary
existing_events = {}

#################################################################################
# Timestamp a message
#################################################################################
def log(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} {text}", flush=True)


log("Google api polling started")

while os.path.exists(server_running):
    # Retrieve the list of events
    events_result = service.events().list(calendarId='primary').execute()
    events = events_result.get('items', [])

    # Create a new dictionary to hold current events
    current_events = {}

    for event in events:
        event_id = event['id']
        event_summary = event['summary']  # Title of the event
        event_start = event['start'].get('dateTime', event['start'].get('date'))  # Start time
        
        # Format the event start time to "yyyy-dd-mm hh:mm:ss"
        if 'dateTime' in event['start']:
            dt_object = datetime.fromisoformat(event_start.replace('Z', '+00:00'))  # Handle UTC
            formatted_start = dt_object.strftime("%Y-%d-%m %H:%M:%S")
        else:
            # For all-day events, you can decide how to format them (use date only or set a time)
            formatted_start = event_start  # Just using the date, no specific time

        current_events[event_id] = event_summary

        # Check if the event is new or updated
        if event_id not in existing_events:
            log(f"New event created: {event_summary}")
            # Call the local script with arguments
            subprocess.run(["mynotes", event_summary, formatted_start])
        elif existing_events[event_id] != event_summary:
            log(f"Event updated: {event_summary}")
            # Call the local script with arguments
            subprocess.run(["mynotes", event_summary, formatted_start])

    # Check for deleted events
    for event_id in list(existing_events.keys()):
        if event_id not in current_events:
            log(f"Event deleted: {existing_events[event_id]}")
            del existing_events[event_id]  # Remove it from the existing events

    # Update the existing events with the current ones
    existing_events = current_events

    # Wait before polling again
    time.sleep(60)  # Poll every minute

log("Google api polling stopped")



