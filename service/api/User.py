from flask_restx import Resource
from flask import request

class User(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
    
    def post(self,UUID):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            result = self.db.ban_user(UUID,request_argument['ban'])
            if result == None:
                return 'SQL Command Failed', 500
        except KeyError:
            return 'Bad Request',400
        return 'OK',200
