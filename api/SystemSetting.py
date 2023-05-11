from flask_restful import Resource, request
from Argument import Argument
import json

class SystemSetting(Resource):
    def __init__(self,apiHandler):
        self.argument = Argument()
        self.apiHandler = apiHandler
        
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        try:
            with open('data/config.conf','r') as f:
                configs = f.read()
                return configs
        except:
            return 'Internal Server Error',500
    
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        
        if request_argument['settings']=='':
            return 'Bad Request',400
        else:
            with open('data/config.conf','w') as f:
                f.write(request_argument['settings'])
            self.apiHandler.reload_password_hash()
            return 'OK',200