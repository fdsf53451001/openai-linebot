import os

chat_language = os.getenv("INIT_LANGUAGE", default = "zh")

MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default = 6)) #20
LANGUAGE_TABLE = {
  "zh": "嗨！",
  "en": "Hi!"
}

class Prompt:
    def __init__(self):
        self.msgs = {}
    
    def new_session(self,userId):
        self.msgs[userId] = []
        self.msgs[userId].append(f"AI:{LANGUAGE_TABLE[chat_language]}")

    def add_msg(self, userId, new_msg):
        if userId not in self.msgs: # first session
            self.new_session(userId)

        elif len(self.msgs) >= MSG_LIST_LIMIT: # not first
            self.remove_msg()

        self.msgs[userId].append(new_msg)

    def remove_msg(self, userId):
        self.msgs[userId].pop(0)

    def generate_prompt(self, userId):
        return '\n'.join(self.msgs[userId])
