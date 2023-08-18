from flask_restx import Resource
from flask import request
from Argument import Argument

class ChatSetting(Resource):
    def __init__(self, *args, **kwargs):
        self.argument = Argument()
        self.apiHandler = kwargs['apiHandler']
        
    def post(self,key):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            if key=='' or request_argument['value']=='':
                return 'Bad Request',400
            self.argument.set_conf('function',key,request_argument['value'])
        except KeyError:
            return 'Bad Request',400
        return 'OK',200