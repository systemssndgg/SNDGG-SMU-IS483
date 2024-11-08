@echo off
echo Running Docker Compose...
docker-compose -f grafana.yml -p grafana-project up --build
pause
