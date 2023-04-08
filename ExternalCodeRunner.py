import threading
import subprocess
import logging

class ExternalCodeRunner():
    def check_format(self, command, platform_name, user_id, send_to_user):
        if not command:
            return None
        if not command.startswith('[ExtCode] '):
            return command
        command = command.split(' ')[1]

        threading.Thread(target=self.run_command, args=(command, platform_name, user_id, send_to_user)).start()
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