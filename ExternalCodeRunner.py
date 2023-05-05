import threading
import subprocess
import logging

class ExternalCodeRunner():
    def check_format(self, command, platform_name, user_id, send_to_user):
        if not command:
            return None
        command_content = self.fetch_command_content(command, 'ExtCode')
        if not command_content:
            return command

        threading.Thread(target=self.run_command, args=(command[2], platform_name, user_id, send_to_user)).start()
        return 'Code Running...'

    def run_command(self, command, platform_name, user_id, send_to_user):
        logging.info('Running command: %s', command)
        result = None
        if command=='hello_world':
            result = self.run('python3 custom_code/hello_world.py').decode()

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
            s_index = text.index('['+command+'-')
            e_index = text.index(']',s_index)
            command_content = text[s_index+len(command)+2:e_index]
            return (s_index, e_index, command_content)
        return None