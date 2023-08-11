docker-compose down
# git stash
git pull
docker build -t openai-linebot . -f ./docker/main/Dockerfile
docker build -t openai-linebot-grafana . -f ./docker/grafana/Dockerfile
docker-compose up -d