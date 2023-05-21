from flask_restful import Resource, reqparse, request
from flask import send_file
import werkzeug
import os
import logging
# import imghdr

class ImageAPI(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler
        self.baseURL = '/home/user/Desktop/openai-linebot/resources/image/'
    
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        image_file = args['file']

        num = self.get_next_filename()
        if not num:
            return ('Image Folder Format Error', 500)

        if image_file.content_type == 'image/png':
            image_file.save(self.baseURL+num+'.png')
            return (num+'.png',200)
        elif image_file.content_type == 'image/jpeg':
            image_file.save(self.baseURL+num+'.jpeg')
            return (num+'.jpeg',200)
        else :
            return ('error',415) 
        
    
    def get(self, filename):
        # Logic to fetch or generate the image
        # Replace this with your actual image retrieval code
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.png'):
                return send_file(filename, mimetype='image/png')
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return send_file(filename, mimetype='image/jpeg')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)
        
    def get_next_filename(self):
        files = os.listdir(self.baseURL)
        if not files:
            return '1'
        try:
            max_num = max([int(file.split(".")[0]) for file in files])
            return str(max_num+1)
        except:
            logging.error('Image Folder Format Error!')
            return None