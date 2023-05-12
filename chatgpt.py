import os
import openai
import logging
from opencc import OpenCC

# pip install opencc-python-reimplemented

class ChatGPT:
    def __init__(self,db,openai_key):
        self.db = db
        self.model = os.getenv("OPENAI_MODEL", default = "text-davinci-003")
        self.cc = OpenCC('s2t')
        #self.model = os.getenv("OPENAI_MODEL", default = "chatbot")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default = 0))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default = 0))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default = 0.6))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default = 240))
        openai.api_key = openai_key

    def get_response(self, userId):
        message_list = []
        data = self.db.load_chat(userId)
        # message_list.append({'role':'user','content':'以下請用繁體中文和英文回答'})
        for row in data:
            if row[0]==0:
                role = 'assistant'
            else:
                role = 'user'
            message_list.append({'role':role,'content':row[1]})
        
        return self.send_to_openai(message_list)

    def send_to_openai(self ,message_list):
        try:
            logging.debug('send to openai %s',message_list[-1])
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
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