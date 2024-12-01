#!/bin/env python3
#######################################################################################################################
# This python program is a continously running "server" that scans for work in /home/rwalk/mynotes/nnnnn.txt file
# then logs those messages in mongodb.  There is a schedule associated with the note.  When that expires,
# the note will popup on the KDE desktop and then be deleted from the mongodb database.
#
# Commands can be issued by placing the command and its arguments in mynote/command file.
#   Valid commands:
#           show - List all notes in the database
#           cancel nnn - Cancel the timer for note nnn
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

timers          = {}
server_running  = os.environ['MYNOTES_RUNNING']

#################################################################################
# Timestamp a message
#################################################################################
def log(text):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{current_time} {text}", flush=True)



#################################################################################
# Remove running file and exit with code passed
#################################################################################
def get_out(code):
    os.remove(server_running)
    sys.exit(code)


#################################################################################
# Restart all the timers (run upon startup)
#################################################################################
def catchup():
    notes = collection.find({"displayed": False})

    # Each note not displayed yet, schedule it for the time remaining
    for note in notes:
        log(f"Restarting timer for: Name: {note['name']} Sched: {note['sched']}")
        schedule_note(note['name'], note['sched'])



#################################################################################
# Cancel a note's schedule
#################################################################################
def cancel_note(name):
    
    # If the timer object exists...
    if name in timers:

        # Stop the timers
        timers[name].cancel()

        # Remove the timer object
        del timers[name]

        log(f"Timer for {name} cancelled")

    else:
        log(f"ERROR: No timer found for {name}")

    # Use update_one with the upsert option
    result = collection.delete_one({"name": name})
    
    # If note was found...
    if result.deleted_count > 0:
        log(f"Note '{name}' deleted from database")



#################################################################################
# Show all notes from the database 
#################################################################################
def show_notes():
    notes = collection.find()

    log("Reading notes from MongoDB")

    # Show each note from the database
    for note in notes:

        if note['displayed']:
            if note['sched'] == "1970-01-01 00:00:00":
                status = "was displayed immediately"
            else:
                status = f"was displayed at {note['sched']}"
        else:
            status = f"will be displayed at {note['sched']}"

        log(f"{note['name']} {status} =>  \"{note['note']}\"")



#################################################################################
# Purge MongoDB database
#################################################################################
def purge_database():

    # Cancel all timers first
    stop_timers()

    collection.delete_many({})
    log("MongoDB database purged")



#################################################################################
# Save a note to the database.  Update it if it already exists.
#################################################################################
def save_note_to_db(name, sched, note):

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
    
    log(f"Note saved as '{name}' with timer set for {sched}")



#################################################################################
# Post the note to the Post its folder for the desktop
#################################################################################
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
    


#################################################################################
# Read a note from the database and notify KDE
#################################################################################
def retrieve_note_and_show(name):
     
    log(f"Timer for {name} popped")

    result = collection.find_one({"name": name})

    if result:
        os.environ["DISPLAY"] = ":0"
        subprocess.Popen(["notify-send", "--expire-time=0", "My Notes", result["note"]])
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

        # Remove it from the timers array
        if name in timers:
            timers[name].cancel()
            del timers[name]
    else:
        log(f"ERROR: {name} was not found in MongoDB")



#################################################################################
# Schedule a note and start its timer
#################################################################################
def schedule_note(name, sched):

    # Parse the "yyyy-mm-dd hh:mm:ss" formatted string into a datetime object
    schedule_time   = parser.parse(sched)
    current_time    = datetime.now()

    if schedule_time > current_time:
        # Calculate the delay in seconds
        delay_seconds = (schedule_time - current_time).total_seconds()
        
        # Use threading.Timer to run the function after delay_seconds
        timers[name] = threading.Timer(delay_seconds, retrieve_note_and_show, args=[name])
                                             
        timers[name].start()
       
        log(f"{name} has been scheduled for {sched} (in {delay_seconds} seconds)")
    else:
        log(f"Running {name} now")
        retrieve_note_and_show(name)



#################################################################################
# Check the date format
#################################################################################
def is_valid_date(date_string, date_format="%Y-%m-%d %H:%M:%S"):
    try:
        # Attempt to parse the date_string with the specified format
        parsed_date = datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        # If parsing fails, return False
        return False



#################################################################################
# Validate file name found in work queue ($HOME/mynotes/*.txt)
#################################################################################
def is_valid_filename(filename):

    if filename == "command":
        return True
    
    # Regular expression to match 1 to 20 digits followed by ".txt"
    pattern = r'^\d{1,20}\.txt$'
    return bool(re.match(pattern, filename))


#################################################################################
# Execute user's command from mynotes/command file
#################################################################################
def process_command(command):

    log(f"Command:{command}")

    # Determine the command and execute it

    # Show all the notes in the database
    if command == "show":
        show_notes()
        return

    # Show all the notes in the database
    if command == "purge":
        purge_database()
        return
    
    # Cancel a note's schedule
    if command.startswith("cancel:"):
        note_num = command.split(":")[1]
        name = f"note{note_num}"

        if note_num != "all":
            cancel_note(name)
        else:
            notes = collection.find({"displayed": False})

            # Each note not displayed yet, schedule it for the time remaining
            for note in notes:
                cancel_note(note['name'])
        return
    
    log(f"ERROR: Command {command} not recognized")


#################################################################################
# Stop all timers
#################################################################################
def stop_timers():
    for timer in timers.values():
        timer.cancel()

    log("All timers cancelled")


#################################################################################
#                               MAIN LOGIC                                      #
#################################################################################
def main():

    # Check if arguments are provided
    if len(sys.argv) < 2:
        log("Usage: mynotes.py 'mynotes_dir'")
        get_out(0)

    # Parse arguments
    mynotes_dir = sys.argv[1]

    log("mynotes server started")
    caught_up       = False
    wait_msg_issued = False

    # Run the scheduler continuously
    while os.path.exists(server_running):

        # Restart timers for undisplayed notes
        if not caught_up:
            catchup()
            caught_up = True

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
                                name = f"note{filename.split('.')[0]}"

                                log(f"Scheduling {name} for {sched}")
                                save_note_to_db(name, sched, note)
                                schedule_note(name, sched)
                            else:
                                log(f"ERROR: {sched} is not a valid date and time")

                        log(f"Removing {file_path}")
                        os.remove(file_path)
        
        
        if not wait_msg_issued:
            log("Waiting for work...")
            wait_msg_issued = True
        
        time.sleep(1)
    
    
    stop_timers()
    log("mynotes server shutting down")


#################################################################################
#################################################################################
#                               Program start                                   #
#################################################################################
#################################################################################


# MongoDB setup (assuming MongoDB is running locally on default port 27017)
client = pymongo.MongoClient(os.environ['MONGODB'])

if client:
    log("Connected to MongoDB database")
    db = client["mynotes"]
    collection = db["notes"]
else:
    log("ERROR: Failed to connect to MongoDB")
    get_out(1)


if __name__ == "__main__":
    main()
