import tqdm
import requests
import os
import json
import tqdm
import logging

class ChatAnalyze:
    def __init__(self, db, chatgpt, argument):
        self.db =db
        self.chatgpt = chatgpt
        self.argument = argument

    def search_chat_session(self):
        chat_groups = self.db.load_chat_start_index_group_by_time_gap(300)
        for row in chat_groups:
            self.db.add_chat_session(row[0], row[1])

    def analyze_with_openai(self):
        emotions = ['憤怒','厭惡','恐懼','愉快','悲傷','驚訝','羞恥','正常']
        chat_sesstion_time_gap =  int(self.argument.read_conf('sentiment_analysis','chat_session_time_gap'))

        chat_sessions = self.db.load_chat_session_no_analyze()
        if not chat_sessions : return
        for chat_session in tqdm.tqdm(chat_sessions,desc='Analyze Chat Session'):
            data = self.db.load_chats_by_start_index_limit_time(chat_session[1], chat_session[2], chat_sesstion_time_gap)
            message_list = []
            message_list.append({'role':'system','content':'你是一個情緒分析專家，請問你認為以下對話情緒如何？請只要使用「憤怒,厭惡,恐懼,愉快,悲傷,驚訝,羞恥,正常」其中一個詞回答我，如果沒有情緒則輸出正常，格式為<情緒> 喝奶茶真爽 快樂;明天竟然要補班 驚訝;走廊太暗好可怕 恐懼;最討厭馬路三寶了 厭惡;座我旁邊的人一直抄我答案，我要舉報他 憤怒;臨別的時刻，母親緊緊擁抱著兒子 悲傷;---'})
            for row in data:
                if row[0]==0:
                    role = 'assistant'
                else:
                    role = 'user'
                message_list.append({'role':role,'content':row[1]})
            message_list.append({'role':'user','content':'情緒是'})

            # print(message_list)
            response_msg = self.chatgpt.send_to_openai(message_list)
            if response_msg:
                for emotion in emotions:
                    if emotion in response_msg:
                        response_msg = emotion
                        break
                else:
                    response_msg = '正常'

                self.db.save_chat_analyze(chat_session[0], response_msg)

            # no response, leave the entry empty  
            
    @staticmethod
    def get_grafana_analyze_image(argument):
        urls = argument.read_conf('grafana','image_url')
        for i in tqdm.tqdm(range(int(argument.read_conf('grafana','image_amount'))),desc='Download Grafana Image'):
            r=requests.get(argument.read_conf('system','grafana_domain')+urls[i])
            if r.status_code != 200:
                logging.error('Grafana Image Download Failed !')
            with open('./static/grafana/'+str(i)+'.png','wb') as f:
                f.write(r.content)