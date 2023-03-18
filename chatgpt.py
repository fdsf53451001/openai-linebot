from argument import Argument
import os
import openai

from database import database

openai.api_key = Argument.openai_key
db = database()

class ChatGPT:
    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", default = "text-davinci-003")
        #self.model = os.getenv("OPENAI_MODEL", default = "chatbot")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default = 0))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default = 0))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default = 0.6))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default = 240))

    def get_response(self, userId):
        message_list = []
        data = db.load_chat(userId)
        for row in data:
            if row[0]==0:
                role = 'assistant'
            else:
                role = 'user'
            message_list.append({'role':role,'content':row[1]})

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=message_list
                )

            #print(response)
            return response['choices'][0]['message']['content']
        
        except openai.error.RateLimitError:
            return None