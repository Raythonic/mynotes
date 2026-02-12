#!/bin/bash
pip freeze > requirements.txt
publish "$1"
