import sys

from Argument import Argument

class APIHandler:
    def __init__(self,db):
        self.db = db
        self.argument = Argument()
    
    def deal_api_request(self, service_type, request_data):
        if service_type == 'keyword':
            pass
        else:
            return 'No Service Provide', 400
    
    def user_login(self, username, password):
        try:
            index = [user[0] for user in self.argument.user_list].index(username)
            if password == self.argument.user_list[index][1]:
                sessionID=self.argument.user_list[index][2]
                return sessionID
        except ValueError:
            pass
        # login fail
        return None
    
    def check_sid_valid(self, sid):
        sid_list = [user[2] for user in self.argument.user_list]
        if sid==None or sid not in sid_list:
            return None
        else:
            return self.argument.user_list[sid_list.index(sid)][0]
    
    def check_request_username(self,request):
        args = request.args
        sid = args.get('sid', None)
        user_info = self.check_sid_valid(sid)
        if user_info:
            return (sid, user_info)
        return None