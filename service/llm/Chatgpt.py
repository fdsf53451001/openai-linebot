import os
import openai
import logging
from opencc import OpenCC

# pip install opencc-python-reimplemented

class ChatGPT:
    def __init__(self,db,argument):
        self.db = db
        self.argument = argument

        self.cc = OpenCC('s2t')
        # self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default = 0))
        # self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default = 0.6))
        # self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default = 240))
        openai.api_key = argument.openai_key

    def get_response(self, userId) -> str:
        message_list = []
        data = self.db.load_chat(userId)

        if self.argument.read_conf('openai','prompt_prefix') != 'None':
            message_list.append({'role':'system','content':self.argument.read_conf('openai','prompt_prefix')})
        
        for row in data:
            if row[0]==0:
                role = 'assistant'
            else:
                role = 'user'
            message_list.append({'role':role,'content':row[1]})
        
        return self.send_to_openai(message_list)

    def send_to_openai(self ,message_list) -> str:
        try:
            logging.debug('send to openai %s',message_list[-1])
            response = openai.ChatCompletion.create(
                model=self.argument.read_conf('openai','model'),
                temperature=float(self.argument.read_conf('openai','chat_temperature')),
                max_tokens=int(self.argument.read_conf('openai','max_tokens')),
                messages=message_list
                )

            if response:
                response_msg = self.cc.convert(response['choices'][0]['message']['content'])
                logging.debug('receive from openai %s',response_msg)
                return response_msg
            else:
                return None
        
        except openai.error.RateLimitError:
            return None
        
        except ConnectionResetError:
            return None