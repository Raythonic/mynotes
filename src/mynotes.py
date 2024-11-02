#!/bin/env python
#######################################################################################################################
# This python program is a continously running "server" that scans for work in /home/rwalk/mynotes/nnnnn.txt file
# then logs those messages in mongodb.  There is a schedule associated with the note.  When that expires,
# the note will popup on the KDE desktop and then be deleted from the mongodb database.
#
# See mynotes.sh for the script that you should interface with.  This Python program is not meant to be run
# from the commandline, though with care it can.  But you have to emulate what mynotes.sh does
#######################################################################################################################

import sys
import os
import threading
import time
import pymongo
from datetime import datetime
from dateutil import parser
import subprocess
import re

def log(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} {text}", flush=True)

# MongoDB setup (assuming MongoDB is running locally on default port 27017)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mynotes"]
collection = db["notes"]

log("Connected to mongodb")

def save_note_to_db(name, note, sched):
    """Saves note with a timer in MongoDB. Updates if the document exists, otherwise inserts."""
    # Create a filter to find the document by name
    filter = {"name": name}
    
    # Create an update operation
    update = {
        "$set": {
            "note": note,
            "sched": sched,
            "displayed": False
        }
    }
    
    # Use update_one with the upsert option
    collection.update_one(filter, update, upsert=True)
    
    log(f"Note inserted as '{name}' with timer set for {sched}")

def retrieve_note_and_show(name):
    """Retrieve the note from MongoDB and display it using kdialog."""

    log(f"Timer for {name} popped")

    result = collection.find_one({"name": name})


    if result:
        os.environ["DISPLAY"] = ":0"
        subprocess.Popen(["notify-send", "--expire-time=0", "From mynotes server", result["note"]])

        # Mark note as displayed
        filter = {"name": name}
    
        # Create an update operation
        update = {
            "$set": {
                "displayed": True
            }
        }
        
        # Use update_one with the upsert option
        collection.update_one(filter, update)
    else:
        log(f"ERROR: {name} was not found in MongoDB")


def schedule_note(name, sched):
    """Schedules a job at the specified datetime to display the note."""
    # Parse the "yyyy-mm-dd hh:mm:ss" formatted string into a datetime object
    schedule_time = parser.parse(sched)
    current_time = datetime.now()

    if schedule_time > current_time:
        # Calculate the delay in seconds
        delay_seconds = (schedule_time - current_time).total_seconds()
        
        # Use threading.Timer to run the function after delay_seconds
        threading.Timer(delay_seconds, retrieve_note_and_show, args=[name]).start()
        
        log(f"{name} has been scheduled for {sched} (in {delay_seconds} seconds)")
    else:
        log(f"Running {name} now")
        retrieve_note_and_show(name)


def is_valid_date(date_string, date_format="%Y-%m-%d %H:%M:%S"):
    try:
        # Attempt to parse the date_string with the specified format
        parsed_date = datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        # If parsing fails, return False
        return False


def is_valid_filename(filename):
    # Regular expression to match 1 to 20 digits followed by ".txt"
    pattern = r'^\d{1,20}\.txt$'
    return bool(re.match(pattern, filename))


def main():

    # Check if arguments are provided
    if len(sys.argv) < 2:
        log("Usage: mynotes.py 'mynotes_dir'")
        return

    # Parse arguments
    mynotes_dir = sys.argv[1]

    log("mynotes server started.  Waiting for work...")

    # Run the scheduler continuously
    while os.path.exists("/tmp/.mynotes.running"):

        # Work comes in by way of a file in /home/mynotes/nnnnn.txt  Any file name is acceptable and
        # it will be used as the name under which it is logged to MongoDB
        if any(os.path.isfile(os.path.join(mynotes_dir, f)) for f in os.listdir(mynotes_dir)):

            # We have work to do.  Read that work from the file, log it, and set the timer
            for filename in os.listdir(mynotes_dir):

                # File name must be in format nnnn.txt
                if is_valid_filename(filename):
                    file_path = os.path.join(mynotes_dir, filename)

                    log(f"Processing file {file_path}")

                    note=""
                    sched=""
                    
                    # Ensure we only process files
                    if os.path.isfile(file_path):

                        # Read the file in.  First line must be schedule
                        with open(file_path, 'r') as file:

                            # Read each line in the file
                            for line in file:

                                note = line

                                # If we don't have a schedule, get it
                                if not sched:
                                    sched = ' '.join(line.split()[:2])
                                    note = ' '.join(line.split()[2:])

                        if is_valid_date(sched):
                            name = f"note:{filename.split('.')[0]}"

                            save_note_to_db(name, note, sched)

                            log(f"Removing {file_path}")
                            os.remove(file_path)

                            log(f"Scheduling {name} for {sched}")
                            schedule_note(name, sched)
                        else:
                            print(f"ERROR: {sched} is not a valid date and time.")
        
        time.sleep(1)
    
    log("mynotes server shutting down")

if __name__ == "__main__":
    main()
