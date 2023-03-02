import sqlite3

class database:
    def __init__(self):
        self.conn = sqlite3.connect('chat.db', check_same_thread=False)
        self.c = self.conn.cursor()

    def save_chat(self, userId, time ,direction, text): # 0:AI ; 1:Human
        print(userId, time , direction, text)

        try:
            self.c.execute('INSERT INTO Message (userId,time,direction,text) VALUES '+str((userId, time, direction, text)))
        except sqlite3.Error as err:
            print('ERR sqlite save failed!', err)
        self.conn.commit()