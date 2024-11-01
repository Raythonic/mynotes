#!/bin/bash

#######################################################################################################################
# This script is a controlling script for the mynotes.py server.  With this script you can:
#   1. start the mynotes server: mynotes start
#   2. stop the mynotes server: mynote stop
#   3. schedule a note with the mynotes server: mynote "text..."
#######################################################################################################################

[ -z "$1" ] && echo "Usage: mynotes [start|stop|text]" && exit 0

declare mydir="$HOME/mynotes"
declare log="$HOME/logs/mynotes.log"

# Initalize .settings is the is a first run
if [ ! -d $HOME/mynotes ]
then
    mkdir $HOME/mynotes
    echo "file: 1" > $mydir/.settings
fi

declare option="$1"
declare -i file_idx=$(grep "^file: " $mydir/.settings | awk '{print $2}')
declare file_name="$file_idx.txt"

# Increment the file name index value
echo "file: $(($file_idx+1))" > $mydir/.settings

#######################################################################################################################
# Function to check and format the $sched variable
#######################################################################################################################
valid_sched_format() {
    local sched="$1"
    local current_date
    current_date=$(date +"%Y-%m-%d")

    # Regular expression to match the required format
    if [[ "$sched" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2}|)( +[0-9]{2}:[0-9]{2}:[0-9]{2})$ ]]
    then
        # If the date part is missing, use the current date
        if [[ -z "${BASH_REMATCH[1]}" ]]
        then
            sched="$current_date${BASH_REMATCH[2]}"
        fi

        echo "$sched"
    else
        echo ""
    fi
}

#######################################################################################################################
#######################################################################################################################
# Execute the user's option
#######################################################################################################################
#######################################################################################################################
case "$option" in
    "start")
        touch /tmp/.mynotes.running
        python -u $HOME/bin/mynotes.py "$mydir" >> $log &
        ;;
    
    "stop")
        rm /tmp/.mynotes.running
        ;;
    
    *)
        if [ -f /tmp/.mynotes.running ]
        then
            sched=""
            text="$1"

            if [ -z "$2" ]
            then
                echo "Enter schedule (yyyy-mm-dd hh:mm:ss or hh:mm:ss)"
                read sched
            else
                sched="$2"
            fi

            # If it's a valid date, this function will echo it back or nother
            # If the date is missing, it will plug it in with the current one
            clean_sched=$(valid_sched_format "$sched")

            if [ ! -z "$clean_sched" ]
            then
                # Schedule work for the mynotes server
                printf "%s\n%s" "$clean_sched" "$text" > "$mydir/$file_name"
            else
                echo "ERROR: $sched is not in form yyyy-mm-dd hh:mm:ss or hh:mm:ss"
            fi
        else
            echo "ERROR: mynotes server not running"
        fi
esac
