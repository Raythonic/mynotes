#!/bin/bash
cp src/mynotes.py $HOME/bin/.
cp src/mynotes.sh $HOME/bin/mynotes
cp src/google-calendar.py $HOME/bin/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/bin/mynotes.py
chmod +x $HOME/bin/mynotes


if [ $($HOME/bin/mynotes status | grep -v "not running" | wc -l) -eq 0 ]
then
    echo "Starting mynotes server"
    $HOME/bin/mynotes start
else
    echo "Restarting mynotes server"
    $HOME/bin/mynotes restart
fi