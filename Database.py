import sqlite3
import time
import threading
import json

class database:
    def __init__(self, db_file_path, db_lock):
        self.conn = sqlite3.connect(db_file_path, check_same_thread=False)
        self.c = self.conn.cursor()
        self.db_lock = db_lock

    def deal_sql_request(self, command, params=None) -> list:
        # TODO : 建議使用transaction重新改寫
        try:
            self.db_lock.acquire()
            if params:
                self.c.execute(command, params)
            else:
                self.c.execute(command)
            result = self.c.fetchall()
            self.conn.commit()
        except sqlite3.Error as err:
            print('ERR request failed!', command, err)
            result = None
        finally:
            self.db_lock.release()
            return result

    ### Chat Operation

    def save_chat(self, userId, time ,direction, text): # 0:AI ; 1:Human
        # print(userId, time , direction, text)
        # self.deal_sql_request('INSERT INTO Message (userId,time,direction,text) VALUES '+str((userId, time, direction, text)))
        self.deal_sql_request('INSERT INTO Message (userId,time,direction,text) VALUES (?, ?, ?, ?)', (userId, time, direction, text))
        result = self.deal_sql_request('SELECT last_insert_rowid()')
        return result[0][0]
    
    def save_reply(self, messageId, reply_mode, reply_rule):
        if reply_rule==None: reply_rule=''
        # self.deal_sql_request('INSERT INTO Message_reply (messageId,reply_mode,reply_rule) VALUES '+str((messageId, reply_mode, reply_rule)))
        self.deal_sql_request('INSERT INTO Message_reply (messageId,reply_mode,reply_rule) VALUES (?, ?, ?)', (messageId, reply_mode, reply_rule))

    # def search_message(self, messageId):
    #     result = self.deal_sql_request('SELECT text FROM Message WHERE messageId=='+str(messageId))
    #     return result

    # def load_chat(self, userId, count=5):
    #     result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time')
    #     return result

    # def load_chat_deteil(self, count=100):
    #     result = self.deal_sql_request('SELECT time,userId,name,direction,text FROM Message,User WHERE Message.userId==User.UUID ORDER BY messageId DESC LIMIT 100')
    #     return result

    # def load_chat_limited(self, userId, count=5, time_offset=180):
    #     time_limit = int((time.time()-time_offset)*1000)
    #     result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId="'+userId+'" AND time>='+str(time_limit)+' ORDER BY time  DESC LIMIT '+str(count)+') AS A ORDER BY time')
    #     return result

    # def load_chat_amount(self):
    #     result = self.deal_sql_request('SELECT COUNT(*) FROM Message')
    #     return result[0][0]

    # def load_chat_amount_each_month(self):
    #     result = self.deal_sql_request("SELECT strftime('%Y-%m-%d', time / 1000, 'unixepoch') as day, COUNT(*) FROM Message GROUP BY day")
    #     result = {r[0]:r[1] for r in result}
    #     return result
    
    # def load_lest_reply_id(self, user_id):
    #     result = self.deal_sql_request('SELECT messageId FROM Message WHERE userId=="'+user_id+'" AND direction==0 ORDER BY time DESC LIMIT 1')
    #     if result:
    #         return result[0][0]
    #     else:
    #         return None

    # def check_reply_mode(self, messageId):
    #     result = self.deal_sql_request('SELECT reply_mode,reply_rule FROM Message_reply WHERE messageId=='+str(messageId))
    #     if result:
    #         return result[0]
    #     else:
    #         return None

    def search_message(self, messageId):
        result = self.deal_sql_request('SELECT text FROM Message WHERE messageId==?', (messageId,))
        return result

    def load_chat(self, userId, count=5):
        result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId=? ORDER BY time DESC LIMIT ?) AS A ORDER BY time', (userId, count))
        return result

    def load_chat_detail(self, count=100):
        result = self.deal_sql_request('SELECT time,userId,name,direction,text FROM Message,User WHERE Message.userId==User.UUID ORDER BY messageId DESC LIMIT ?', (count,))
        return result

    def load_chat_limited(self, userId, count=5, time_offset=180):
        time_limit = int((time.time()-time_offset)*1000)
        result = self.deal_sql_request('SELECT direction,text FROM (SELECT time,direction,text FROM Message WHERE userId=? AND time>=? ORDER BY time DESC LIMIT ?) AS A ORDER BY time', (userId, time_limit, count))
        return result

    def load_chat_amount(self):
        result = self.deal_sql_request('SELECT COUNT(*) FROM Message')
        return result[0][0]

    def load_chat_amount_each_month(self):
        result = self.deal_sql_request("SELECT strftime('%Y-%m-%d', time / 1000, 'unixepoch') as day, COUNT(*) FROM Message GROUP BY day")
        result = {r[0]:r[1] for r in result}
        return result

    def load_last_reply_id(self, user_id):
        result = self.deal_sql_request('SELECT messageId FROM Message WHERE userId=? AND direction==0 ORDER BY time DESC LIMIT 1', (user_id,))
        if result:
            return result[0][0]
        else:
            return None

    def check_reply_mode(self, messageId):
        result = self.deal_sql_request('SELECT reply_mode,reply_rule FROM Message_reply WHERE messageId==?', (messageId,))
        if result:
            return result[0]
        else:
            return None

    ### talk analyze

    # def load_chat_start_index_group_by_time_gap(self, time_gap=60): # sec
    #     result = self.deal_sql_request('SELECT messageId,time, (time/1000) as ts   FROM Message GROUP BY ts-ts%('+str(time_gap)+')')
    #     return result

    # def load_chats_by_start_index_limit_time(self, s_index, t_start, duration=60):
    #     result = self.deal_sql_request('SELECT direction,text FROM Message WHERE messageId>='+str(s_index)+' AND time<'+str(t_start+duration*1000))
    #     return result

    # def add_chat_session(self, messageId, time):
    #     result = self.deal_sql_request('Insert INTO Chat_session(messageId,time) SELECT '+str(messageId)+','+str(time)+' WHERE NOT EXISTS (SELECT 1 FROM Chat_session WHERE messageId=='+str(messageId)+')')
    #     return result

    # def load_chat_session(self):
    #     result = self.deal_sql_request('SELECT sessionId, messageId,time,analyze FROM Chat_session')
    #     return result
    
    # def load_chat_session_no_analyze(self):
    #     result = self.deal_sql_request('SELECT sessionId, messageId,time FROM Chat_session WHERE analyze IS NULL')
    #     return result

    # def save_chat_analyze(self, sessionId, analyze):
    #     result = self.deal_sql_request('UPDATE Chat_session SET analyze="'+analyze+'" WHERE sessionId='+str(sessionId))
    #     return result
    
    def load_chat_start_index_group_by_time_gap(self, time_gap=60): # sec
        result = self.deal_sql_request('SELECT messageId,time, (time/1000) as ts   FROM Message GROUP BY ts-ts%(?)', (time_gap,))
        return result

    def load_chats_by_start_index_limit_time(self, s_index, t_start, duration=60):
        result = self.deal_sql_request('SELECT direction,text FROM Message WHERE messageId>=? AND time<?', (s_index, t_start+duration*1000))
        return result

    def add_chat_session(self, messageId, time):
        result = self.deal_sql_request('Insert INTO Chat_session(messageId,time) SELECT ?,? WHERE NOT EXISTS (SELECT 1 FROM Chat_session WHERE messageId=?)', (messageId, time, messageId))
        return result

    def load_chat_session(self):
        result = self.deal_sql_request('SELECT sessionId, messageId,time,analyze FROM Chat_session')
        return result

    def load_chat_session_no_analyze(self):
        result = self.deal_sql_request('SELECT sessionId, messageId,time FROM Chat_session WHERE analyze IS NULL')
        return result

    def save_chat_analyze(self, sessionId, analyze):
        result = self.deal_sql_request('UPDATE Chat_session SET analyze=? WHERE sessionId=?', (analyze, sessionId))
        return result

    ### Keyword Operation

    # def search_keyword(self, str):
    #     result = self.deal_sql_request('SELECT enable,reply,id FROM Keyword WHERE instr("'+str+'",keyword)>0 ORDER BY length(keyword) DESC')
    #     for r in result:
    #         if r[0] == 1:   # keyword enable
    #             return (r[1],r[2])
    #     return None

    # def load_keyword(self):
    #     result = self.deal_sql_request('SELECT Id,Enable,Keyword,Reply,Note FROM Keyword')
    #     return result

    # def add_keyword(self, enable, keyword, reply, note):
    #     result = self.deal_sql_request('INSERT INTO Keyword (enable,keyword,reply,note) VALUES ("'+str(enable)+'","'+keyword+'",\''+reply+'\',"'+note+'")')
    #     return result
    
    # def delete_keyword(self, keyword_id):
    #     result = self.deal_sql_request('DELETE FROM Keyword WHERE Id='+str(keyword_id))
    #     return result
    
    def search_keyword(self, search_str):
        result = self.deal_sql_request('SELECT enable,reply,id FROM Keyword WHERE instr(?,keyword)>0 ORDER BY length(keyword) DESC', (search_str,))
        for r in result:
            if r[0] == 1:   # keyword enable
                return (r[1],r[2])
        return None

    def load_keyword(self):
        result = self.deal_sql_request('SELECT Id,Enable,Keyword,Reply,Note FROM Keyword')
        return result

    def add_keyword(self, enable, keyword, reply, note):
        result = self.deal_sql_request('INSERT INTO Keyword (enable,keyword,reply,note) VALUES (?,?,?,?)', (str(enable), keyword, reply, note))
        return result

    def delete_keyword(self, keyword_id):
        result = self.deal_sql_request('DELETE FROM Keyword WHERE Id=?', (str(keyword_id),))
        return result

    ### Story Operation

    # def load_all_story(self):
    #     result = self.deal_sql_request('SELECT Story.story_id, enable, sentence_id, output_or_condiction FROM Story,Story_sentence WHERE Story.story_id==Story_sentence.story_id AND Story_sentence.type==0')
    #     return result

    # def load_story_name(self):
    #     result = self.deal_sql_request('SELECT story_id, name FROM Story')
    #     return result

    # def load_next_sentence(self, sentence_id):
    #     result = self.deal_sql_request('SELECT sentence_id FROM Story_sentence WHERE parent_id=='+str(sentence_id))
    #     return result

    # def load_sentence(self, sentence_id):
    #     result = self.deal_sql_request('SELECT sentence_id, type, output_or_condiction FROM Story_sentence WHERE sentence_id=='+str(sentence_id))
    #     return result[0]

    # def load_sentences_from_story(self, story_id):
    #     result = self.deal_sql_request('SELECT sentence_id,parent_id,type,output_or_condiction FROM Story_sentence WHERE story_id=='+str(story_id))
    #     return result
    
    # def add_story_name(self, name):
    #     result = self.deal_sql_request('INSERT INTO Story (enable, name) VALUES (1,"'+name+'")')
    #     if result==None: return None
    #     result = self.deal_sql_request('SELECT last_insert_rowid()')
    #     return result[0][0]

    # def add_story_sentence(self, story_id, parent_id, type, output_or_condiction):
    #     story_id = str(story_id)
    #     parent_id = str(parent_id)
    #     type = str(type)
    #     result = self.deal_sql_request('INSERT INTO Story_sentence (story_id,parent_id,type,output_or_condiction) VALUES ("'+story_id+'","'+parent_id+'","'+type+'",\''+output_or_condiction+'\')')
    #     if result==None: return None
    #     result = self.deal_sql_request('SELECT last_insert_rowid()')
    #     return result[0][0]

    # def delete_storyname_id(self, story_id):
    #     result = self.deal_sql_request('DELETE FROM Story WHERE story_id=='+str(story_id))
    #     return result

    # def delete_storysentence_id(self, story_id):
    #     result = self.deal_sql_request('DELETE FROM Story_sentence WHERE story_id=='+str(story_id))
    #     return result

    def load_all_story(self):
        result = self.deal_sql_request('SELECT Story.story_id, enable, sentence_id, output_or_condiction FROM Story,Story_sentence WHERE Story.story_id==Story_sentence.story_id AND Story_sentence.type==?', (0,))
        return result

    def load_story_name(self):
        result = self.deal_sql_request('SELECT story_id, name FROM Story')
        return result

    def load_next_sentence(self, sentence_id):
        result = self.deal_sql_request('SELECT sentence_id FROM Story_sentence WHERE parent_id==?', (sentence_id,))
        return result

    def load_sentence(self, sentence_id):
        result = self.deal_sql_request('SELECT sentence_id, type, output_or_condiction FROM Story_sentence WHERE sentence_id==?', (sentence_id,))
        return result[0]

    def load_sentences_from_story(self, story_id):
        result = self.deal_sql_request('SELECT sentence_id,parent_id,type,output_or_condiction FROM Story_sentence WHERE story_id==?', (story_id,))
        return result

    def add_story_name(self, name):
        result = self.deal_sql_request('INSERT INTO Story (enable, name) VALUES (?, ?)', (1, name))
        if result==None: return None
        result = self.deal_sql_request('SELECT last_insert_rowid()')
        return result[0][0]

    def add_story_sentence(self, story_id, parent_id, type, output_or_condiction):
        result = self.deal_sql_request('INSERT INTO Story_sentence (story_id,parent_id,type,output_or_condiction) VALUES (?, ?, ?, ?)', (story_id, parent_id, type, output_or_condiction))
        if result==None: return None
        result = self.deal_sql_request('SELECT last_insert_rowid()')
        return result[0][0]

    def delete_storyname_id(self, story_id):
        result = self.deal_sql_request('DELETE FROM Story WHERE story_id==?', (story_id,))
        return result

    def delete_storysentence_id(self, story_id):
        result = self.deal_sql_request('DELETE FROM Story_sentence WHERE story_id==?', (story_id,))
        return result

    ### openAI
    def load_openai_usage(self):
        result = self.deal_sql_request('SELECT COUNT(1) FROM Message_reply WHERE reply_mode==4')
        return result[0][0]

    ### User Operation

    # def load_user_amount(self):
    #     result = self.deal_sql_request('SELECT COUNT(DISTINCT userId) FROM Message')
    #     return result[0][0]

    # def load_all_user(self):
    #     result = self.deal_sql_request('SELECT  UUID, platform, ban, name, photo, last_update_time, tmp,count(messageId)  FROM User, Message WHERE User.UUID==Message.userId GROUP BY UUID')
    #     return result

    # def check_user(self, user_id):
    #     result = self.deal_sql_request('SELECT UUID,last_update_time,ban FROM User WHERE UUID=="'+user_id+'"')
    #     return result

    # def add_new_user(self, user_id, platform, name, photo, last_update_time):
    #     result = self.deal_sql_request('INSERT INTO User (UUID, platform, name, photo, last_update_time) VALUES ("'+user_id+'","'+platform+'","'+name+'","'+photo+'","'+last_update_time+'")')
    #     return result

    # def add_new_user_no_profile(self, user_id, platform):
    #     result = self.deal_sql_request('INSERT INTO User (UUID, platform) VALUES ("'+user_id+'","'+platform+'")')
    #     return result
    
    # def update_user_profile(self, user_id, name, photo, last_update_time):
    #     result = self.deal_sql_request('UPDATE User SET name="'+name+'", photo="'+photo+'", last_update_time="'+last_update_time+'" WHERE UUID=="'+user_id+'"')
    #     return result

    # def ban_user(self, user_id, ban):
    #     result = self.deal_sql_request('UPDATE User SET ban='+ban+' WHERE UUID=="'+user_id+'"')
    #     return result

    # def load_all_user_extra_data(self, user_id):
    #     result = self.deal_sql_request('SELECT tmp FROM User WHERE UUID=="'+user_id+'"')
    #     if not result:
    #         return None
    #     result = json.loads(result[0][0])
    #     return result
    
    # def load_user_extra_data(self, user_id, d_name):
    #     d = self.load_all_user_extra_data(user_id)
    #     if d and d_name in d:
    #         return d[d_name]
    #     return None

    # def add_user_extra_data(self, user_id, d_name, d_value):
    #     d = self.load_all_user_extra_data(user_id)
    #     d[d_name] = d_value
    #     result = self.deal_sql_request('UPDATE User SET tmp=\''+json.dumps(d)+'\' WHERE UUID=="'+user_id+'"')
    #     return result

    def load_user_amount(self):
        result = self.deal_sql_request('SELECT COUNT(DISTINCT userId) FROM Message')
        return result[0][0]

    def load_all_user(self):
        result = self.deal_sql_request('SELECT  UUID, platform, ban, name, photo, last_update_time, tmp,count(messageId)  FROM User, Message WHERE User.UUID==Message.userId GROUP BY UUID')
        return result

    def check_user(self, user_id):
        result = self.deal_sql_request('SELECT UUID,last_update_time,ban FROM User WHERE UUID=?', (user_id,))
        return result

    def add_new_user(self, user_id, platform, name, photo, last_update_time):
        result = self.deal_sql_request('INSERT INTO User (UUID, platform, name, photo, last_update_time) VALUES (?, ?, ?, ?, ?)', (user_id, platform, name, photo, last_update_time))
        return result

    def add_new_user_no_profile(self, user_id, platform):
        result = self.deal_sql_request('INSERT INTO User (UUID, platform) VALUES (?, ?)', (user_id, platform,))
        return result

    def update_user_profile(self, user_id, name, photo, last_update_time):
        result = self.deal_sql_request('UPDATE User SET name=?, photo=?, last_update_time=? WHERE UUID=?', (name, photo, last_update_time, user_id))
        return result

    def ban_user(self, user_id, ban):
        result = self.deal_sql_request('UPDATE User SET ban=? WHERE UUID=?', (ban, user_id,))
        return result

    def load_all_user_extra_data(self, user_id):
        result = self.deal_sql_request('SELECT tmp FROM User WHERE UUID=?', (user_id,))
        if not result:
            return None
        result = json.loads(result[0][0])
        return result

    def load_user_extra_data(self, user_id, d_name):
        d = self.load_all_user_extra_data(user_id)
        if d and d_name in d:
            return d[d_name]
        return None

    def add_user_extra_data(self, user_id, d_name, d_value):
        d = self.load_all_user_extra_data(user_id)
        d[d_name] = d_value
        result = self.deal_sql_request('UPDATE User SET tmp=? WHERE UUID=?', (json.dumps(d), user_id))
        return result

    ### System Logs

    def load_system_logs(self):
        # logs = [{'time':'2020-01-01','status':'success' ,'text':'test'}]
        logs = []
        with open('data/system.log', 'r') as f:
            texts = f.readlines()[::-1]
            for text_row in texts:
                if text_row.startswith('*'):
                    logs.append({'time':'','status':'' ,'text':text_row[1:]})

        if len(logs)==0:
            logs = [{'time':'','status':'success' ,'text':'all good'}]
        elif len(logs)>10:
            logs = logs[:10]

        return logs

if __name__ == '__main__':
    db = database('data/chat.db',threading.Lock())
    data = db.load_chat_session_no_analyze()
    print(data)