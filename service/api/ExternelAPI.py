from flask_restx import Resource

class ExternelAPI(Resource):
    """This API is use to provide externel API for outside service to use.
    Currently unusable because of system design!    

    Args:
        Resource (_type_): _description_
    """
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler
    
    # def post(self,UUID):
    #     user_config = self.apiHandler.check_request_username(request)
    #     if not user_config:
    #         return 'Not Authorized',401
    #     request_argument = request.get_json()
    #     try:
    #         result = self.db.ban_user(UUID,request_argument['ban'])
    #         if result == None:
    #             return 'SQL Command Failed', 500
    #     except KeyError:
    #         return 'Bad Request',400
    #     return 'OK',200
