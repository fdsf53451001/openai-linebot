from Argument import Argument
import time

class MessageHandler:
    def __init__(self,db,chatgpt):
        self.db = db
        self.chatgpt = chatgpt
        self.argument = Argument()

    def handdle(self, user_id, receive_text, receive_timestamp):
        self.db.save_chat(user_id, receive_timestamp, 1, receive_text)

        reply_msg = None

        if self.argument.read_conf('function','default_reply') == 'true':
            reply_msg = self.argument.read_conf('function','default_reply_word')

        if self.argument.read_conf('function','keyword_reply') == 'true' and reply_msg == None:
            reply_msg = self.keyword_hold(receive_text)
            
        if self.argument.read_conf('function','chatgpt_reply') == 'true'  and reply_msg == None:
            reply_msg = self.chatgpt.get_response(user_id)
            if reply_msg != None:
                reply_msg = reply_msg.replace("AI:", "", 1)
            else:
                reply_msg = "RateLimitError!"

        if reply_msg == None:
            reply_msg = "所有對話引擎不可用，請檢查設定!"

        self.db.save_chat(user_id, int(time.time()*1000), 0, reply_msg)   
        return reply_msg
    
    def keyword_hold(self,receive_text):
        return self.db.search_keyword(receive_text)