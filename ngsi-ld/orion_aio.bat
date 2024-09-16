@echo off
echo Running Docker Compose...
docker-compose -f orion.aio.yml up --build
pause
