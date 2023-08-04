import requests

class Flowise:
    def __init__(self, db, argument) -> None:
        self.db = db
        self.argument = argument
    
    def get_response(self, userId) -> str:
        try:
            data = self.db.load_chat(userId, 1)

            API_URL = self.argument.read_conf('flowise','flowise_api_url')

            def query(payload):
                response = requests.post(API_URL, json=payload)
                return response.json()
                
            output = query({"question": data[-1][1]})
            return output
        
        except:
            return 'Flowise沒有回應，請重新嘗試。'