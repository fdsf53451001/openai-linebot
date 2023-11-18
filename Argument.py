import configparser
import os
import json

class Argument:
    def __init__(self):
        self.config_file_path = 'data/config.json'
        self.openai_key = self.read_conf('key','openai_key')
        self.line_channel_access_token = self.read_conf('key','line_channel_access_token')
        self.line_channel_secret = self.read_conf('key','line_channel_secret')
        self.discord_token = self.read_conf('key','discord_token')

    def read_conf(self,type,key):
        # load json
        with open(self.config_file_path, 'r', encoding="utf8") as f:
            config = json.load(f)
            # get value, if not exist return None
            if type not in config or key not in config[type]:
                return None
            return config[type][key]
        
    def set_conf(self,type,key,value):
        # load json
        with open(self.config_file_path, 'r', encoding="utf8") as f:
            config = json.load(f)
        with open(self.config_file_path, 'w', encoding="utf8") as f:
            config[type][key] = value
            json.dump(config, f, ensure_ascii=False)

    def read_whole_conf(self):
        # load json
        with open(self.config_file_path, 'r', encoding="utf8") as f:
            return f.read()
        
    def set_whole_conf(self,config):
        # load json
        with open(self.config_file_path, 'w', encoding="utf8") as f:
            f.write(config)