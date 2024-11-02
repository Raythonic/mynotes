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
client = pymongo.MongoClient(os.environ['MONGODB'])
db = client["mynotes"]
collection = db["notes"]
timers = {}

log("Connected to mongodb")

def cancel_note(name):
    timer_name = name.replace(":", "")
    
    if timer_name in timers:
        timers[timer_name].cancel()
        del timers[timer_name]

        log(f"Timer for {name} cancelled")
    else:
        log(f"ERROR: No timer found for {name}")


def show_notes():
    notes = collection.find()

    log("Reading notes from mongo")

    for note in notes:
        log(f"Name: {note['name']} Sched: {note['sched']} Displayed: {note['displayed']}")

def save_note_to_db(name, sched, note):
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


def post_note(name, sched, note):

    filename = name.replace(":", "")

    # Define the directory where notes will be stored
    postits_dir = os.path.expanduser('~/PostIts')

    # Create the directory if it doesn't exist
    os.makedirs(postits_dir, exist_ok=True)

    # Construct the file path
    file_path = os.path.join(postits_dir, f"{filename}.txt")

    # Write the note to the file
    with open(file_path, 'w') as postit_file:
        postit_file.write(f"{sched} {note}")
    

def retrieve_note_and_show(name):
    """Retrieve the note from MongoDB and display it using kdialog."""

    log(f"Timer for {name} popped")

    result = collection.find_one({"name": name})

    if result:
        os.environ["DISPLAY"] = ":0"
        subprocess.Popen(["notify-send", "--expire-time=0", "From mynotes server", result["note"]])
        post_note(result['name'], result['sched'], result['note'])

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


def schedule_note(name, sched, note):
    """Schedules a job at the specified datetime to display the note."""
    save_note_to_db(name, sched, note)

    # Parse the "yyyy-mm-dd hh:mm:ss" formatted string into a datetime object
    schedule_time = parser.parse(sched)
    current_time = datetime.now()
    timer_name = name.replace(":", "")

    if schedule_time > current_time:
        # Calculate the delay in seconds
        delay_seconds = (schedule_time - current_time).total_seconds()
        
        # Use threading.Timer to run the function after delay_seconds
        timers[timer_name] = threading.Timer(delay_seconds, retrieve_note_and_show, args=[name])
                                             
        timers[timer_name].start()
       
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

    if filename == "command":
        return True
    
    # Regular expression to match 1 to 20 digits followed by ".txt"
    pattern = r'^\d{1,20}\.txt$'
    return bool(re.match(pattern, filename))


def process_command(command):
    log(f"Command:{command}")
    if command == "show":
        show_notes()
    
    if command.startswith("cancel:"):
        name = f"note:{command.split(":")[1]}"
        cancel_note(name)

def main():

    # Check if arguments are provided
    if len(sys.argv) < 2:
        log("Usage: mynotes.py 'mynotes_dir'")
        return

    # Parse arguments
    mynotes_dir = sys.argv[1]

    log("mynotes server started.")
    wait_msg_issued = False

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
                    
                    # Ensure we only process files
                    if os.path.isfile(file_path):

                        text = ""
                        # Read the file in.  First line must be schedule
                        with open(file_path, 'r') as file:

                            # Read each line in the file
                            for line in file:
                                text += line

                        # If a command came in, run that command
                        if filename == "command":
                            process_command(text.strip())
                        else:
                            sched = ' '.join(text.split()[:2])
                            note = ' '.join(text.split()[2:])

                            if is_valid_date(sched):
                                name = f"note:{filename.split('.')[0]}"

                                log(f"Scheduling {name} for {sched}")
                                schedule_note(name, sched, note)
                            else:
                                log(f"ERROR: {sched} is not a valid date and time.")

                        log(f"Removing {file_path}")
                        os.remove(file_path)
        
        
        if not wait_msg_issued:
            log("Waiting for work...")
            wait_msg_issued = True
        
        time.sleep(1)
    
    log("mynotes server shutting down")

if __name__ == "__main__":
    main()
