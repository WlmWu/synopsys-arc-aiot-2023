import sqlite3
from datetime import datetime
import pytz
from pathlib import Path

from .config import DATABASE_PATH, DB_NAME, TABLE_NAME_EMPLOYEE, TABLE_NAME_TIMESTAMP, TIME_ZONE


class _Database():
    def __init__(self, dbpath=Path(DATABASE_PATH) / DB_NAME) -> None:
        self._conn = sqlite3.connect(dbpath, check_same_thread=False)
        self._cursor = self._conn.cursor()

    def execute(self, execute: str):
        self._cursor.execute(execute)
        self._conn.commit()

    
    def insert_new(self, table_name: str, execute: dict):
        sql = \
        f"""
        INSERT INTO {table_name}
        {tuple((execute.keys()))}
        VALUES {tuple(execute.values())}
        """
        self.execute(sql)

    def get_all_data(self, table_name: str) -> list:
        sql = \
        f"""
        SELECT *
        FROM {table_name}
        """
        data = self._cursor.execute(sql)
        
        col_names = [description[0] for description in data.description]
        res = [dict(zip(col_names, row)) for row in data]

        return res
    
    def select_one(self, table_name: str, conditions: dict) -> dict:
        sql = \
        f"""
        SELECT * 
        FROM {table_name}
        WHERE {' AND '.join([f"{k} = '{v}'" for k, v in conditions.items()])}
        """
        data = self._cursor.execute(sql)
        col_names = [description[0] for description in data.description]

        try: 
            res = list(data)[0]
        except:
            res = ''

        return dict(zip(col_names,res))
    
    def update_one(self, table_name: str, conditions: dict, update_content: dict):
        sql = \
        f"""
        UPDATE {table_name} 
        SET {', '.join([f"{k} = '{v}'" for k, v in update_content.items()])} 
        WHERE {' AND '.join([f"{k} = '{v}'" for k, v in conditions.items()])}
        """

        self.execute(sql)


class DBMananger():
    def __init__(self, dbpath=Path(DATABASE_PATH) / DB_NAME) -> None:
        self._db = _Database(dbpath)

    def key_error_handler(self, keys: list, dic: dict, func_name: str):
        try:
            [dic[k] for k in keys]
        except KeyError:
            msg = ' and '.join(list(f'"{k}"' for k in keys))
            print(f'KeyError: {func_name} should have {msg}')
            return False
        return True

    def enroll_new(self, new_employee: dict):
        keys = ['name', 'email', 'feature_path']
        if self.key_error_handler(keys, new_employee, "New employees") is False:
            return
        
        self._db.insert_new(TABLE_NAME_EMPLOYEE, new_employee)

    
    def clock_in(self, timestamp: dict):
        keys = ['eid', 'time_in']
        if self.key_error_handler(keys, timestamp, "Clocking in") is False:
            return
        
        self._db.insert_new(TABLE_NAME_TIMESTAMP, timestamp)

    def clock_out(self, timestamp: dict):
        keys = ['eid', 'time_in', 'time_out']
        if self.key_error_handler(keys, timestamp, "Clocking out") is False:
            return
        
        t_out = timestamp.pop('time_out')
        employee = self._db.select_one(TABLE_NAME_TIMESTAMP, timestamp)
        self._db.update_one(TABLE_NAME_TIMESTAMP, employee, {'time_out': t_out})

    def get_all_enrolled(self) -> dict:
        return self._db.get_all_data(TABLE_NAME_EMPLOYEE)
    
    def get_all_timestamps(self) -> dict:
        return self._db.get_all_data(TABLE_NAME_TIMESTAMP)
    
    def get_new_eid(self) -> int:
        sql = \
        f"""
        SELECT eid
        FROM {TABLE_NAME_EMPLOYEE}
        ORDER BY eid DESC LIMIT 1
        """
        self._db._cursor.execute(sql)

        return list(self._db._cursor)[0][0] + 1
    
    def get_employee(self, eid: int) -> dict:
        return self._db.select_one(TABLE_NAME_EMPLOYEE, dict(EID=eid))
        


if __name__ == '__main__':
    t1 = \
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME_EMPLOYEE} (
        EID INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        feature_path TEXT
    );
    """
    t2 = \
    f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME_TIMESTAMP} (
        EID INTEGER,
        time_in TEXT,
        time_out TEXT,
        FOREIGN KEY (EID) REFERENCES {TABLE_NAME_EMPLOYEE}(EID) 
    );
    """
    current_time = lambda: datetime.now(pytz.timezone(TIME_ZONE)).strftime("%Y-%m-%d %H:%M:%S")

    db = _Database()
    # db.execute(t1)
    # db.execute(t2)
    # insert1 = {'name': 'test', 'email': 'test@nycu.edu', 'feature_path': './'}
    # db.insert_new(TABLE_NAME_EMPLOYEE, insert1)
    # insert2 = {'eid': 1, 'time_in': current_time(), 'time_out': current_time()}
    # db.insert_new(TABLE_NAME_TIMESTAMP, insert2)
    # print(db.get_all_data(TABLE_NAME_EMPLOYEE))
    # print(db.select_one(TABLE_NAME_EMPLOYEE, {'eid': 1, 'name': 'ttest'}))

    dbm = DBMananger()
    # print(dbm.get_all_timestamps())
    # dbm.enroll_new({'name': 'test3', 'feature_path': '../.'})
    # dbm.clock_in({'eid': 2, 'time_in': current_time(), 'time_out': current_time()})
    # dbm.clock_out({'eid': 1, 'time_in': '2023-05-13 04:35:56', 'time_out': current_time()})


