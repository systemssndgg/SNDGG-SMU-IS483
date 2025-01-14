#!/bin/bash

# Navigate to your Docker Compose directory
cd /path/to/your/docker-compose-directory

# Stop the containers defined in 'orion.aio.yml'
docker-compose -f "/home/nathanaelsndgo/SNDGG-SMU-IS483/telegram-bot/context_broker/orion.aio.yml" down

# Remove unused volumes (optional, be careful if you have important data in volumes)
docker volume prune -f

# Rebuild and restart containers using 'orion.aio.yml'
docker-compose -f "/home/nathanaelsndgo/SNDGG-SMU-IS483/telegram-bot/context_broker/orion.aio.yml" up --build -d
