#!/bin/bash

[ -z "$1" ] && echo "Usage: mynotes [start|stop|text]" && exit 0

declare mydir="$HOME/mynotes"
declare log="$HOME/logs/mynotes.log"

if [ ! -d $HOME/mynotes ]
then
    mkdir $HOME/mynotes
    echo "file: 1" > $mydir/.settings
fi


declare option="$1"
declare -i file_idx=$(grep "^file: " .settings | awk '{print $2}')
declare file_name="$file_idx.txt"

echo "file: $(($file_idx+1))" > $mydir/.settings

# Function to check and format the $sched variable
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

case "$option" in
    "start")
        touch /tmp/.mynotes.running
        $HOME/bin/mynotes.py "$mydir" >> $log
        ;;
    
    "stop")
        rm /tmp/.mynotes.running
        ;;
    
    *)
        sched=""
        text="$1"

        if [ -z "$2" ]
        then
            echo "Enter schedule (yyyy-mm-dd hh:mm:ss or hh:mm:ss)"
            read sched
        else
            sched="$2"
        fi

        clean_sched=$(valid_sched_format "$sched")

        if [ ! -z "$clean_sched" ]
        then
            printf "%s\n%s" "$clean_sched" "$text" > "$mydir/$file_name"
        else
            echo "ERROR: $sched is not in form yyyy-mm-dd hh:mm:ss or hh:mm:ss"
        fi
        ;;

esac
