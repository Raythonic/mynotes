#!/bin/bash
source /home/rwalk/bin/bash_ext > /dev/null

# Update this app's version number in the mongodb database
increment_app_version "MyNotes"

cp src/mynotes.py $HOME/services/.
cp src/mynotes.sh $HOME/services/mynotes
cp src/google-calendar.py $HOME/services/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/services/mynotes.py
chmod +x $HOME/services/google-calendar.py 
chmod +x $HOME/services/mynotes
