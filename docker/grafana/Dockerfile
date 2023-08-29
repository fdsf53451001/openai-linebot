# 如何构建: docker build -t REPO/openai-linebot-grafana . -f ./docker/grafana/Dockerfile

FROM grafana/grafana-enterprise:9.5.5

VOLUME ["/opt/grafana"]

COPY --chown=472/472 --chmod=777 default/grafana.ini /etc/grafana/grafana.ini
COPY --chown=472/472 --chmod=777 default/grafana.db /var/lib/grafana/grafana.db

CMD ["grafana-server"]

EXPOSE 8080