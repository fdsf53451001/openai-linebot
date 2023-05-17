import sys    
import bcrypt
import logging
import json

from Argument import Argument

class APIHandler:
    def __init__(self,db):
        self.db = db
        self.argument = Argument()
        self.user_list = json.loads(self.argument.read_conf('user','user_list'))
        pass

    def deal_api_request(self, service_type, request_data):
        if service_type == 'keyword':
            pass
        else:
            return 'No Service Provide', 400
    
    def user_login(self, username, password):
        try:
            index = [user[0] for user in self.user_list].index(username)
            if self.verify_password(password,self.user_list[index][2]):
                hash_value=self.user_list[index][2]
                return hash_value
        except ValueError:
            pass
        # login fail
        return None
    
    def check_sid_valid(self, sid):
        sid_list = [user[2] for user in self.user_list]
        if sid==None or sid not in sid_list:
            return None
        else:
            return self.user_list[sid_list.index(sid)][0]
    
    def check_request_username(self,request):
        args = request.args
        sid = args.get('sid', None)
        user_info = self.check_sid_valid(sid)
        if user_info:
            return (sid, user_info)
        return None

    # generate password hash

    def hash_password(self, password):
        # Generate a salt
        salt = bcrypt.gensalt()
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def reload_password_hash(self):
        self.user_list = json.loads(self.argument.read_conf('user','user_list'))
        for user in self.user_list:
            if(user[1] != ''):
                user[2] = self.hash_password(user[1])
                user[1] = '' # remove plain password
                logging.warning('user: %s password changed' % user[0])
        self.argument.set_conf('user','user_list',json.dumps(self.user_list))
