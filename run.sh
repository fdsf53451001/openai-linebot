sudo docker-compose down
# git stash
git pull
sudo docker build -t openai-linebot . -f ./docker/main/Dockerfile
sudo docker build -t openai-linebot-grafana . -f ./docker/grafana/Dockerfile
sudo docker-compose up -d