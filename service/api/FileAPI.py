from flask_restx import Resource, reqparse
from flask import send_file, request
import werkzeug

class FileAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.baseURL = 'resources/files/'
    
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        if filename == 'undefined':
            return 'No filename',400

        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        file = args['file']
        if file.content_length > 1024*1024*10: # 10MB
            return 'File too large',413

        file.save(self.baseURL+filename)
        return (filename,200)
        