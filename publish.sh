#!/bin/bash

build_version=$(cat build-version.txt)

# Split the version string into an array
IFS='.' read -r -a version_parts <<< "$build_version"

# Add 1 to the last part (patch version)
((version_parts[2]++))

# Join the version parts back together
new_version="${version_parts[0]}.${version_parts[1]}.${version_parts[2]}"

echo "$new_version" > build-version.txt

# Update this app's version number in the mongodb database
/home/rwalk/bin/update-myconfig.sh "MyNotes" "version" "$new_version"

cp src/mynotes.py $HOME/services/.
cp src/mynotes.sh $HOME/services/mynotes
cp src/google-calendar.py $HOME/services/.
cp google-api/*.json $HOME/sensitive/.

chmod +x $HOME/services/mynotes.py
chmod +x $HOME/services/google-calendar.py 
chmod +x $HOME/services/mynotes
