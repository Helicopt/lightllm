from flask import Flask
import os
from loguru import logger
from multiprocessing import Process
import json
import sys
import traceback

from env import EXEC_TYPE, NUM_WORKERS, SRV_NAME, MQ_TYPE, MQ_CONNSTR, NON_CONSUMER, MQ_CHECKPOINT, MQ_CHECKPOINT_CONTAINER, DBS_CERTIFICATE_CONNECT_STRING, DBS_CERTIFICATE_DB_NAME, LLM
from msgq import get_mq
from dbs.cosmos import CosmosDb
from simple_client import InfohubConversation

# EXEC_TYPE = os.environ.get('EXEC_TYPE', 'Deploy')
# NUM_WORKERS = os.environ.get('NUM_WORKERS', 2)
# SRV_NAME = os.environ.get('SRV_NAME', 'srv01')


# set logger format to | level | [worker_id] name - message
# retention: 7 days, rotation: 1 day
logger.remove()
logger.add(
    sys.stderr, format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <level>{level:<8}</level> | <cyan>{module}</>:<cyan>{function}</>:<cyan>{line}</> - <level>{message}</>', level='INFO', filter=lambda record: not record['extra'])
formatter_with_worker = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <level>{level:<8}</level> | <blue>[{extra[worker_id]}]</> <cyan>{module}</>:<cyan>{function}</>:<cyan>{line}</> - <level>{message}</>'
logger.add(
    sys.stderr, format=formatter_with_worker, level='INFO', filter=lambda record: 'worker_id' in record['extra'])
logger.add('infohub-bg.log',
           format=formatter_with_worker, level='INFO', rotation='1 day', retention='7 days', filter=lambda record: 'worker_id' in record['extra'])
logger.info(f'EXEC_TYPE={EXEC_TYPE}, MQ_TYPE={MQ_TYPE}')


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'this_is_sideapp_secret_key')


@app.route("/")
def hello():
    return "This is a default page of infohub bg servers."


def main(rank: int = 0):
    worker_id = f'{SRV_NAME}:{rank}'
    wlogger = logger.bind(worker_id=worker_id)
    db = CosmosDb({'connection_string': DBS_CERTIFICATE_CONNECT_STRING,
                  'db_name': DBS_CERTIFICATE_DB_NAME})
    mq = get_mq(MQ_TYPE, MQ_CONNSTR,
                consumer=not NON_CONSUMER, checkpoint=(None if NON_CONSUMER or MQ_CHECKPOINT.strip() == '' else MQ_CHECKPOINT, MQ_CHECKPOINT_CONTAINER))
    mq.init()
    while True:
        # get an operation from the queue
        wlogger.info('Waiting for operation...')
        with mq:
            msg = mq.receive(blocking=True)
            msg = json.loads(msg)
        dialogId = msg['DialogId']
        if 'cmd' in msg:
            cmd = msg['cmd']
            if cmd == 'clear':
                chat = InfohubConversation(LLM, conv_id=dialogId)
                chat.new_conv(dialogId)
                if 'system' in msg:
                    chat.set_system_msg(msg['system'])
                conn = db._connect()
                cursor = conn.cursor()
                c = cursor.get_container_client('llm')
                all_logs = list(c.query_items(
                    query='SELECT * FROM c',
                    partition_key=dialogId,
                ))
                for log in all_logs:
                    c.delete_item(log, partition_key=dialogId)
                conn.close()
                continue
            continue
        seq = msg['seq']
        content = msg['content']
        ask = content
        chat = InfohubConversation(LLM, conv_id=dialogId)
        if 'system' in msg:
            chat.set_system_msg(msg['system'])
        logger.info('create cosmos log')
        conn = db._connect()
        cursor = conn.cursor()
        c = cursor.get_container_client('llm')
        c.upsert_item({
            'id': dialogId + '-' + str(seq),
            'DialogId': dialogId,
            'ask': ask,
            'answer': '',
        })
        chat.push(content)
        content = chat.last_answer()
        logger.info('write back cosmos log')
        c.upsert_item({
            'id': dialogId + '-' + str(seq),
            'DialogId': dialogId,
            'ask': ask,
            'answer': content,
        })
        conn.close()
        logger.info(f'[{worker_id}] Inserted {dialogId}-{seq} into cosmos db.')


bgps = []
for i in range(NUM_WORKERS):
    bgps.append(Process(target=main, args=(i, )))
    bgps[-1].start()

# This file must not be run directly!!!!!!!!!!!!!!!!!!!!!!!!!!!!
