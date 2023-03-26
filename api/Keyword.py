from flask_restful import Resource, request

class Keywords(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler

    def get(self):
        return self.db.load_keyword()
    
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            if request_argument['enable']!='0' and request_argument['enable']!='1':
                return 'Bad Request',400
            result = self.db.add_keyword(request_argument['enable'],request_argument['keyword'],request_argument['reply'],request_argument['note'])
            if result == None:
                return 'SQL Command Failed', 500
        except KeyError:
            return 'Bad Request',400
        return 'OK',200

class Keyword(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler

    def delete(self,keyword_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        result = self.db.delete_keyword(keyword_id)
        if result == None:
            return 'SQL Command Failed', 500
        return 'OK',200