import threading
import time
import re
import logging
import json
from typing import Tuple

from service.llm.Flowise import Flowise

from linebot.models import QuickReply
from linebot.models import QuickReplyButton
from linebot.models import MessageAction
from linebot.models.send_messages import TextSendMessage, ImageSendMessage, VideoSendMessage
from linebot.models.send_messages import SendMessage
from linebot.models.template import ButtonsTemplate, TemplateSendMessage, CarouselColumn, CarouselTemplate

from Argument import Argument
from ExternalCodeRunner import ExternalCodeRunner

class ReplyMessage:
    def __init__(self, finish:bool, reply_mode:int=None, reply_text:SendMessage=None, reply_rule:int=None):
        self.finish = finish
        self.reply_mode = reply_mode
        self.reply_text = reply_text
        self.reply_rule = reply_rule

class MessageHandler:
    def __init__(self,db,chatgpt):
        self.db = db
        self.chatgpt = chatgpt
        self.argument = Argument()
        self.platforms = {}
        self.extrunner = ExternalCodeRunner()
        self.flowise = Flowise(self.db, self.argument)

    def set_platform(self,platform_name,platform):
        self.platforms[platform_name] = platform

    def receive_request(self, platform_name, request):
        return self.platforms[platform_name].receive(request)

    def handdle(self, platform_name, user_id, receive_text, receive_timestamp):
        logging.info('receive from [%s] %s %s',platform_name,user_id,receive_text)
        self.db.save_chat(user_id, receive_timestamp, 1, receive_text)

        if not self.check_user(user_id, platform_name):
            return ('You are banned by admin!', None)

        rm = ReplyMessage(False) 
        reply_engine = self.get_reply_engine()
        for engine in reply_engine:
            rm = engine(platform_name, user_id, receive_text)
            if rm.finish:
                break
        
        msg = None
        if isinstance(rm.reply_text, TextSendMessage): # text message
            msg = rm.reply_text.text
            chatgpt_sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, rm.reply_text.text)
        else: # other rich message
            msg = str(rm.reply_text)
            chatgpt_sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, str(rm.reply_text))
        logging.info('reply to [%s] %s %s',platform_name,user_id,msg)
        self.db.save_reply(chatgpt_sentence_id, rm.reply_mode, rm.reply_rule)
        return rm.reply_text

    # ? special command

    def check_restart_command(self,platform_name, user_id, receive_text):
        if self.check_input_rule(platform_name, user_id, ['[Regex-(重新開始|重啟|[rR]estart)] '],receive_text) != -1:
            logging.info('user reset session : %s',user_id)
            t = str(time.time()*1000)
            for i in range(5//2):
                self.db.save_chat(user_id, t, 1, '')
                sid = self.db.save_chat(user_id, t, 0, '')
                self.db.save_reply(sid, 5, None)
            msg = TextSendMessage(text='OK')
            return ReplyMessage(True, 5, msg)
        return ReplyMessage(False)
    
    def check_default_reply(self, platform_name, user_id, receive_text):
        msg = self.argument.read_conf('function','default_reply_word')
        if msg: 
            msg = TextSendMessage(text=msg)
            return ReplyMessage(True, 1, msg)
        return ReplyMessage(False)

    def check_user_variable(self, user_id, msg) -> str:
        '''
        load user variable
        if request variable is UUID, then return UUID directly
        '''
        command_content = self.fetch_command_content(msg,'LoadUserData')
        if command_content:
            # get value
            user_value = self.db.load_user_extra_data(user_id,command_content[2])
            if command_content[2] == 'UUID':
                user_value = user_id

            if user_value:
                return msg.replace(msg[command_content[0]:command_content[1]+1],user_value)
            else:
                return msg.replace(msg[command_content[0]:command_content[1]+1],'None')
        return msg

    def story_add_quick_reply(self, reply_message:ReplyMessage):
        if not reply_message.finish:
            return reply_message
        
        reply_rule = reply_message.reply_rule
        next_sentences = self.db.load_next_sentence(reply_rule)
        quick_reply = []
        for sentene in next_sentences:
            sentence_content = self.db.load_sentence(sentene[0])
            message = sentence_content[2]
            if message and (not self.fetch_command_content(message,'Regex')) and (not self.fetch_command_content(message,'SaveUserData')): # pass regex
                quick_reply.append(QuickReplyButton(action=MessageAction(label=message, text=message)))
        
        if quick_reply:
            reply_message.reply_text.quick_reply = QuickReply(items=quick_reply)
        
        return reply_message

    def check_input_rule(self, platform_name:str, user_id:str, rules:list, receive_text:str) -> int:
        '''
        rule : rule set up by web admin to check this receive_text
        receive_text : input from normal user
        '''
        
        # check text match first
        match_index = self._check_input_rule_textonly(rules, receive_text)
        if match_index != -1:
            return match_index

        # no text match
        match = False
        # notice : an input message can triger multiple rule at the same time

        for i,rule in enumerate(rules):
            command_content = self.fetch_command_content(rule,'Regex')
            if command_content: # match regex
                regex = re.compile(command_content[2])
                match = regex.search(receive_text)
                if not match : continue
            
            command_content = self.fetch_command_content(rule,'SaveUserData')
            if command_content: # match save data
                self.db.add_user_extra_data(user_id, command_content[2], receive_text)
                match = True

            command_content = self.fetch_command_content(rule,'SetUserData')
            if command_content: # match save data
                try:
                    input_variable = command_content[2].split('=')[0]
                    input_value = command_content[2].split('=')[1]
                except:
                    logging.error('Error Format in SetUserData : '+command_content[2])
    
                if not self.check_user_special_variable(platform_name, user_id, input_variable, input_value):
                    # not special variable, save to user data
                    self.db.add_user_extra_data(user_id, input_variable, input_value)

                match = True


            if match:
                return i

        # all rule failed to match
        return -1

    def _check_input_rule_textonly(self, rules:list, receive_text:str) -> int:
        '''
        args:
            rules : list of rule
            receive_text : input from normal user
        return:
            int : index of rule that match max words in receive_text
        '''
        (max_match_index, max_match_len) = (-1, 0)
        for i,rule in enumerate(rules):
            if len(rule)>max_match_len and rule in receive_text:
                (max_match_index, max_match_len) = (i, len(rule))
        return max_match_index
    
    def check_user_special_variable(self, platform_name, user_id, variable, value) -> bool:
        '''
        This function used to detect special user variable.
        when this kind of variable change, system will take some action.        
        ex.
        RichMenuID : use to change some user's rich menu

        return:
            bool : if this variable is special variable
        '''
        if variable == 'RichMenuID':
            richmenu_id = self.argument.read_conf('line','richmenu_id_'+str(value))
            if richmenu_id:
                self.platforms[platform_name].set_richmenu_for_user(user_id, richmenu_id)
            else:
                logging.error('Try to load RichMenu not found : '+str(value))

        elif variable == 'Tag':
            if value != '':
                self.db.add_user_extra_tag(user_id, value)       
        else:
            return False
    
        return True
        

    # ? reply engine

    def get_reply_engine(self):
        reply_engine = []
        # 0=none, 1=default_reply, 2=keyword, 3=story, 4=chatgpt, 5=command, 6=flowise

        reply_engine.append(self.check_restart_command)

        if self.argument.read_conf('function','default_reply'):
            reply_engine.append(self.check_default_reply)

        if self.argument.read_conf('function','keyword_reply'):
            reply_engine.append(self.keyword_hold)
                     
        if self.argument.read_conf('function','story_reply'):
            reply_engine.append(self.story_hold)  

        if self.argument.read_conf('function','flowise_reply'):
            reply_engine.append(self.flowise_hold)

        if self.argument.read_conf('function','chatgpt_reply'):
            reply_engine.append(self.chatgpt_hold)

        reply_engine.append(self.fallback_reply)

        return reply_engine

    def fallback_reply(self, platform_name, user_id, receive_text):
        msg = TextSendMessage(text="所有對話引擎不可用，請檢查設定!")
        rm = ReplyMessage(True, 0, msg)
        logging.warning('no reply engine response!')
        return rm

    def keyword_hold(self,platform_name, user_id, receive_text):
        # return self.db.search_keyword(receive_text)
        keywords = self.db.load_keyword()
        for keyword_row in keywords:
            if not keyword_row[1]: 
                keywords.remove(keyword_row) # remove disabled keyword

        match_index = self.check_input_rule(platform_name, user_id, [keyword_row[2] for keyword_row in keywords], receive_text)
        if match_index != -1:
            msg = TextSendMessage(text=keywords[match_index][3])
            msg = self.check_rich_display(platform_name, user_id, msg)
            return ReplyMessage(True, 2, msg, keywords[match_index][0])
        
        return ReplyMessage(False)
    
    def story_hold(self, platform_name, user_id, receive_text):

        last_reply_id = self.db.load_last_reply_id(user_id)
        if last_reply_id:
            (reply_mode, reply_rule) = self.db.check_reply_mode(last_reply_id)
            # node type : 0=entry, 1=fork, 2=condiction, 3=response 
            if reply_mode == 3:
                rm = self.story_hold_continue(platform_name,user_id, reply_rule, receive_text)
                if rm.finish:
                    rm.reply_text = self.check_rich_display(platform_name, user_id, rm.reply_text)
                    rm = self.story_add_quick_reply(rm)
                return rm

        rm = self.story_hold_first(platform_name, user_id, receive_text)
        if rm.finish:
            rm.reply_text = self.check_rich_display(platform_name, user_id, rm.reply_text)
            rm = self.story_add_quick_reply(rm)
        return rm

    def story_hold_first(self, platform_name, user_id, receive_text):
        # first using story, check all entry
        story_content = self.db.load_all_story()
        for story in story_content:
            if story[1] != 1: # enable
                story_content.remove(story) # remove disabled story
        match_index = self.check_input_rule(platform_name, user_id, [story[3] for story in story_content], receive_text)
        if match_index != -1:
            return self.story_hold_continue(platform_name, user_id, story_content[match_index][2], receive_text)
        
        # failed to match
        return ReplyMessage(False)

    def story_hold_continue(self, platform_name, user_id, last_reply_rule, receive_text):
        # continue using story, check next node
        next_sentences = self.db.load_next_sentence(last_reply_rule)
        if len(next_sentences)==0:
            return self.story_hold_first(platform_name, user_id, receive_text)
        
        # if next row is fork, or response, output directly
        first_next_sentence = next_sentences[0]
        sentence = self.db.load_sentence(first_next_sentence[0])
        if sentence[1]==1 or sentence[1]==3:
            msg = TextSendMessage(text=sentence[2])
            return ReplyMessage(True, 3, msg, first_next_sentence[0])

        # if next row is condiction, check all rule for maximum words match
        sentences = []
        for next_sentence in next_sentences:
            sentence = self.db.load_sentence(next_sentence[0])
            # node type : 1=fork, 2=condiction, 3=response
            sentences.append(sentence)
               
        match_index = self.check_input_rule(platform_name, user_id, [sentence[2] for sentence in sentences], receive_text)
        if match_index != -1:
            return self.story_hold_continue(platform_name,user_id, sentences[match_index][0], receive_text)
        
        # failed to match
        self.send_to_user(platform_name, user_id, "以下由人工智能對話")
        return ReplyMessage(False)

    def chatgpt_hold(self, platform_name, user_id, receive_text) -> TextSendMessage:
        timeout_config = {
            'timeout_warning_sec' : self.argument.read_conf('openai','openai_timeout_warning_sec'),
            'timeout_cut_sec' : self.argument.read_conf('openai','openai_timeout_cut_sec'),
            'enable_warning_message' : self.argument.read_conf('openai','openai_warning_message')
        }
        text_send_message = self._llm_hold(platform_name, user_id, self._chatgpt_handler, 'OpenAI', timeout_config)
        text_send_message.text = text_send_message.text.replace("AI:", "", 1)
        return ReplyMessage(True, 4, text_send_message)

    def flowise_hold(self, platform_name, user_id, receive_text) -> TextSendMessage:
        timeout_config = {
            'timeout_warning_sec' : self.argument.read_conf('openai','10'),
            'timeout_cut_sec' : self.argument.read_conf('openai','20'),
            'enable_warning_message' : self.argument.read_conf('openai','openai_warning_message')
        }
        text_send_message = self._llm_hold(platform_name, user_id, self._flowuse_handler, 'Flowise', timeout_config)
        return ReplyMessage(True, 6, text_send_message)

    def _llm_hold(self, platform_name, user_id, handler_function, handler_name:str, timeout_config:dict) -> TextSendMessage:
        """Generate response from handler_function, and return TextSendMessage.
        handler_function is a function that call LLM such as chatgpt, flowise etc.

        Args:
            platform_name (_type_)
            user_id (_type_)
            handler_function (_type_): provide handler function to call LLM
            handler_name (_type_): handler name to show in log
            timeout_config (dict): {timeout_warning_sec,timeout_cut_sec,warning_message}

        Returns:
            TextSendMessage: _description_
        """                    
        result = []
        thread = threading.Thread(target=handler_function, args=(platform_name,user_id,result))
        thread.start()

        s_time = time.time()
        timeout_warning = timeout_config['timeout_warning_sec']
        timeout_cut = timeout_config['timeout_cut_sec']
        while thread.is_alive() and time.time()-s_time < int(timeout_warning):
            pass    # waiting reply
        
        if thread.is_alive() and timeout_config['enable_warning_message']==True: # send warning
            self.send_to_user(platform_name, user_id, "等待回應中...")
            logging.warning(handler_name+" reply timeout for "+timeout_warning+" seconds!")
        
        while thread.is_alive() and time.time()-s_time < int(timeout_cut):
            pass    # waiting reply
        
        # stop waiting
        if not thread.is_alive() and result[0]:
            reply_msg = result[0]
        else:
            reply_msg = handler_name+" 沒有回應或花費太久，請稍候再嘗試！"
            logging.warning(reply_msg)
    
        return TextSendMessage(text=reply_msg)

    def _chatgpt_handler(self, platform_name, user_id, result):
        reply_msg = self.chatgpt.get_response(user_id)
        result.append(reply_msg)

    def _flowise_handler(self, platform_name, user_id, result):
        reply_msg = self.flowise.get_response(user_id)
        result.append(reply_msg)

    # ? rich display

    def check_rich_display(self, platform_name, user_id, reply_msg:SendMessage) -> SendMessage:
        
        check_list = [
            self.check_run_ext_code,
            self.check_image_reply,
            self.check_video_reply,
            self.check_buttons_template_reply,
            self.check_buttons_templates_reply
        ]

        if type(reply_msg) != TextSendMessage:
            return reply_msg

        for check in check_list:
            reply_msg = check(platform_name, user_id, reply_msg, self.send_to_user)
            if type(reply_msg) != TextSendMessage:
                return reply_msg

        # all check pass
        return reply_msg

    def check_run_ext_code(self, platform_name:str, user_id:str, reply_msg:TextSendMessage, send_to_user) -> SendMessage:
        reply_msg.text = self.extrunner.check_format(platform_name, user_id, reply_msg.text, self.send_to_user)
        reply_msg.text = self.check_user_variable(user_id, reply_msg.text)
        return reply_msg

    def check_image_reply(self, platform_name:str, user_id:str, reply_msg:TextSendMessage, send_to_user) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'LoadImage')
        if command_content:
            img_domain = self.argument.read_conf('system','system_domain')+'/api/image/'
            return ImageSendMessage(original_content_url = img_domain+reply_msg.text[command_content[0]+11:command_content[1]],
                                    preview_image_url = img_domain+reply_msg.text[command_content[0]+11:command_content[1]]
                                    )
        return reply_msg

    def check_video_reply(self, platform_name:str, user_id:str, reply_msg:TextSendMessage, send_to_user) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'LoadVideo')
        if command_content:
            video_domain = self.argument.read_conf('system','system_domain')+'/api/video/'
            video_thumbnail_domain = self.argument.read_conf('system','system_domain')+'/api/video_thumbnail/'

            video_file_name = reply_msg.text[command_content[0]+11:command_content[1]].split('.')[0]
            return VideoSendMessage(original_content_url = video_domain+reply_msg.text[command_content[0]+11:command_content[1]],
                                    preview_image_url = video_thumbnail_domain + video_file_name + '.jpg'
                                    )
        return reply_msg


    def check_buttons_template_reply(self, platform_name:str, user_id:str, reply_msg:TextSendMessage, send_to_user) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'ButtonsTemplate')
        if command_content:
            buttons_template_array = json.loads(command_content[2])
            buttons_template = self._generate_button_template(buttons_template_array,ButtonsTemplate)
            return TemplateSendMessage(alt_text=buttons_template_array['title'], template=buttons_template)
        return reply_msg

    def check_buttons_templates_reply(self, platform_name:str, user_id:str, reply_msg:TextSendMessage, send_to_user) -> SendMessage:
        command_content = self.fetch_command_content(reply_msg.text,'ButtonsTemplates')
        if command_content:
            buttons_template_arrays = json.loads(command_content[2])
            buttons_templates = []
            for buttons_template_array in buttons_template_arrays:
                buttons_templates.append(self._generate_button_template(buttons_template_array,CarouselColumn))
            return TemplateSendMessage(alt_text=buttons_template_arrays[0]['title'], template=CarouselTemplate(columns=buttons_templates))
        return reply_msg

    def _generate_button_template(self, buttons_template_array, T):
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

    # ? other utility

    def fetch_command_content(self, text, command) -> Tuple[int,int,str]:
        '''
        input:
            text : input text to check
            command : check if command in text
        output:
            (start_index, end_index, command_content)
        '''
        if text and '['+command+'-' in text:
            try:
                s_index = text.index('['+command+'-')
                e_index = text.index('] ',s_index)
                command_content = text[s_index+len(command)+2:e_index]
                return (s_index, e_index, command_content)
            except ValueError:
                logging.error('command格式錯誤! 請檢查格式正確，或是結尾是否有空格。 '+text)
        return None

    def send_to_user(self, platform_name, user_id, msg:str):
        if not (self.argument.read_conf('function','send_alarm_msg')==True):
            return
        
        logging.debug('send to [%s] %s %s',platform_name,user_id,msg)
        sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, msg)
        self.db.save_reply(sentence_id, 0, 0)
        
        self.platforms[platform_name].send_to_user(user_id, msg)

    def send_to_users(self, platform_name, user_ids:list, msg:str):
        logging.debug('send to [%s] %s %s',platform_name,user_ids,msg)
        for user_id in user_ids:
            sentence_id = self.db.save_chat(user_id, int(time.time()*1000), 0, msg)
            self.db.save_reply(sentence_id, 0, 0)

        self.platforms[platform_name].send_to_users(user_ids, msg)

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