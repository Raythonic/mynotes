#!/bin/bash

#######################################################################################################################
# This script is a controlling script for the mynotes.py server.  With this script you can:
#   1. start the mynotes server: mynotes start
#   2. stop the mynotes server: mynote stop
#   3. schedule a note with the mynotes server: mynote "text..."
#######################################################################################################################

[ -z "$1" ] && echo "Usage: mynotes [start|stop|text]" && exit 0

source /home/rwalk/bin/bash_ext > /dev/null
declare mydir="$HOME/mynotes"
declare app_name="MyNotes"

# Load this app's config parameters into env variables
export_myconfig $app_name

export MYNOTES_RUNNING="/tmp/.mynotes.running"
export GOOGLE_CREDENTIALS="$HOME/sensitive/google-api-credentials.json"

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

#######################################################################################################################
# Start the mynotes server
#######################################################################################################################
start_server ()
{
    if [ ! -f $MYNOTES_RUNNING ]
    then
        # Spawn the process and capture its PID immediately
        (
            echo $$ > $MYNOTES_RUNNING # Write PID of this subshell
            chown rwalk:rwalk $MYNOTES_RUNNING
            local version=$(get_version "$app_name")
            local dat=$(date +"%Y-%m-%d %H:%M:%S")
            local path=$(realpath "$0")
            local header=$(form_header "$app_name" "$version")

            echo "$header"  >> $log_file

            /home/rwalk/services/mynotes.py "$mydir" "$log_file"
        ) &

        #start_google_polling
        echo "$app_name server started"
    else
        echo "$app_name server is already running"
    fi
}


#######################################################################################################################
# Stop the mynotes server
#######################################################################################################################
stop_server ()
{
    if [ -f $MYNOTES_RUNNING ]
    then
        rm $MYNOTES_RUNNING
        local dat=$(date +"%Y-%m-%d %H:%M:%S")
        local path=$(realpath "$0")
        local trailer=$(form_trailer "$app_name" "$version")

        echo "$trailer"  >> $log_file

        echo "MyNotes server and google monitoring stopped"
    else
        echo "mynotes server not running"
    fi
}


#######################################################################################################################
# Start google polling
#######################################################################################################################
start_google_polling ()
{
    if [ -z $GOOGLE_POLLING ]
    then
        $HOME/services/google-calendar.py >> $log_file &
    else
        echo "google polling already running"
    fi
}


#######################################################################################################################
# Dump the notes database
#######################################################################################################################
show_notes ()
{
    echo "show" > $mydir/command
}

#######################################################################################################################
# Dump the notes database
#######################################################################################################################
dump_notes ()
{
    echo "dump" > $mydir/command
}

#######################################################################################################################
# Cancel the timers of a note
#######################################################################################################################
cancel_note ()
{
    local name="$1"

    echo "cancel:$name" > $mydir/command
}

#######################################################################################################################
# Purge database
#######################################################################################################################
purge_database ()
{
    echo "purge" > $mydir/command
}

#######################################################################################################################
# Schedule a note
#######################################################################################################################
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
        echo "[ERROR] $sched is not in form yyyy-mm-dd hh:mm:ss or hh:mm:ss"
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
    
    "start-google")
        start_google_polling
        ;;
    
    "stop")
        stop_server
        ;;
    
    "restart")
        stop_server
        sleep 3
        start_server
        ;;

    "status")
        if [ -f $MYNOTES_RUNNING ]
        then 
            echo "mynotes server is running"
        else
            echo "mynotes server is not running"
        fi
        ;;

    "check")
        if [ -f $MYNOTES_RUNNING ]
        then 
            echo 1
        else
            echo 0
        fi
        ;;

    "show")
        show_notes
        ;;

    "cancel")
        cancel_note "$2"
        ;;

    "purge")
        purge_database
        ;;
    
    *)
        if [ -f $MYNOTES_RUNNING ]
        then
            schedule_note "$1" "$2"
        else
            echo "[ERROR] mynotes server not running"
        fi
        ;;
esac
