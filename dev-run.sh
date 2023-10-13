sudo docker-compose down
# git stash
# git pull
sudo docker build -t openai-linebot . -f ./docker/main/Dockerfile --no-cache
sudo docker build -t openai-linebot-grafana . -f ./docker/grafana/Dockerfile --no-cache
sudo docker-compose up -d