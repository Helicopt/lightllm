import os
import json

EXEC_TYPE = os.environ.get('EXEC_TYPE', 'Debug')

# side_app settings
NUM_WORKERS = os.environ.get('NUM_WORKERS', 2)
SRV_NAME = os.environ.get('SRV_NAME', 'srv01')

# redis settings
REDIS_CONNSTR = os.environ.get(
    'REDIS_CONNSTR', 'localhost:6379,password=,ssl=False')

REDIS_DB_INDEX = os.environ.get('REDIS_DB_INDEX', 2)
REDIS_SESSION_DB_INDEX = os.environ.get('REDIS_SESSION_DB_INDEX', 4)


# message queue settings

MQ_TYPE = os.environ.get('MQ_TYPE', 'eventhub')
MQ_CONNSTR = os.environ.get(
    'MQ_CONNSTR', 'Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=;EntityPath=')

# outsourced settings

OUTSRC_ENABLED = os.environ.get('OUTSRC_ENABLED', 'True').lower() == 'true'
NON_CONSUMER = os.environ.get('NON_CONSUMER', 'False').lower() == 'true'

# message queue checkpoint settings

MQ_CHECKPOINT = os.environ.get(
    'MQ_CHECKPOINT', 'DefaultEndpointsProtocol=https;AccountName=')
MQ_CHECKPOINT_CONTAINER = os.environ.get('MQ_CHECKPOINT_CONTAINER', 'llmq')

global DBS_CERTIFICATE_CONNECT_STRING, DBS_CERTIFICATE_DB_NAME, DBS_CERTIFICATE_DB_CONTAINER


if EXEC_TYPE == 'Debug' and os.path.exists('credentials.json'):
    with open('credentials.json') as f:
        data = json.load(f)
        MQ_TYPE = data.get('mq_type', 'eventhub')
        MQ_CONNSTR = data['mq_connstr']
        # OUTSRC_ENABLED = data.get('outsrc_enabled', True)
        # NON_CONSUMER = data.get('non_consumer', True)
        MQ_CHECKPOINT = data.get('mq_checkpoint', '')
        MQ_CHECKPOINT_CONTAINER = data.get(
            'mq_checkpoint_container', 'llmq')
        DBS_CERTIFICATE_CONNECT_STRING = data['certificate_connect_string']
        DBS_CERTIFICATE_DB_NAME = data['db_name']
        DBS_CERTIFICATE_DB_CONTAINER = data['certificate_container']
else:
    DBS_CERTIFICATE_CONNECT_STRING = os.environ.get(
        'DBS_CERTIFICATE_CONNECT_STRING')
    DBS_CERTIFICATE_DB_NAME = os.environ.get('DBS_CERTIFICATE_DB_NAME')
    DBS_CERTIFICATE_DB_CONTAINER = os.environ.get(
        'DBS_CERTIFICATE_DB_CONTAINER')

SALT = os.environ.get('SALT', 'this_is_a_salt')

# auth settings

DEFAULT_AUTH = os.environ.get('DEFAULT_AUTH', 'this_is_default_auth')
DEBUG_TOKEN = 'bG9uZ2FjaGFpbjo='

# LLM
LLM_URL = 'http://127.0.0.1:9090/v1/chat/completions'
LLM_TYPE = 'codellama'
CONV_DB = './conv_db'

LLM = dict(
    url=LLM_URL,
    model=LLM_TYPE,
    max_tokens=2048,
)
