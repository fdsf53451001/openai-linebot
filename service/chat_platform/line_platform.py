from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, BubbleContainer, RichMenu
import json
import logging

class line_platform():
    def __init__(self, argument, messageHandler):
        self.line_bot_api = LineBotApi(argument.line_channel_access_token)
        self.line_handler = WebhookHandler(argument.line_channel_secret)
        self.line_handler.add(MessageEvent, message=TextMessage)(self.handle_message)
        self.messageHandler = messageHandler
        self.messageHandler.set_platform('line',self)

    def receive(self,request):
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']
        # get request body as text
        body = request.get_data(as_text=True)
        # app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            self.line_handler.handle(body, signature)
        except InvalidSignatureError:
            return ('abort',400)
        return ('OK',200)

    def handle_message(*args):
        self = args[0]
        event = args[1]
        if event.message.type != "text":
            return
        
        user_id = event.source.user_id
        receive_text = event.message.text
        receive_timestamp = event.timestamp

        reply_msg = self.messageHandler.handdle('line',user_id, receive_text, receive_timestamp)

        try:
            self.line_bot_api.reply_message(
                    event.reply_token,
                    reply_msg)
        except LineBotApiError as e:
            logging.error('line reply error %s',e)

    def send_to_user(self, user_id, message):
        self.line_bot_api.push_message(user_id, TextSendMessage(text=message))

    def send_to_users(self, user_ids:list, message:str):
        self.line_bot_api.multicast(user_ids, TextSendMessage(text=message))

    def send_to_user_with_flex_msg(self, user_id, flex_message_json):
        bubble_container = BubbleContainer.new_from_json_dict(flex_message_json)
        flex_message = FlexSendMessage(alt_text="Flex Message", contents=bubble_container)
        self.line_bot_api.push_message(user_id, flex_message)

    def get_user_profile(self, user_id):
        try:
            profile = self.line_bot_api.get_profile(user_id)
            return (profile.display_name, profile.picture_url)
        except LineBotApiError as e:
            logging.error('get_user_profile error %s',e)
            return None
    
    def upload_rich_menu(self, image_path, json_path) -> str:
        try:
            with open(json_path, 'r') as f:
                rich_menu_json = json.load(f)
            rich_menu = RichMenu.new_from_json_dict(rich_menu_json)
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu=rich_menu)
            with open(image_path, 'rb') as f:
                if image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                    self.line_bot_api.set_rich_menu_image(rich_menu_id, 'image/jpeg', f)
                elif image_path.endswith('.png'):
                    self.line_bot_api.set_rich_menu_image(rich_menu_id, 'image/png', f)
                else:
                    logging.error('Line setup RichMenu Failed : image format not support.')
                    raise Exception('image format not support')
            return rich_menu_id
        
        except Exception as e:
            logging.error('upload richmenu error %s',e)
            return False
    
    def set_default_rich_menu(self, rich_menu_id:str):
        try:
            self.line_bot_api.set_default_rich_menu(rich_menu_id)
            return True
        except LineBotApiError as e:
            logging.error('set default richmenu error %s',e)

    def set_richmenu_for_user(self, user_id:str, rich_menu_id:str):
        try:
            self.line_bot_api.link_rich_menu_to_user(user_id, rich_menu_id)

            print("Rich Menu successfully set for the user!")

        except LineBotApiError as e:
            logging.error('set user richmenu error %s',e)