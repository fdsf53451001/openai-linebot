from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import logging

class line_platform():
    def __init__(self, argument, messageHandler):
        self.line_bot_api = LineBotApi(argument.linebot_apt)
        self.line_handler = WebhookHandler(argument.webhook_secret)
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
        # logging.info('receive from %s %s',user_id,receive_text)

        reply_msg = self.messageHandler.handdle('line',user_id, receive_text, receive_timestamp)

        # logging.info('reply to %s %s',user_id,reply_msg)
        self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_msg))

    def send_to_user(self, user_id, message):
        # logging.info('send to %s %s',user_id,message)
        if user_id=='testing': return
        self.line_bot_api.push_message(user_id, TextSendMessage(text=message))

    def get_user_profile(self, user_id):
        try:
            profile = self.line_bot_api.get_profile(user_id)
            return (profile.display_name, profile.picture_url)
        except LineBotApiError as e:
            logging.error('get_user_profile error %s',e)
            return None
        