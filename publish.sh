#!/bin/bash
cp src/mynotes.py $HOME/bin/.
cp src/mynotes.sh $HOME/bin/mynotes
cp src/google-calendar.py $HOME/bin/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/bin/mynotes.py
chmod +x $HOME/bin/google-calendar.py 
chmod +x $HOME/bin/mynotes
