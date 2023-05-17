import configparser
import json

class Argument:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.openai_key = self.read_conf('key','openai_key')
        self.line_channel_access_token = self.read_conf('key','line_channel_access_token')
        self.line_channel_secret = self.read_conf('key','line_channel_secret')
        self.discord_token = self.read_conf('key','discord_token')
        # self.user_list = json.loads(self.config['user']['user_list'])

    def read_conf(self,type,key):
        self.config.read('data/config.conf', encoding="utf8")
        return self.config[type][key]

    def set_conf(self,type,key,value):
        self.config[type][key] = value
        with open('data/config.conf', 'w', encoding="utf8") as configfile:
            self.config.write(configfile)