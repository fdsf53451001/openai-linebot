# Chat Platform
## 功能
這是一個開放、可擴展的對話平台。

<img width="1223" alt="截圖 2023-05-01 下午11 25 32" src="https://user-images.githubusercontent.com/35889113/235476986-efbbcffd-68b9-4d0e-b0a3-d3fb6441cace.png">

除了整合對話平台常見的關鍵字、劇本模式功能，還加入了Regex、外掛程式的功能，可以快速套用各項專案。
並且可以串接openAI的gpt3.5, gpt4，達成智能對話功能。

## 可使用的LLM與工具
* OpenAI GPT3.5 / GPT4
* Flowise (串接Flowise作為對話後端)
* Grafana (用作分析使用)

## 目前已串接平台
* Line

## 通過docker-compose快速部署
```
docker build -t openai-linebot . -f ./docker/main/Dockerfile
docker build -t openai-linebot-grafana . -f ./docker/grafana/Dockerfile
docker-compose up --build
```

## 完整移除
```
docker-compose rm --volumes
```
