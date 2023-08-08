from flask_restful import Resource, reqparse, request
from flask import send_file
import werkzeug
import os
import logging
# import imghdr

class VideoThumbnailAPI(Resource):
    def __init__(self,db,apiHandler):
        self.db = db
        self.apiHandler = apiHandler
        self.baseURL = 'resources/video/img/'
    
    def get(self, filename):
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return send_file(filename, mimetype='image/jpeg')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)
        