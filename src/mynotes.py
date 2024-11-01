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
import schedule
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

def save_note_to_db(name, note, timer):
    """Saves note with a timer in MongoDB."""
    collection.insert_one({"name": name, "note": note, "timer": timer, "displayed": False})
    log(f"Note saved as '{name}' with timer set for {timer}")



def retrieve_note_and_show(name):
    """Retrieve the note from MongoDB and display it using kdialog."""
    result = collection.find_one({"name": name})
    if result:
        note = result["note"]
        subprocess.run(["kdialog", "--msgbox", note])

        # Optionally, delete the note after it's displayed
        collection.delete_one({"name": name})


def set_timer(name, timer):
    """Schedules a job at the specified datetime to display the note."""
    schedule_time = parser.parse(timer)
    current_time = datetime.now()

    if schedule_time > current_time:
        delay_seconds = (schedule_time - current_time).total_seconds()
        schedule.enter(delay_seconds, 1, retrieve_note_and_show, (name,))
    else:
        log(f"ERROR: The specified time {timer} is in the past.")


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
                                    note = ' '.join(line.split()[1:])

                        if is_valid_date(sched):
                            save_note_to_db(filename, note, sched)

                            log(f"Removing {file_path}")
                            os.remove(file_path)

                            log(f"Schedule {file_path} for {sched}")
                            set_timer(filename, sched)
                        else:
                            print(f"ERROR: {sched} is not a valid date and time.")
        
        time.sleep(10)
    
    log("mynotes shutting down")

if __name__ == "__main__":
    main()
