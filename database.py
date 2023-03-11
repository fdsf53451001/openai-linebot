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
    
    def load_chat(self, userId, count=5):
        sql = 'SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time'
        try:
            self.c.execute(sql)
            result = self.c.fetchall()
        except sqlite3.Error as err:
            print('ERR sqlite load failed!', err)
        return result

    def load_chat_limited(self, userId, count=5, time_offset=180):
        time_limit = int((time.time()-time_offset)*1000)
        sql = 'SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" AND time>='+str(time_limit)+' ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time'
        try:
            self.c.execute(sql)
            result = self.c.fetchall()
        except sqlite3.Error as err:
            print('ERR sqlite load failed!', err)
        return result

if __name__ == '__main__':
    db = database()
    data = db.load_chat_limited("U6a538ecc80009f40ac41e09d21ae6155")
    print(data)