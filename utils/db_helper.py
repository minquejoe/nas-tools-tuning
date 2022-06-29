import os
import threading

import log
from config import Config
from utils.functions import singleton
from utils.db_pool import DBPool

lock = threading.Lock()


@singleton
class DBHelper:
    __connection = None
    __db_path = None
    __pools = None

    def __init__(self):
        self.init_config()
        self.__init_tables()

    def init_config(self):
        config = Config()
        config_path = config.get_config_path()
        if not config_path:
            log.console("【ERROR】NASTOOL_CONFIG 环境变量未设置，程序无法工作，正在退出...")
            quit()
        self.__db_path = os.path.join(os.path.dirname(config_path), 'user.db')
        self.__pools = DBPool(
            max_active=5, max_wait=20, init_size=5, db_type="SQLite3",
            **{'database': self.__db_path, 'check_same_thread': False})

    def __init_tables(self):
        conn = self.__pools.get()
        cursor = conn.cursor()
        try:
            # 资源搜索结果表
            cursor.execute('''CREATE TABLE IF NOT EXISTS SEARCH_RESULT_INFO
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   TORRENT_NAME    TEXT,
                                   ENCLOSURE    TEXT,
                                   DESCRIPTION    TEXT,
                                   TYPE TEXT,
                                   TITLE    TEXT,
                                   YEAR    TEXT,
                                   SEASON    TEXT,
                                   EPISODE    TEXT,
                                   ES_STRING    TEXT,
                                   VOTE    TEXT,
                                   IMAGE    TEXT,
                                   POSTER   TEXT,
                                   TMDBID   TEXT,
                                   OVERVIEW    TEXT,
                                   RES_TYPE    TEXT,
                                   RES_ORDER    TEXT,
                                   SIZE    INTEGER,
                                   SEEDERS    INTEGER,
                                   PEERS    INTEGER,                   
                                   SITE    TEXT,
                                   SITE_ORDER    TEXT,
                                   PAGEURL    TEXT,
                                   OTHERINFO    TEXT,
                                   UPLOAD_VOLUME_FACTOR REAL,
                                   DOWNLOAD_VOLUME_FACTOR REAL,
                                   NOTE     TEXT);''')

            # RSS下载记录表
            cursor.execute('''CREATE TABLE IF NOT EXISTS RSS_TORRENTS
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   TORRENT_NAME    TEXT,
                                   ENCLOSURE    TEXT,
                                   TYPE TEXT,
                                   TITLE    TEXT,
                                   YEAR    TEXT,
                                   SEASON    TEXT,
                                   EPISODE    TEXT);''')
            cursor.execute(
                '''CREATE INDEX IF NOT EXISTS INDX_RSS_TORRENTS_NAME ON RSS_TORRENTS (TITLE, YEAR, SEASON, EPISODE);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_RSS_TORRENTS_URL ON RSS_TORRENTS (ENCLOSURE);''')
            # 电影订阅表
            # STATE: D-队列中 S-正在检索 R-正在订阅 F-完成
            cursor.execute('''CREATE TABLE IF NOT EXISTS RSS_MOVIES
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   NAME    TEXT,
                                   YEAR    TEXT,
                                   TMDBID   TEXT,
                                   IMAGE    TEXT,
                                   DESC    TEXT,
                                   STATE    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_RSS_MOVIES_NAME ON RSS_MOVIES(NAME);''')
            # 电视剧订阅表
            # STATE: D-队列中 S-正在检索 R-正在订阅 F-完成
            cursor.execute('''CREATE TABLE IF NOT EXISTS RSS_TVS
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   NAME    TEXT,
                                   YEAR    TEXT,
                                   SEASON    TEXT,
                                   TMDBID   TEXT,
                                   IMAGE    TEXT,
                                   DESC    TEXT,
                                   TOTAL    INTEGER,
                                   LACK    INTEGER,
                                   STATE    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_RSS_TVS_NAME ON RSS_TVS(NAME);''')
            # 电视剧订阅剧集明细
            cursor.execute('''CREATE TABLE IF NOT EXISTS RSS_TV_EPISODES
                                               (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                               RSSID    TEXT,
                                               EPISODES    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_RSS_TV_EPISODES_RSSID ON RSS_TV_EPISODES (RSSID);''')
            # 豆瓣关注信息表
            cursor.execute('''CREATE TABLE IF NOT EXISTS DOUBAN_MEDIAS
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   NAME    TEXT,
                                   YEAR    TEXT,
                                   TYPE    TEXT,
                                   RATING   TEXT,
                                   IMAGE    TEXT,
                                   STATE    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_DOUBAN_MEDIAS_NAME ON DOUBAN_MEDIAS (NAME, YEAR);''')
            # 识别转移历史记录表
            cursor.execute('''CREATE TABLE IF NOT EXISTS TRANSFER_HISTORY
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   SOURCE    TEXT,
                                   MODE    TEXT,
                                   TYPE    TEXT,
                                   FILE_PATH    TEXT,
                                   FILE_NAME    TEXT,
                                   TITLE   TEXT,
                                   CATEGORY   TEXT,
                                   YEAR    TEXT,
                                   SE    TEXT,
                                   DEST    TEXT,
                                   DATE    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_HISTORY_PATH ON TRANSFER_HISTORY (FILE_PATH);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_HISTORY_NAME ON TRANSFER_HISTORY (FILE_NAME);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_HISTORY_TITLE ON TRANSFER_HISTORY (TITLE);''')
            # 无法识别的文件列表
            # STATE N-未处理 Y-已处理
            cursor.execute('''CREATE TABLE IF NOT EXISTS TRANSFER_UNKNOWN
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   PATH    TEXT,
                                   DEST    TEXT,
                                   STATE    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_UNKNOWN ON TRANSFER_UNKNOWN (PATH);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_UNKNOWN_STATE ON TRANSFER_UNKNOWN (STATE);''')
            # 识别黑名单
            cursor.execute('''CREATE TABLE IF NOT EXISTS TRANSFER_BLACKLIST
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   PATH    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_TRANSFER_BLACKLIST ON TRANSFER_BLACKLIST (PATH);''')
            # 站点配置表
            cursor.execute('''CREATE TABLE IF NOT EXISTS CONFIG_SITE
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   NAME    TEXT,
                                   PRI    TEXT,
                                   RSSURL   TEXT,
                                   SIGNURL  TEXT,
                                   COOKIE   TEXT,
                                   INCLUDE  TEXT,
                                   EXCLUDE  TEXT,
                                   SIZE    TEXT,
                                   NOTE    TEXT);''')
            # 搜索过滤规则表
            cursor.execute('''CREATE TABLE IF NOT EXISTS CONFIG_SEARCH_RULE
                                   (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                   INCLUDE  TEXT,
                                   EXCLUDE  TEXT,
                                   SIZE    TEXT,
                                   NOTE    TEXT);''')
            # RSS全局规则表
            cursor.execute('''CREATE TABLE IF NOT EXISTS CONFIG_RSS_RULE
                                               (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                               NOTE    TEXT);''')
            # 目录同步记录表
            cursor.execute('''CREATE TABLE IF NOT EXISTS SYNC_HISTORY
                                               (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                               PATH    TEXT,
                                               SRC    TEXT,
                                               DEST    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_SYNC_HISTORY ON SYNC_HISTORY (PATH);''')

            # 用户表
            cursor.execute('''CREATE TABLE IF NOT EXISTS CONFIG_USERS
                                                           (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                                           NAME    TEXT,
                                                           PASSWORD    TEXT,
                                                           PRIS    TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_CONFIG_USERS ON CONFIG_USERS (NAME);''')

            # 消息中心
            cursor.execute('''CREATE TABLE IF NOT EXISTS MESSAGES
                                                           (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                                           LEVEL    TEXT,
                                                           TITLE    TEXT,
                                                           CONTENT    TEXT,
                                                           DATE     TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_MESSAGES_DATE ON MESSAGES (DATE);''')

            # 站点流量历史
            cursor.execute('''CREATE TABLE IF NOT EXISTS SITE_STATISTICS_HISTORY
                                                           (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                                           SITE    TEXT,
                                                           DATE    TEXT,
                                                           USER_LEVEL    TEXT,
                                                           UPLOAD    TEXT,
                                                           DOWNLOAD     TEXT,
                                                           RATIO     TEXT,
                                                           SEEDING     INTEGER default 0,
                                                           LEECHING     INTEGER default 0,
                                                           SEEDING_SIZE     INTEGER default 0,
                                                           BONUS     REAL default 0.0,
                                                           URL     TEXT);''')

            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_SITE_STATISTICS_HISTORY_DS ON SITE_STATISTICS_HISTORY (DATE, URL);''')

            # 实时站点数据
            cursor.execute('''CREATE TABLE IF NOT EXISTS SITE_USER_STATISTICS
                                                           (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                                           SITE    TEXT,
                                                           USERNAME    TEXT,
                                                           USER_LEVEL    TEXT,
                                                           JOIN_AT    TEXT,
                                                           UPDATE_AT    TEXT,
                                                           UPLOAD    INTEGER,
                                                           DOWNLOAD     INTEGER,
                                                           RATIO     REAL,
                                                           SEEDING     INTEGER,
                                                           LEECHING     INTEGER,
                                                           SEEDING_SIZE     INTEGER,
                                                           BONUS     REAL,
                                                           URL     TEXT);''')
            cursor.execute(
                '''CREATE INDEX IF NOT EXISTS INDX_SITE_USER_STATISTICS_URL ON SITE_USER_STATISTICS (URL);''')
            cursor.execute(
                '''CREATE INDEX IF NOT EXISTS INDX_SITE_USER_STATISTICS_SITE ON SITE_USER_STATISTICS (SITE);''')

            # 下载历史
            cursor.execute('''CREATE TABLE IF NOT EXISTS DOWNLOAD_HISTORY
                                                           (ID INTEGER PRIMARY KEY AUTOINCREMENT     NOT NULL,
                                                           TITLE    TEXT,
                                                           YEAR    TEXT,
                                                           TYPE    TEXT,
                                                           TMDBID     TEXT,
                                                           VOTE     TEXT,
                                                           POSTER     TEXT,
                                                           OVERVIEW    TEXT,
                                                           TORRENT     TEXT,
                                                           ENCLOSURE     TEXT,
                                                           SITE     TEXT,
                                                           DESC     TEXT,
                                                           DATE     TEXT);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_DOWNLOAD_HISTORY_DATE ON DOWNLOAD_HISTORY (DATE);''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS INDX_DOWNLOAD_HISTORY_TITLE ON DOWNLOAD_HISTORY (TITLE);''')

            # 提交
            conn.commit()

        except Exception as e:
            log.error(f"【DB】创建数据库错误：{e}")
        finally:
            cursor.close()
            self.__pools.free(conn)

    def excute(self, sql, data):
        if not sql:
            return False
        conn = self.__pools.get()
        cursor = conn.cursor()
        try:
            if data:
                cursor.execute(sql, data)
            else:
                cursor.execute(sql)
            conn.commit()
        except Exception as e:
            log.error(f"【DB】执行SQL出错：sql:{sql}; parameters:{data}; {e}")
            return False
        finally:
            cursor.close()
            self.__pools.free(conn)
        return True

    def excute_many(self, sql, data_list):
        if not sql or not data_list:
            return False
        conn = self.__pools.get()
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, data_list)
            conn.commit()
        except Exception as e:
            log.error(f"【DB】执行SQL出错：sql:{sql}; {e}")
            return False
        finally:
            cursor.close()
            self.__pools.free(conn)
        return True

    def select(self, sql, data):
        if not sql:
            return False
        conn = self.__pools.get()
        cursor = conn.cursor()
        try:
            if data:
                res = cursor.execute(sql, data)
            else:
                res = cursor.execute(sql)
            ret = res.fetchall()
        except Exception as e:
            log.error(f"【DB】执行SQL出错：sql:{sql}; parameters:{data}; {e}")
            return []
        finally:
            cursor.close()
            self.__pools.free(conn)
        return ret


def select_by_sql(sql, data=None):
    """
    执行查询
    :param sql: 查询的SQL语句
    :param data: 数据，需为列表或者元祖
    :return: 查询结果的二级列表
    """
    return DBHelper().select(sql, data)


def update_by_sql(sql, data=None):
    """
    执行更新或删除
    :param sql: SQL语句
    :param data: 数据，需为列表或者元祖
    :return: 执行状态
    """
    return DBHelper().excute(sql, data)


def update_by_sql_batch(sql, data_list):
    """
    执行更新或删除
    :param sql: 批量更新SQL语句
    :param data_list: 数据列表
    :return: 执行状态
    """
    return DBHelper().excute_many(sql, data_list)
