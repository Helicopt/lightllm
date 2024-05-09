import requests
import json
from loguru import logger
import pickle
import uuid
import os

LLM_URL = 'http://127.0.0.1:9090/v1/chat/completions'
LLM_TYPE = 'codellama'
CONV_DB = './conv_db'


class InfohubConversation:

    def __init__(self, llm=dict(url=LLM_URL, model=LLM_TYPE), conv_db=CONV_DB, conv_id=None):
        if conv_id is not None and os.path.exists(conv_id):
            conv_id = os.path.basename(conv_id)
        self.conv_db = conv_db
        os.makedirs(self.conv_db, exist_ok=True)
        self.llm = llm
        if conv_id is not None:
            self.load_conv(conv_id)
        else:
            self.new_conv()

    def load_conv(self, conv_id):
        if os.path.exists(f'{self.conv_db}/{conv_id}'):
            with open(f'{self.conv_db}/{conv_id}', 'rb') as f:
                self.conv = pickle.load(f)
                self.conv_id = conv_id
        else:
            print(
                f"Conversation {conv_id} not found. Creating new conversation.")
            self.new_conv(conv_id)

    def new_conv(self, conv_id=None):
        self.conv = [self.system_message()]
        self.conv_id = self.gen_conv_id() if conv_id is None else conv_id
        self.save_conv()

    def save_conv(self):
        os.makedirs(self.conv_db, exist_ok=True)
        with open(f'{self.conv_db}/{self.conv_id}', 'wb') as f:
            pickle.dump(self.conv, f)

    @staticmethod
    def gen_conv_id():
        return str(uuid.uuid4())

    def set_system_msg(self, message):
        self.conv[0] = self.system_message(message)
        self.save_conv()

    def system_message(self, message=""):
        return {"role": "system", "content": message}

    def user_message(self, message=""):
        return {"role": "user", "content": message}

    def assistant_message(self, message="", origin=None):
        return {"role": "assistant", "content": message, "origin": origin}

    def push(self, message, sync=False):
        if self.conv[-1]['role'] == 'user':
            self.ask()
        self.conv.append(self.user_message(message))
        self.save_conv()
        ret = self.ask()
        if ret:
            return
        if sync:
            self.sync()

    def ask(self):
        url = self.llm['url']
        params = {}
        params.update(self.llm)
        params.pop('url')
        content_length = 0
        for one in self.conv:
            content_length += len(one['content'])
        logger.info(f'context content length: {content_length}')
        ret = requests.post(url, json={
            "messages": [{'role': one['role'], 'content': one['content']} for one in self.conv], ** params
        })
        if ret.status_code != 200:
            return False
        sess = ret.json()
        self.conv.append(self.assistant_message(
            sess['choices'][0]['message']['content'], origin=sess))
        self.save_conv()
        return True

    def sync(self):
        print(self.playback())

    def playback(self):
        return '\n========================\n'.join([f"[{m['role'].capitalize()}]\n {m['content']}" for m in self.conv])

    def last_message(self):
        return self.conv[-1]

    def last_answer(self):
        return self.conv[-1]['content']


def max_width(text, width):
    for i in range(0, len(text), width):
        yield text[i:i+width]


if __name__ == '__main__':

    import sys
    conv_id = sys.argv[1] if len(sys.argv) > 1 else None

    conv = InfohubConversation(llm=dict(
        url=LLM_URL,
        model=LLM_TYPE,
        max_tokens=512,
    ), conv_id=conv_id)
    conv.sync()
    while True:
        q = input('> ')
        conv.push(q)
        for o in conv.last_answer().split('\n'):
            for o_ in max_width(o, 120):
                print(f'||> {o_}')
