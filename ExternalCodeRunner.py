import threading
import subprocess
import logging

class ExternalCodeRunner():
    def check_format(self, platform_name, user_id, msg, send_to_user) -> str:

        command_content = self.fetch_command_content(msg, 'ExtCode')
        if not command_content:
            return msg

        threading.Thread(target=self.run_command, args=(command_content[2], platform_name, user_id, send_to_user)).start()
        return 'Code Running...'

    def run_command(self, command, platform_name, user_id, send_to_user):
        logging.info('Running command: %s', command)
        result = None
        if command=='hello_world':
            result = self.run('python3 service/custom_code/hello_world.py').decode()
        else:
            result = '程式錯誤！'
            logging.error('command錯誤！指定程式不存在：'+command)
        
        if not result or result=='':
            result = '程式執行完成！'
        send_to_user(platform_name, user_id, result) 

    def run(self, command):
        result = None
        try:
            result = subprocess.check_output(command, shell=True)
        except Exception as e:
            logging.error(e)
        return result
    
    def fetch_command_content(self, text, command):
        if text and '['+command+'-' in text:
            try:
                s_index = text.index('['+command+'-')
                e_index = text.index('] ',s_index)
                command_content = text[s_index+len(command)+2:e_index]
                return (s_index, e_index, command_content)
            except ValueError:
                logging.error('command格式錯誤! 請檢查格式正確，或是結尾是否有空格。 '+text)
        return None