from Argument import Argument
import threading
import time
import logging

class MessageHandler:
    def __init__(self,db,chatgpt):
        self.db = db
        self.chatgpt = chatgpt
        self.argument = Argument()

    def set_platform(self,platform):
        self.platform = platform

    def handdle(self, user_id, receive_text, receive_timestamp):
        receive_sentence_id = self.db.save_chat(user_id, receive_timestamp, 1, receive_text)

        reply_msg = None
        (reply_mode,reply_rule) = (0,None)  
        # 0=none, 1=default_reply, 2=keyword, 3=story, 4=chatgpt

        if self.argument.read_conf('function','default_reply') == 'true':
            reply_msg = self.argument.read_conf('function','default_reply_word')
            if reply_msg : reply_mode = 1

        if self.argument.read_conf('function','keyword_reply') == 'true' and reply_msg == None:
            reply_msg = self.keyword_hold(receive_text)
            if reply_msg : 
                reply_rule = reply_msg[1]
                reply_msg = reply_msg[0]
                reply_mode = 2
            
        if self.argument.read_conf('function','story_reply') == 'true' and reply_msg == None:
            (reply_rule, reply_msg) = self.story_hold(user_id,receive_text)
            if reply_msg : reply_mode = 3

        if self.argument.read_conf('function','chatgpt_reply') == 'true'  and reply_msg == None:
            result = []
            thread = threading.Thread(target=self.chatgpt_handler, args=(user_id,result))
            thread.start()

            s_time = time.time()
            timeout_warning = self.argument.read_conf('function','chatgpt_timeout_warning_sec')
            timeout_cut = self.argument.read_conf('function','chatgpt_timeout_cut_sec')
            while thread.is_alive() and time.time()-s_time < int(timeout_warning):
                pass    # waiting reply
            
            if thread.is_alive(): # send warning
                self.platform.send_to_user(user_id, "waiting reply...")
                logging.warning("OpenAI reply timeout for "+timeout_warning+" seconds!")
            
            while thread.is_alive() and time.time()-s_time < int(timeout_cut):
                pass    # waiting reply
            
            # stop waiting
            if not thread.is_alive() and result[0]:
                reply_msg = result[0]
                reply_msg = reply_msg.replace("AI:", "", 1)
            else:
                reply_msg = "OpenAI not responding !"
                logging.warning(reply_msg)

            reply_mode = 4

        if reply_msg == None:
            reply_msg = "所有對話引擎不可用，請檢查設定!"
            reply_mode = 0

        chatgpt_sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, reply_msg)  
        self.db.save_reply(chatgpt_sentence_id, reply_mode, reply_rule)
        return reply_msg
    
    def keyword_hold(self,receive_text):
        return self.db.search_keyword(receive_text)
    
    def story_hold(self, user_id, receive_text):
        # node type : 0=entry, 1=fork, 2=condiction, 3=response 
        last_reply_id = self.db.load_lest_reply_id(user_id)
        if last_reply_id:
            (reply_mode, reply_rule) = self.db.check_reply_mode(last_reply_id)
            if reply_mode == 3:
                continue_result = self.story_hold_continue(user_id, reply_rule, receive_text)
                if continue_result[0]:
                    return continue_result 
        return self.story_hold_first(user_id, receive_text)

    def story_hold_first(self, user_id, receive_text):
        # first using story, check all entry
        story_content = self.db.load_all_story()
        for story in story_content:
            if story[1] == 1: # enable
                if story[3] in receive_text:
                    return self.story_hold_continue(user_id, story[2], receive_text)
        # failed to match
        return (None,None)

    def story_hold_continue(self, user_id, last_reply_rule, receive_text):
        # continue using story, check next node
        next_sentences = self.db.load_next_sentence(last_reply_rule)
        if len(next_sentences)==0:
            return (None,None)
        for next_sentence in next_sentences:
            sentence = self.db.load_sentence(next_sentence[0])
            # node type : 1=fork, 2=condiction, 3=response
            if sentence[1]==1 or sentence[1]==3:
                return (sentence[0],sentence[2])
            elif sentence[1]==2:
                if sentence[3] in receive_text:
                    return self.story_hold_continue(user_id, sentence[0], receive_text)
        # failed to match
        self.platform.send_to_user(user_id, "無法繼續對話，將由OpenAI回覆")
        return (None,None)

    def chatgpt_handler(self, user_id, result):
        reply_msg = self.chatgpt.get_response(user_id)
        result.append(reply_msg)
