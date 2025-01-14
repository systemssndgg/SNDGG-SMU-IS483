#!/bin/bash

# Clean up Docker
/home/nathanaelsndgo/SNDGG-SMU-IS483/telegram-bot/context_broker/docker_cleanup.sh

# Kill any existing instance of main.py
pkill -u root -f python

echo "Sleep to give time for docker to boot"
sleep 30
echo "Start python"

# Start the script with the correct Python interpreter
/home/nathanaelsndgo/SNDGG-SMU-IS483/telegram-bot/mvenv/bin/python /home/nathanaelsndgo/SNDGG-SMU-IS483/telegram-bot/main.py
