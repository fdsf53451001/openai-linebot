from flask_restful import Resource, reqparse, request
from flask import send_file
import werkzeug

class SystemConfigAPI(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler
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
        