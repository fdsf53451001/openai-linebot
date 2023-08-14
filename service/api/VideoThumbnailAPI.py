from flask_restx import Resource, reqparse
from flask import request
from flask import send_file
import werkzeug
import os
import logging
# import imghdr

class VideoThumbnailAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
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
        