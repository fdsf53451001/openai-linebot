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
        except sqlite3.Error as err:
            print('ERR sqlite save failed!', err)
        self.conn.commit()
    
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
    
    def load_system_logs(self):
        # logs = [{'time':'2020-01-01','status':'success' ,'text':'test'}]
        logs = []

        if len(logs)==0:
            logs = [{'time':'','status':'success' ,'text':'all good'}]
        
        # if len(logs) < 10:
        #     logs = logs + [{'time':'','status':'null' ,'text':''}]*(10-len(logs))
        return logs
    
    def search_keyword(self, str):
        result = self.deal_sql_request('SELECT enable,reply FROM Keyword WHERE instr("'+str+'",keyword)>0 ORDER BY length(keyword) DESC')
        for r in result:
            if r[0] == 1:   # keyword enable
                return r[1]
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
    
if __name__ == '__main__':
    db = database()
    data = db.add_keyword(0,'test','test','test')
    print(data)