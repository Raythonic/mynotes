import sys
import os
import schedule
import time
import pymongo
from datetime import datetime
from dateutil import parser
import subprocess

# MongoDB setup (assuming MongoDB is running locally on default port 27017)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["user_notes"]
collection = db["notes"]

def save_note_to_db(name, note, timer):
    """Saves note with a timer in MongoDB."""
    collection.insert_one({"name": name, "note": note, "timer": timer, "displayed": False})
    print(f"Note saved as '{name}' with timer set for {timer}")

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
        print("The specified time is in the past.")

def is_valid_date(date_string, date_format="%Y-%m-%d"):
    try:
        # Attempt to parse the date_string with the specified format
        parsed_date = datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        # If parsing fails, return False
        return False

def main():
    # Check if arguments are provided
    if len(sys.argv) < 3:
        print("Usage: mynotes.py 'mynotes_dir'")
        return

    # Parse arguments
    mynotes_dir = sys.argv[1]

    # Run the scheduler continuousl

    while os.path.exists("/tmp/.mynotes.running"):

        print("Waiting for notes...")

        # Work comes in by way of a file in /home/mynotes/  Any file name is acceptable and
        # it will be used as the name under which it is logged to MongoDB
        if any(os.path.isfile(os.path.join(mynotes_dir, f)) for f in os.listdir(mynotes_dir)):

            # We have work to do.  Read that work from the file, log it, and set the timer
            for filename in os.listdir(mynotes_dir):
                file_path = os.path.join(mynotes_dir, filename)

                note=""
                sched=""
                
                # Ensure we only process files
                if os.path.isfile(file_path):

                    # Read the file in.  First line must be schedule
                    with open(file_path, 'r') as file:

                        # Read each line in the file
                        for line in file:

                            # If we don't have a schedule, get it
                            if not sched:
                                sched=line
                            else:
                                note += line.strip()  # Remove any leading/trailing whitespace

                    if is_valid_date(sched):
                        save_note_to_db(filename, note, sched)
                        os.remove(file_path)

                        set_timer(filename, sched)
                    else:
                        print(f"ERROR: {sched} is not a valid date and time.")

        
        time.sleep(10)

if __name__ == "__main__":
    main()
