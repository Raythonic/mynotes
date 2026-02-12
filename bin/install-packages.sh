#!/bin/bash

if [ ! -f requirements.txt ]
then
    echo "requirements.txt file not found."
    exit 1
fi

pip install -r requirements.txt