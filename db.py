"""
Create DB instance

"""

import pymysql,os
from dotenv import load_dotenv
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager

load_dotenv()

class DB:
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            host=os.getenv("MYSQL_HOST","localhost"),
            port=int(os.getenv("MYSQL_PORT",3306)),
            database=os.getenv("MYSQL_DATABASE","blog"),
            user=os.getenv("MYSQL_USER","root"),
            password=os.getenv("MYSQL_PASSWORD","root123"),
            maxconnections=5,
            mincached=2
        )

    @contextmanager
    def conn_cursor(self):
        conn = self.pool.connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetch_one(self, sql, params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    
    def fetch_all(self,sql,params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.fetchall()
        
    def insert(self,sql,params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.lastrowid
    
    def update(self,sql,params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.rowcount
        
    def delete(self,sql,params=None):
        with self.conn_cursor() as cursor:
            cursor.execute(sql,params or ())
            return cursor.rowcount
        
    def insert_many(self,sql,params_list):
        with self.conn_cursor() as cursor:
            cursor.executemany(sql,params_list)
            return cursor.rowcount
        

db = DB()