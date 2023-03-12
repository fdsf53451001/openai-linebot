import sqlite3
import time

class database:
    def __init__(self):
        self.conn = sqlite3.connect('data\chat.db', check_same_thread=False)
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
        return result
        

if __name__ == '__main__':
    db = database()
    data = db.load_chat_amount_each_month()
    print(data)