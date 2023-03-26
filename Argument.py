import configparser
import json

class Argument:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.openai_key = self.read_conf('key','openai_key')
        self.linebot_apt = self.read_conf('key','linebot_apt')
        self.webhook_secret = self.read_conf('key','webhook_secret')
        self.user_list = json.loads(self.config['user']['user_list'])

    def read_conf(self,type,key):
        self.config.read('data/config.conf')
        return self.config[type][key]

    def set_conf(self,type,key,value):
        self.config[type][key] = value
        with open('data/config.conf', 'w') as configfile:
            self.config.write(configfile)