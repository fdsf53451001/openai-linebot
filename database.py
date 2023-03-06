import sqlite3

class database:
    def __init__(self):
        self.conn = sqlite3.connect('chat.db', check_same_thread=False)
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

if __name__ == '__main__':
    db = database()
    data = db.load_chat("U6a538ecc80009f40ac41e09d21ae6155")
    print(data)