#!/bin/bash
source /home/rwalk/bin/bash_ext > /dev/null

# Update this app's version number in the mongodb database
load_project_config "MyNotes"

cp src/mynotes.py $HOME/services/.
cp src/mynotes.sh $HOME/services/mynotes
cp src/google-calendar.py $HOME/services/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/services/mynotes.py
chmod +x $HOME/services/google-calendar.py 
chmod +x $HOME/services/mynotes

# Place command in bin/
rm $HOME/bin/mynotes
ln -s $HOME/services/mynotes $HOME/bin/mynotes 
