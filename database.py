import sqlite3
import time

class database:
    def __init__(self):
        self.conn = sqlite3.connect('data/chat.db', check_same_thread=False)
        self.c = self.conn.cursor()

    def save_chat(self, userId, time ,direction, text): # 0:AI ; 1:Human
        # print(userId, time , direction, text)

        try:
            self.c.execute('INSERT INTO Message (userId,time,direction,text) VALUES '+str((userId, time, direction, text)))
            self.c.execute('SELECT last_insert_rowid()')
            result = self.c.fetchall()
        except sqlite3.Error as err:
            print('ERR sqlite save failed!', err)
        self.conn.commit()
        return result[0][0]
    
    def save_reply(self, messageId, reply_mode, reply_rule):
        if reply_rule==None: reply_rule=''
        try:
            self.c.execute('INSERT INTO Message_reply (messageId,reply_mode,reply_rule) VALUES '+str((messageId, reply_mode, reply_rule)))
        except sqlite3.Error as err:
            print('ERR sqlite save failed!', err)
        self.conn.commit()

    def search_message(self, messageId):
        try:
            self.c.execute('SELECT text FROM Message WHERE messageId=='+str(messageId))
            result = self.c.fetchall()
        except sqlite3.Error as err:
            print('ERR sqlite save failed!', err)
        self.conn.commit()
        return result

    def deal_sql_request(self, command):
        try:
            self.c.execute(command)
            result = self.c.fetchall()
        except sqlite3.Error as err:
            print('ERR request failed!', command, err)
            result = None
        self.conn.commit()
        return result

    def load_chat(self, userId, count=5):
        result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time')
        return result

    def load_chat_limited(self, userId, count=5, time_offset=180):
        time_limit = int((time.time()-time_offset)*1000)
        result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" AND time>='+str(time_limit)+' ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time')
        return result

    def load_user_amount(self):
        result = self.deal_sql_request('SELECT COUNT(DISTINCT userId) FROM Message')
        return result[0][0]

    def load_chat_amount(self):
        result = self.deal_sql_request('SELECT COUNT(*) FROM Message')
        return result[0][0]

    def load_chat_amount_each_month(self):
        result = self.deal_sql_request("SELECT strftime('%Y-%m-%d', time / 1000, 'unixepoch') as day, COUNT(*) FROM Message GROUP BY day")
        result = {r[0]:r[1] for r in result}
        return result
    
    def load_lest_reply_id(self, user_id):
        result = self.deal_sql_request('SELECT messageId FROM Message WHERE userId=="'+user_id+'" AND direction==0 ORDER BY time DESC LIMIT 1')
        if result:
            return result[0][0]
        else:
            return None

    def check_reply_mode(self, messageId):
        result = self.deal_sql_request('SELECT reply_mode,reply_rule FROM Message_reply WHERE messageId=='+str(messageId))
        if result:
            return result[0]
        else:
            return None

    def load_system_logs(self):
        # logs = [{'time':'2020-01-01','status':'success' ,'text':'test'}]
        logs = []

        if len(logs)==0:
            logs = [{'time':'','status':'success' ,'text':'all good'}]
        
        # if len(logs) < 10:
        #     logs = logs + [{'time':'','status':'null' ,'text':''}]*(10-len(logs))
        return logs
    
    def search_keyword(self, str):
        result = self.deal_sql_request('SELECT enable,reply,id FROM Keyword WHERE instr("'+str+'",keyword)>0 ORDER BY length(keyword) DESC')
        for r in result:
            if r[0] == 1:   # keyword enable
                return (r[1],r[2])
        return None

    def load_keyword(self):
        result = self.deal_sql_request('SELECT Id,Enable,Keyword,Reply,Note FROM Keyword')
        return result

    def add_keyword(self, enable, keyword, reply, note):
        result = self.deal_sql_request('INSERT INTO Keyword (enable,keyword,reply,note) VALUES ("'+str(enable)+'","'+keyword+'","'+reply+'","'+note+'")')
        return result
    
    def delete_keyword(self, keyword_id):
        result = self.deal_sql_request('DELETE FROM Keyword WHERE Id='+str(keyword_id))
        return result
    
    def load_all_story(self):
        result = self.deal_sql_request('SELECT Story.story_id, enable, sentence_id, condiction FROM Story,Story_sentence WHERE Story.story_id==Story_sentence.story_id AND Story_sentence.type==0')
        return result

    def load_next_sentence(self, sentence_id):
        result = self.deal_sql_request('SELECT sentence2 FROM Story_choice WHERE sentence1=='+str(sentence_id))
        return result

    def load_sentence(self, sentence_id):
        result = self.deal_sql_request('SELECT sentence_id, type, output, condiction FROM Story_sentence WHERE sentence_id=='+str(sentence_id))
        return result[0]

if __name__ == '__main__':
    db = database()
    data = db.load_next_sentence(1)
    print(data)