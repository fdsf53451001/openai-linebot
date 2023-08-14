from flask_restx import Resource, reqparse
from flask import request
from flask import send_file
import werkzeug

class SystemConfigAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.configURL = 'data/config.conf'
    
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        file = args['file']

        if file.content_type == 'text/plain' and file.filename == 'config.conf':
            file.save(self.configURL)
            return ('ok',200)
        else:
            return ('error',415) 
        
    
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401

        return send_file(self.configURL, mimetype='text/plain')
        