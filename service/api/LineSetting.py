from flask_restx import Resource
from flask import request
import json

class LineReachMenu(Resource):
    def __init__(self,argument,apiHandler,line_platform):
        self.argument = argument
        self.apiHandler = apiHandler
        self.line_platform = line_platform

    # def get(self):
    #     return json.dumps({'richmenu_image':self.argument.read_conf('line','richmenu_image'),'richmenu_json':self.argument.read_conf('line','richmenu_json')})
    
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            if request_argument['richmenu_image']=='' or request_argument['richmenu_json']=='':
                return 'Bad Request',400

            richmenu_image = 'resources/image/' + request_argument['richmenu_image']
            richmenu_json = 'resources/files/' + request_argument['richmenu_json']
            status = self.line_platform.set_default_rich_menu(richmenu_image,richmenu_json)
            if not status: return 'Bad Request',400
            self.argument.set_conf('line','richmenu_image',request_argument['richmenu_image'])
            self.argument.set_conf('line','richmenu_json',request_argument['richmenu_json'])
            return 'OK',200
        
        except KeyError:
            return 'Bad Request',400