# 如何构建: docker build -t REPO/openai-linebot .
# 如何提交: docker push REPO/openai-linebot
# 如何运行: docker create -it --net=host --restart always REPO/openai-linebot

FROM python:3.11

VOLUME ["/bot/data"]
WORKDIR /bot

COPY ../.. .

RUN pip3 install -r requirements.txt

RUN python3 setup.py

# RUN apt install -y apt-transport-https software-properties-common && \
#     wget -q -O /usr/share/keyrings/grafana.key https://packages.grafana.com/gpg.key && \
#     echo "deb [signed-by=/usr/share/keyrings/grafana.key] https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list && \
#     apt-get update && \
#     apt-get install grafana

# https://mileslin.github.io/2019/12/%E4%BD%BF%E7%94%A8-docker-compose-%E5%BB%BA%E7%AB%8B%E5%A4%9A%E5%80%8B%E6%9C%8D%E5%8B%99/

CMD ["python3", "-u", "index.py"]

EXPOSE 80