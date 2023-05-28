import os
import shutil
import subprocess

# make sure to run this script with ROOT Permission

# init files
# default login info : username/password

process = subprocess.Popen("sudo apt -y install ffmpeg", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

os.makedirs('data', exist_ok=True)
os.makedirs('resources/image', exist_ok=True)
os.makedirs('resources/video', exist_ok=True)
os.makedirs('resources/video/img', exist_ok=True)
os.makedirs('/opt/grafana', exist_ok=True)

shutil.copy('default/config.conf', 'data/config.conf')
shutil.copy('default/chat.db', '/opt/grafana/chat.db')
