import os
import subprocess

# make sure to run this script with ROOT Permission

# init files
# default login info : username/password

process = subprocess.Popen("sudo apt -y install ffmpeg", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# set timezone to UTC+8
process = subprocess.Popen("sudo timedatectl set-timezone Asia/Taipei", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

os.makedirs('data', exist_ok=True)
os.makedirs('static/grafana', exist_ok=True)

os.makedirs('resources/image', exist_ok=True)
os.makedirs('resources/video', exist_ok=True)
os.makedirs('resources/files', exist_ok=True)
os.makedirs('resources/video/img', exist_ok=True)
