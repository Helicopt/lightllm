from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.core import MatchConditions
from azure.cosmos.exceptions import CosmosAccessConditionFailedError
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
from loguru import logger
import traceback


from dbs.base_db import BaseDbConn


def require_connection(func):
    def wrapper(*args, conn=None, **kwargs):
        new_conn = False
        if conn is None:
            conn = args[0]._connect()
            new_conn = True
        if conn is None:
            return "Database connection error", 500
        try:
            ret = func(*args, conn=conn, **kwargs)
        except Exception as e:
            logger.error('\n'+traceback.format_exc())
            logger.error(str(e))
            ret = "Database op error", 500
        finally:
            if new_conn:
                args[0]._close(conn)
        return ret
    wrapper.__name__ = func.__name__
    return wrapper


class CosmosDbConn(BaseDbConn):

    class CosmosConnection:

        def __init__(self, client: CosmosClient, db_name: str) -> None:
            self.client = client
            self.database = self.client.get_database_client(db_name)

        def cursor(self):
            return self.database

        def close(self):
            pass

    def _connect(self):
        client = CosmosClient.from_connection_string(
            self.db_cfg['connection_string'], connection_timeout=5, retry_total=5)
        return CosmosDbConn.CosmosConnection(client, self.db_cfg['db_name'])

    def _close(self, conn: CosmosConnection):
        conn.close()


class CosmosDb(CosmosDbConn):

    @require_connection
    def insert(self, container, data, overwrite=False, conn=None):
        cursor = conn.cursor()
        container: ContainerProxy = cursor.get_container_client(container)
        if isinstance(data, dict):
            data = [data]
        cnt = 0
        for item in data:
            if overwrite:
                container.upsert_item(item)
                cnt += 1
            else:
                try:
                    container.upsert_item(
                        item, match_condition=MatchConditions.IfMissing)
                    cnt += 1
                except CosmosAccessConditionFailedError as e:
                    pass
        return cnt

    @require_connection
    def query(self, container, ids, conn=None):
        cursor = conn.cursor()
        container: ContainerProxy = cursor.get_container_client(container)
        exists = []
        grouped = {}
        for id, part in ids:
            grouped.setdefault(part, []).append(id)
        for part in grouped:
            if len(grouped[part]) < 3:
                for id in grouped[part]:
                    try:
                        item = container.read_item(
                            item=id, partition_key=part if part is not None else {})
                        exists.append(item)
                    except Exception as e:
                        exists.append(None)
            else:
                items = container.query_items(
                    query='SELECT * FROM c', partition_key=part if part is not None else {})
                all_items = {}
                for item in items:
                    all_items[item['id']] = item
                for id in grouped[part]:
                    exists.append(all_items.get(id, None))
        return exists

    @require_connection
    def existance(self, container, ids, conn=None):
        exists = self.query(container, ids, conn=conn)
        return [item is not None for item in exists]

    @require_connection
    def delete(self, container, ids, conn=None):
        cursor = conn.cursor()
        container: ContainerProxy = cursor.get_container_client(container)
        for id, part in ids:
            if part is None:
                part = {}
            container.delete_item(item=id, partition_key=part)
        return True
