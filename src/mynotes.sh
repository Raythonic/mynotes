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
declare server_running="/tmp/.mynotes.running"

export MONGODB="mongodb://localhost:27017/"

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
    if [[ "$sched" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})?\ ?([0-9]{2}:[0-9]{2}:[0-9]{2})?$ ]]
    then
        # If the date part is missing, use the current date
        if [[ -z "${BASH_REMATCH[1]}" ]]
        then
            sched="$current_date ${BASH_REMATCH[2]}"
        fi

        if [[ -z "${BASH_REMATCH[2]}" ]]
        then
            sched="${BASH_REMATCH[1]} 00:00:00"
        fi

        echo "$sched"
        return
    fi

    echo ""

}

start_server ()
{
    if [ ! -f $server_running ]
    then
        touch $server_running
        $HOME/bin/mynotes.py $mydir >> $log &
        echo "mynotes server started"
    else
        echo "mynotes server is already running"
    fi
}

stop_server ()
{
    if [ -f $server_running ]
    then
        rm $server_running
        echo "mynotes server stopped"
    else
        echo "mynotes server not running"
    fi
}

show_notes ()
{
    echo "show" > $mydir/command
    echo "See output in $HOME/logs/mynotes.log"
}

cancel_note ()
{
    local name="$1"

    if [ $(echo "$name" | grep -c -E "^[0-9]+$") -gt 0 ]
    then 
        echo "cancel:$name" > $mydir/command
        echo "See output in $HOME/logs/mynotes.log"
    else
        echo "$name is not a proper numercial name,"
        echo "assigned when the note was submitted via:"
        echo "        mynotes note"
    fi
}

schedule_note ()
{
    text="$1"
    sched="$2"

    if [ -z "$sched" ]
    then
        echo "Enter schedule (yyyy-mm-dd hh:mm:ss, hh:mm:ss, or Enter for immediate)"
        read sched
    fi

    if [ -z "$sched" ] || [ "$sched" == "now" ]
    then 
        sched="1970-01-01 00:00:00"
    fi

    # If it's a valid date, this function will echo it back or nother
    # If the date is missing, it will plug it in with the current one
    clean_sched=$(valid_sched_format "$sched")

    if [ ! -z "$clean_sched" ]
    then
        # Schedule work for the mynotes server
        printf "%s %s" "$clean_sched" "$text" > "$mydir/$file_name"
    else
        echo "ERROR: $sched is not in form yyyy-mm-dd hh:mm:ss or hh:mm:ss"
    fi
}

#######################################################################################################################
#######################################################################################################################
# Execute the user's option
#######################################################################################################################
#######################################################################################################################
case "$option" in
    "start")
        start_server
        ;;
    
    "stop")
        stop_server
        ;;
    
    "restart")
        stop_server
        start_server
        ;;

    "status")
        if [ -f $server_running ]
        then 
            echo "mynotes server is running"
        else
            echo "mynotes server is not running"
        fi
        ;;

    "show")
        show_notes
        ;;

    "cancel")
        cancel_note "$2"
        ;;
    
    *)
        if [ -f $server_running ]
        then
            schedule_note "$1" "$2"
        else
            echo "ERROR: mynotes server not running"
        fi
        ;;
esac
