import logging

import pymysql
from pymysql.cursors import DictCursor

import hashlib
import logging

from dbutils.pooled_db import PooledDB

logger = logging.getLogger(__name__)


def md(obj):
    md5 = hashlib.md5()
    md5.update(str(obj).encode('utf-8'))
    return md5.hexdigest()


class BaseDBlUtils(object):
    _cache_pool = {}

    def __init__(self, **kwargs):
        conn = {**kwargs}
        if 'user' not in conn:
            conn['user'] = conn.pop('username')
        self._db_config = {**conn}
        self._pool = self._get_pool(**self._db_config)

    @classmethod
    def _connect_default(cls):

        return dict(
            # creator=pymysql,
            # cursorclass=DictCursor,
            charset='utf8',
            autocommit=True,
            maxcached=5,
            maxconnections=20,  # 连接池允许的最大连接数，0和None表示不限制连接数
            blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
            maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
            ping=7)

    @classmethod
    def _get_pool(cls, **kwargs):
        """
        @summary: 从连接池中取出连接
        @return PooledDB
        """
        connect = {**cls._connect_default()}
        connect.update(**kwargs)
        cache_key = md(tuple((_, connect[_]) for _ in sorted(connect))).encode()
        if cache_key not in cls._cache_pool:
            cls._cache_pool[cache_key] = PooledDB(**connect)
        return cls._cache_pool[cache_key]

    def query(self, sql, param=None):
        result = self._query(sql, param, fetch=True)
        return result

    def _conn_cursor(self, conn):
        return conn.cursor()

    def _query(self, sql, param=None, many=False, fetch=False):
        logger.debug('debug_query sql:%s param:%s many:%s fetch:%s', sql, param, many, fetch)
        _conn = self._get_conn()
        _cursor = None
        result = None
        try:
            _cursor = self._conn_cursor(_conn)
            if many:
                execute_func = _cursor.executemany
            else:
                execute_func = _cursor.execute
            if param:
                result = execute_func(sql, param)
            else:
                result = execute_func(sql)
            if fetch:
                result = _cursor.fetchall()
        finally:
            self._close(_conn, _cursor)
        return result

    def _get_conn(self):
        _conn = self._pool.connection()
        return _conn

    def _close(self, _conn, _cursor):
        try:
            if _cursor:
                _cursor.close()
                del _cursor
            if _conn:
                _conn.close()
                del _conn
        except Exception as e:
            logger.error('mysql_close_error e:{e}'.format(e=e))

    def execute(self, sql, param=None):
        return self._query(sql, param)

    def execute_many(self, sql, param=None):
        return self._query(sql, param, True)

    @staticmethod
    def gen_insert_duplicate_dict_params_sql(table_name, data, where):
        assert len(set(where) - set(data.keys())) == 0
        fields_list = list(data.keys())
        fields = ','.join('`{0}`'.format(field) for field in fields_list)
        values = ','.join('%({0})s'.format(field) for field in fields_list)
        update_fields_values = ','.join('`{0}`=VALUES(`{0}`)'.format(field) for field in set(fields_list) - set(where))
        insert_duplicate_dict_params_sql = """INSERT INTO {table_name} ({fields}) VALUES ({values}) ON DUPLICATE KEY UPDATE {update_fields_values}""".format(
            table_name=table_name,
            fields=fields,
            values=values,
            update_fields_values=update_fields_values,
        )
        return insert_duplicate_dict_params_sql

    def update(self, table_name, where, results):
        fields_list = results[0].keys() if isinstance(results, list) else results.keys()
        update_fields_values = ','.join(
            '`{0}`=%({0})s'.format(field) for field in set(fields_list) - set(where))
        where_fields_values = ' and '.join('`{0}`=%({0})s'.format(field) for field in where)
        update_sql = """update {table_name} set {update_fields_values} where {where_fields_values}""".format(
            table_name=table_name,
            where_fields_values=where_fields_values,
            update_fields_values=update_fields_values,
        )
        update_res = None
        try:
            if isinstance(results, list):
                update_res = self.execute_many(update_sql, param=results)
            else:
                update_res = self.execute(update_sql, param=results)
            logger.debug(
                'update_success '
                'table_name:{table_name} '
                'update_res:{update_res} '
                'result:{result}'.format(
                    table_name=table_name,
                    update_res=update_res,
                    result=results)
            )
        except Exception as e:
            logger.error(
                'update_error e:{e} table_name:{table_name} result:{result}'.format(
                    e=e, table_name=table_name, result=results))
        return update_res

    def insert_ignore(self, table_name, results, ignore=True):
        fields_list = results[0].keys() if isinstance(results, list) else results.keys()
        fields = ','.join('`{0}`'.format(field) for field in fields_list)
        values = ','.join('%({0})s'.format(field) for field in fields_list)
        insert_sql = """{insert} into {table_name} ({fields}) VALUES ({values})""".format(
            insert='insert ignore' if ignore else 'insert',
            table_name=table_name,
            fields=fields,
            values=values,
        )
        insert_res = None
        try:
            if isinstance(results, list):
                insert_res = self.execute_many(insert_sql, param=results)
            else:
                insert_res = self.execute(insert_sql, param=results)
            logger.debug(
                'insert_ignore_success '
                'table_name:{table_name} '
                'insert_res:{insert_res} '
                'result:{result}'.format(
                    table_name=table_name,
                    insert_res=insert_res,
                    result=len(results))
            )
        except Exception as e:
            logger.error(
                'insert_ignore_error e:{e} table_name:{table_name} result:{result}'.format(
                    e=e, table_name=table_name, result=results))
        return insert_res

    def insert(self, table_name, results):
        return self.insert_ignore(table_name, results, ignore=False)

    def insert_or_update(self, table_name, where, result):
        fields_list = result.keys()
        fields = ','.join('`{0}`'.format(field) for field in fields_list)
        values = ','.join('%({0})s'.format(field) for field in fields_list)
        update_fields_values = ','.join(
            '`{0}`=%({0})s'.format(field) for field in set(fields_list) - set(where))
        where_fields_values = ' and '.join('`{0}`=%({0})s'.format(field) for field in where)
        select_sql = """select {fields} from {table_name} where {where_fields_values}""".format(
            fields=fields,
            table_name=table_name,
            where_fields_values=where_fields_values,
        )
        update_sql = """update {table_name} set {update_fields_values} where {where_fields_values}""".format(
            table_name=table_name,
            where_fields_values=where_fields_values,
            update_fields_values=update_fields_values,
        )
        insert_sql = """insert into {table_name} ({fields}) VALUES ({values})""".format(
            table_name=table_name,
            fields=fields,
            values=values,
        )
        select_res = update_res = insert_res = None
        try:
            select_res = self.execute(select_sql, param=result)
            if select_res:
                update_res = self.execute(update_sql, param=result)
            else:
                insert_res = self.execute(insert_sql, param=result)
            logger.debug(
                'insert_or_update_success '
                'table_name:{table_name} '
                'select_res:{select_res} '
                'update_res:{update_res} '
                'insert_res:{insert_res} '
                'result:{result}'.format(
                    table_name=table_name,
                    select_res=select_res,
                    update_res=update_res,
                    insert_res=insert_res,
                    result=result)
            )
        except Exception as e:
            logger.error(
                'insert_or_update_error e:{e} table_name:{table_name} result:{result}'.format(
                    e=e, table_name=table_name, result=result))
        return select_res, insert_res, update_res


class MysqlUtils(BaseDBlUtils):
    @classmethod
    def _connect_default(self):
        return dict(
            creator=pymysql,
            cursorclass=DictCursor,
            charset='utf8',
            autocommit=True,
            maxcached=5,
            maxconnections=20,  # 连接池允许的最大连接数，0和None表示不限制连接数
            blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
            maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
            ping=7)
