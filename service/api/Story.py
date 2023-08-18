from flask_restx import Resource
from flask import request
import json

class Story_name(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']

    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        return json.dumps(self.db.load_story_name(),ensure_ascii=False)
    

class Story_sentence(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']

    def get(self, story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        return json.dumps(self.db.load_sentences_from_story(story_id),ensure_ascii=False)
        
    def post(self,story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401

        request_argument = request.get_json()
        try:
            story_name =  request_argument['story_name']
            story_content = request_argument['story_content']
            if story_id!="0":
                self.delete_story(story_id)
            self.create_new_story(story_name,story_content)
        except KeyError:
            return 'Bad Request',400
        return 'OK',200

    def delete(self,story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        self.delete_story(story_id)
        return 'OK',200

    def create_new_story(self, story_name,story_content):
        story_id = self.db.add_story_name(story_name)
        for i in range(len(story_content)):
            sentencce_id = self.db.add_story_sentence(story_id, story_content[i][1], story_content[i][2], story_content[i][3])
            # fix auto fillin sentence id
            for j in range(i,len(story_content)):
                if str(story_content[j][1]) == str(story_content[i][0]):
                    story_content[j][1] = sentencce_id

    def delete_story(self, story_id):
        self.db.delete_storyname_id(story_id)
        self.db.delete_storysentence_id(story_id)