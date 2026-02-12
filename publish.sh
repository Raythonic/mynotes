#!/bin/bash
pip freeze > install/requirements.txt
publish "$1"
