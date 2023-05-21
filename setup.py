import os
import shutil

# init files
# default login info : username/password

os.makedirs('data', exist_ok=True)
os.makedirs('resources/image', exist_ok=True)
os.makedirs('/opt/grafana', exist_ok=True)

shutil.copy('default/config.conf', 'data/config.conf')
shutil.copy('default/chat.db', '/opt/grafana/chat.db')
