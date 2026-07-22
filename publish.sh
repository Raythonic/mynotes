#!/bin/bash
pip freeze > install/requirements.txt
bash scripts/load-mynotes-manpages.sh
publish "$1"
