#!/bin/bash
cp src/mynotes.py $HOME/services/.
cp src/mynotes.sh $HOME/services/mynotes
cp src/google-calendar.py $HOME/services/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/services/mynotes.py
chmod +x $HOME/services/google-calendar.py 
chmod +x $HOME/services/mynotes
