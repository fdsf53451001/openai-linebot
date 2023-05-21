import tqdm

class ChatAnalyze:
    def __init__(self, db, chatgpt):
        self.db =db
        self.chatgpt = chatgpt

    def search_chat_session(self):
        chat_groups = self.db.load_chat_start_index_group_by_time_gap(300)
        for row in chat_groups:
            self.db.add_chat_session(row[0], row[1])

    def analyze_with_openai(self):
        emotions = ['快樂','驚訝','恐懼','厭惡','憤怒','悲傷']
        chat_sessions = self.db.load_chat_session_no_analyze()
        if not chat_sessions : return
        for chat_session in tqdm.tqdm(chat_sessions):
            data = self.db.load_chats_by_start_index_limit_time(chat_session[1], chat_session[2], 300)
            message_list = []
            message_list.append({'role':'user','content':'你是一個情緒分析專家，請問你認為以下對話情緒如何？請只要使用「快樂、驚訝、恐懼、厭惡、憤怒、悲傷」其中一個詞回答我，如果沒有情緒則輸出平淡，格式為<情緒>---'})
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
                    response_msg = '平淡'

                self.db.save_chat_analyze(chat_session[0], response_msg)

            # no response, leave the entry empty  
            
