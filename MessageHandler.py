import threading
import time
import re
import logging
import json
from typing import Tuple

from linebot.models import QuickReply
from linebot.models import QuickReplyButton
from linebot.models import MessageAction
from linebot.models.send_messages import TextSendMessage, ImageSendMessage, VideoSendMessage
from linebot.models.send_messages import SendMessage
from linebot.models.template import ButtonsTemplate, TemplateSendMessage, CarouselColumn, CarouselTemplate

from Argument import Argument
from ExternalCodeRunner import ExternalCodeRunner

class MessageHandler:
    def __init__(self,db,chatgpt):
        self.db = db
        self.chatgpt = chatgpt
        self.argument = Argument()
        self.platforms = {}
        self.extrunner = ExternalCodeRunner()

    def set_platform(self,platform_name,platform):
        self.platforms[platform_name] = platform

    def receive_request(self, platform_name, request):
        return self.platforms[platform_name].receive(request)

    def handdle(self, platform_name, user_id, receive_text, receive_timestamp):
        logging.info('receive from [%s] %s %s',platform_name,user_id,receive_text)
        self.db.save_chat(user_id, receive_timestamp, 1, receive_text)

        if not self.check_user(user_id, platform_name):
            return ('You are banned by admin!', None)

        reply_msg = None
        (reply_mode,reply_rule) = (0,None)  
        # 0=none, 1=default_reply, 2=keyword, 3=story, 4=chatgpt, 5=command

        reply_msg = self.check_restart_command(user_id, receive_text)
        if reply_msg : reply_mode = 5

        if self.argument.read_conf('function','default_reply') == 'true' and reply_msg == None:
            msg = self.argument.read_conf('function','default_reply_word')
            if msg: 
                reply_msg = TextSendMessage(text=msg)
                reply_mode = 1

        if self.argument.read_conf('function','keyword_reply') == 'true' and reply_msg == None:
            msg = self.keyword_hold(user_id, receive_text)
            if msg : 
                reply_rule = msg[0]
                reply_msg = msg[1]
                reply_mode = 2
            
        if self.argument.read_conf('function','story_reply') == 'true' and reply_msg == None:
            (reply_rule, msg) = self.story_hold(platform_name,user_id,receive_text)
            if msg : 
                reply_mode = 3
                if platform_name=='line': # only line platform support quick reply
                    quick_reply = self.story_generate_quick_reply(reply_rule)
                reply_msg = TextSendMessage(text=msg,quick_reply=quick_reply)

        reply_msg = self.check_rich_display(platform_name, user_id, reply_msg)

        if self.argument.read_conf('function','chatgpt_reply') == 'true' and reply_msg == None:
            reply_msg = self.chatgpt_hold(platform_name,user_id)
            reply_mode = 4

        if reply_msg == None:
            reply_msg = TextSendMessage(text="所有對話引擎不可用，請檢查設定!")
            reply_mode = 0
            logging.warning('no reply engine response!')


        logging.debug('reply to [%s] %s %s',platform_name,user_id,str(reply_msg))
        if reply_msg is TextSendMessage: # text message
            chatgpt_sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, reply_msg.text)
        else: # rich message
            chatgpt_sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, str(reply_msg))
        self.db.save_reply(chatgpt_sentence_id, reply_mode, reply_rule)
        return reply_msg

    # ? special command

    def check_restart_command(self, user_id, receive_text):
        if self.check_input_rule(user_id, '[Regex-(重新開始|重啟|[rR]estart)] ',receive_text):
            logging.info('user reset session : %s',user_id)
            t = str(time.time()*1000)
            for i in range(5//2):
                self.db.save_chat(user_id, t, 1, '')
                sid = self.db.save_chat(user_id, t, 0, '')
                self.db.save_reply(sid, 5, None)
            return TextSendMessage(text='OK')
        return None
    
    def check_user_variable(self, user_id, msg) -> str:
        command_content = self.fetch_command_content(msg,'LoadUserData')
        if command_content:
            user_value = self.db.load_user_extra_data(user_id,command_content[2])
            if user_value:
                return msg.replace(msg[command_content[0]:command_content[1]+1],user_value)
            else:
                return msg.replace(msg[command_content[0]:command_content[1]+1],'None')
        return msg

    def check_rich_display(self, platform_name, user_id, reply_msg) -> SendMessage:
        # TODO : 程式碼邏輯混亂，需要重構，避免不必要檢查
        if type(reply_msg) == TextSendMessage:
            reply_msg.text = self.extrunner.check_format(reply_msg.text, platform_name, user_id, self.send_to_user)

            reply_msg.text = self.check_user_variable(user_id, reply_msg.text)

        if type(reply_msg) == TextSendMessage:
            reply_msg = self.check_image_reply(reply_msg)

        if type(reply_msg) == TextSendMessage:
            reply_msg = self.check_video_reply(reply_msg)

        if type(reply_msg) == TextSendMessage:
            reply_msg = self.check_buttons_template_reply(reply_msg)

        if type(reply_msg) == TextSendMessage:
            reply_msg =  self.check_buttons_templates_reply(reply_msg)

        return reply_msg

    def check_image_reply(self, msg) -> SendMessage:
        command_content = self.fetch_command_content(msg.text,'LoadImage')
        if command_content:
            img_domain = self.argument.read_conf('system','system_domain')+'/api/image/'
            return ImageSendMessage(original_content_url = img_domain+msg.text[command_content[0]+11:command_content[1]],
                                    preview_image_url = img_domain+msg.text[command_content[0]+11:command_content[1]]
                                    )
        return msg

    def check_video_reply(self, msg) -> SendMessage:
        command_content = self.fetch_command_content(msg.text,'LoadVideo')
        if command_content:
            video_domain = self.argument.read_conf('system','system_domain')+'/api/video/'
            video_thumbnail_domain = self.argument.read_conf('system','system_domain')+'/api/video_thumbnail/'

            video_file_name = msg.text[command_content[0]+11:command_content[1]].split('.')[0]
            return VideoSendMessage(original_content_url = video_domain+msg.text[command_content[0]+11:command_content[1]],
                                    preview_image_url = video_thumbnail_domain + video_file_name + '.jpg'
                                    )
        return msg

    def check_input_rule(self, user_id, rule, receive_text):
        match = False
        
        command_content = self.fetch_command_content(rule,'Regex')
        if command_content: # match regex
            regex = re.compile(command_content[2])
            match = regex.search(receive_text)
            if not match : return False
        
        command_content = self.fetch_command_content(rule,'SaveUserData')
        if command_content: # match save data
            self.db.add_user_extra_data(user_id, command_content[2], receive_text)
            match = True

        if rule in receive_text: # match word
            match = True
            return match
        
        return match

    # ? reply engine

    def keyword_hold(self, user_id, receive_text):
        # return self.db.search_keyword(receive_text)
        keywords = self.db.load_keyword()
        for keyword_row in keywords:
            if not keyword_row[1]: continue
            if self.check_input_rule(user_id, keyword_row[2], receive_text):
                return (keyword_row[0],TextSendMessage(text=keyword_row[3]))
        return None
    
    def story_hold(self, platform_name, user_id, receive_text):
        # node type : 0=entry, 1=fork, 2=condiction, 3=response 
        last_reply_id = self.db.load_lest_reply_id(user_id)
        if last_reply_id:
            (reply_mode, reply_rule) = self.db.check_reply_mode(last_reply_id)
            if reply_mode == 3:
                continue_result = self.story_hold_continue(platform_name,user_id, reply_rule, receive_text)
                if continue_result[0]:
                    return continue_result 
        return self.story_hold_first(platform_name, user_id, receive_text)

    def story_hold_first(self, platform_name, user_id, receive_text):
        # first using story, check all entry
        story_content = self.db.load_all_story()
        for story in story_content:
            if story[1] == 1: # enable
                if self.check_input_rule(user_id, story[3], receive_text):
                    return self.story_hold_continue(platform_name, user_id, story[2], receive_text)
        # failed to match
        return (None,None)

    def story_hold_continue(self, platform_name, user_id, last_reply_rule, receive_text):
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
                if self.check_input_rule(user_id, sentence[2], receive_text):
                    return self.story_hold_continue(platform_name,user_id, sentence[0], receive_text)
        # failed to match
        self.send_to_user(platform_name, user_id, "無法繼續對話，將由OpenAI回覆")
        return (None,None)

    def story_generate_quick_reply(self, reply_rule):
        next_sentences = self.db.load_next_sentence(reply_rule)
        quick_reply = []
        for sentene in next_sentences:
            sentence_content = self.db.load_sentence(sentene[0])
            message = sentence_content[2]
            if message and (not self.fetch_command_content(message,'Regex')) and (not self.fetch_command_content(message,'SaveUserData')): # pass regex
                quick_reply.append(QuickReplyButton(action=MessageAction(label=message, text=message)))
        return QuickReply(items=quick_reply) if quick_reply else None

    def check_buttons_template_reply(self, reply_msg) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'ButtonsTemplate')
        if command_content:
            buttons_template_array = json.loads(command_content[2])
            buttons_template = self.generate_button_template(buttons_template_array,ButtonsTemplate)
            return TemplateSendMessage(alt_text=buttons_template_array['title'], template=buttons_template)
        return reply_msg

    def check_buttons_templates_reply(self, reply_msg) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'ButtonsTemplates')
        if command_content:
            buttons_template_arrays = json.loads(command_content[2])
            buttons_templates = []
            for buttons_template_array in buttons_template_arrays:
                buttons_templates.append(self.generate_button_template(buttons_template_array,CarouselColumn))
            return TemplateSendMessage(alt_text=buttons_template_arrays[0]['title'], template=CarouselTemplate(columns=buttons_templates))
        return reply_msg

    def generate_button_template(self, buttons_template_array, T):
        # return ButtonsTemplate or CarouselColumn according to T
        actions = []
        if 'action1' in buttons_template_array:
            actions.append(MessageAction(label=buttons_template_array['action1'], text=buttons_template_array['action1']))
        if 'action2' in buttons_template_array:
            actions.append(MessageAction(label=buttons_template_array['action2'], text=buttons_template_array['action2']))
        if 'action3' in buttons_template_array:
            actions.append(MessageAction(label=buttons_template_array['action3'], text=buttons_template_array['action3']))
        actions = None if not actions else actions

        img_domain = self.argument.read_conf('system','system_domain')+'/api/image/'

        buttons_template = T(
            title = buttons_template_array['title'],
            text = buttons_template_array['text'],
            thumbnail_image_url = img_domain+buttons_template_array['img'],
            actions = actions
        )
        return buttons_template

    def chatgpt_hold(self, platform_name, user_id):
        result = []
        thread = threading.Thread(target=self.chatgpt_handler, args=(platform_name,user_id,result))
        thread.start()

        s_time = time.time()
        timeout_warning = self.argument.read_conf('openai','openai_timeout_warning_sec')
        timeout_cut = self.argument.read_conf('openai','openai_timeout_cut_sec')
        while thread.is_alive() and time.time()-s_time < int(timeout_warning):
            pass    # waiting reply
        
        if thread.is_alive() and self.argument.read_conf('openai','openai_warning_message'): # send warning
            self.send_to_user(platform_name, user_id, "等待回應中...")
            logging.warning("OpenAI reply timeout for "+timeout_warning+" seconds!")
        
        while thread.is_alive() and time.time()-s_time < int(timeout_cut):
            pass    # waiting reply
        
        # stop waiting
        if not thread.is_alive() and result[0]:
            reply_msg = result[0]
            reply_msg = reply_msg.replace("AI:", "", 1)
        else:
            reply_msg = "OpenAI 沒有回應或花費太久，請稍候再嘗試！"
            # self.send_to_user(platform_name, user_id, reply_msg)
            logging.warning(reply_msg)
    
        return TextSendMessage(text=reply_msg)

    def chatgpt_handler(self, platform_name, user_id, result):
        reply_msg = self.chatgpt.get_response(user_id)
        result.append(reply_msg)

    # ? other utility

    def fetch_command_content(self, text, command) -> Tuple[int,int,str]:
        if text and '['+command+'-' in text:
            try:
                s_index = text.index('['+command+'-')
                e_index = text.index('] ',s_index)
                command_content = text[s_index+len(command)+2:e_index]
                return (s_index, e_index, command_content)
            except ValueError:
                logging.error('command格式錯誤! 請檢查格式正確，或是結尾是否有空格。 '+text)
        return None

    def send_to_user(self, platform_name, user_id, msg):
        # this function for alarm purpose only
        # won't save to database
        logging.debug('send to [%s] %s %s',platform_name,user_id,msg)

        if platform_name=='command_line':
            return
        
        if not (self.argument.read_conf('function','send_alarm_msg')=='true'):
            return
        
        self.platforms[platform_name].send_to_user(user_id, msg)

    def check_user(self, user_id, platform_name):
        user_profile = self.db.check_user(user_id)
        if not user_profile: # user not exist
            threading.Thread(target=self.add_user, args=(user_id, platform_name)).start()
        elif user_profile[0][2]==1: # user is banned
            logging.warning('banned user detect : %s',user_id)
            return False    
        elif user_profile[0][1]==None: # user have no profile
            threading.Thread(target=self.update_user, args=(user_id, platform_name)).start()
        return True

    def add_user(self, user_id, platform_name):
        profile = self.platforms[platform_name].get_user_profile(user_id)
        if profile:
            t = str(time.time()*1000)
            self.db.add_new_user(user_id, platform_name, profile[0], profile[1], t)
        else:
            self.db.add_new_user_no_profile(user_id, platform_name)
        logging.info('new user detect : %s',user_id)

    def update_user(self, user_id, platform_name):
        logging.warn('user with no profile detect : %s',user_id)
        profile = self.platforms[platform_name].get_user_profile(user_id)
        if profile:
            t = str(time.time()*1000)
            self.db.update_user_profile(user_id, profile[0], profile[1], t)