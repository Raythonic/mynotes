#!/bin/bash

if [ ! -d $HOME/mynotes ]
then
    mkdir $HOME/mynotes
    echo "file: 1" > $HOME/mynotes/.settings
fi

declare option="$1"
declare -i file_idx=$(grep "^file: " $HOME/mynotes/.settings | awk '{print $2}')
declare file_name="$file_idx.txt"


((file_idx=$file_idx+1))
echo "file: $file_idx" > $HOME/mynotes/.settings

case "$option" in
    "start")
        touch /tmp/.mynotes.running
        $HOME/bin/mynotes.py
        ;;
    
    "stop")
        rm /tmp/.mynotes.running"
        ;;
    
    *)
        echo "$option" > $HOME/mynotes/$file_name