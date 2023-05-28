from flask_restful import Resource, reqparse, request
from flask import send_file
import werkzeug
import os
import logging
# import imghdr
from os import walk

class VideoAPI(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler
        self.baseURL = 'resources/video/'
        self.videoimgURL = self.baseURL + 'img/'
    
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        video_file = args['file']

        num = self.get_next_filename()
        if not num:
            return ('Video Folder Format Error', 500)

        if video_file.content_type == 'video/mp4':
            video_file.save(self.baseURL+num+'.mp4')
            # 生成影片封面縮圖
            os.system('ffmpeg -i '+self.baseURL+num+'.mp4 -ss 00:00:01.000 -vframes 1 '+self.videoimgURL+num+'.jpg')
            return (num+'.mp4',200)
        else :
            return ('error',415) 
        
    def get(self, filename):
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.mp4'):
                return send_file(filename, mimetype='video/mp4')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)
        
    def get_next_filename(self):
        # get file in path
        files = os.listdir(self.baseURL)
        for file in files:
            if os.path.isdir(self.baseURL + file):
                files.remove(file)
        
        if not files:
            return '1'
        try:
            max_num = max([int(file.split(".")[0]) for file in files])
            return str(max_num+1)
        except Exception as e:
            logging.error('Video Folder Format Error!')
            return None