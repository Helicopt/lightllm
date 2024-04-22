from simple_client import InfohubConversation
import multiprocessing as mp
import time
from loguru import logger
import re

LLM_URL = 'http://127.0.0.1:8080/v1/chat/completions'
LLM_TYPE = 'codellama'
CONV_DB = './conv_db'


class BaseModule:

    def __init__(self) -> None:
        self.users = []
        self.p = mp.Process(target=self._main)
        self.bgs = []

    def link(self, joint):
        self.users.append(joint)

    def start(self):
        self.p.start()

    def notify(self, user, message):
        p = mp.Process(target=self.handle_event,
                       args=(user, message,), daemon=True)
        p.start()
        self.bgs.append(p)

    def push(self, msg):
        for user in self.users:
            user.push(msg)

    def handle_event(self, user, msg):
        if re.fullmatch(r'([Cc]lean|[Rr]estart|[Cc]all-[Rr]epair)[\s]+camera[\s]+[\d]+[.!]*', msg.strip()):
            logger.info(
                f"Module {self.__class__.__name__} received message: {msg}")
            time.sleep(5)
            self.push('[%s] {{%s}} is resolved.' %
                      (self.__class__.__name__, msg))
            logger.info(
                f"Module {self.__class__.__name__} resolved message: {msg}")
        else:
            logger.info(
                f"Module {self.__class__.__name__} ignored message: {msg}")

    def main(self):
        import random
        if random.randint(1, 20) == 1:
            kind = random.randint(1, 3)
            broken_id = random.randint(1, 10)
            if kind == 1:
                logger.info('[%s] camera (%d) is down!' %
                            (self.__class__.__name__, broken_id))
                self.push('[Error] camera (%d) is down!' % broken_id)
            if kind == 2:
                logger.info('[%s] camera (%d) outputs 0 objects for the past 1 hour!' %
                            (self.__class__.__name__, broken_id))
                self.push(
                    'camera (%d) outputs 0 objects for the past 1 hour!' % broken_id)
            if kind == 3:
                logger.info('[%s] could not resolve ip address 10.6.7.13 of camera (%d)' %
                            (self.__class__.__name__, broken_id))
                self.push(
                    'could not resolve ip address 10.6.7.13 of camera (%d)' % broken_id)

    def check_bgs(self):
        new_bgs = []
        for i in range(len(self.bgs)):
            if not self.bgs[i].is_alive():
                self.bgs[i].join()
            else:
                new_bgs.append(self.bgs[i])
        self.bgs = new_bgs

    def _main(self):
        while True:
            self.main()
            self.check_bgs()
            time.sleep(1)


class JointUser:

    def __init__(self, modules):
        self.modules = modules
        self.queue = mp.Queue()
        for module in self.modules:
            assert isinstance(module, BaseModule)
            module.link(self)

    def interact(self, conv: InfohubConversation):
        for module in self.modules:
            module.start()
        while True:
            message = ''
            while not self.queue.empty() and len(message) < 256:
                message += self.queue.get()
            if message:
                conv.push(message)
                ans = conv.last_answer()
                for module in self.modules:
                    module.notify(self, ans)

    def push(self, message):
        self.queue.put(message)


if __name__ == '__main__':
    conv = InfohubConversation(llm=dict(
        url=LLM_URL,
        model=LLM_TYPE,
        max_tokens=512,
    ), conv_id='event_stream')
    system_msg = 'you are a camera system manager. there will be some notifications in the format `camera (x) some_error_info`, once you receive it, you should analyse what the problem (but do not output the details of your thinking) is and resolve it by runing one or more commands (your output should only be a command). you can use the commands `restart camera [x]` to restart the camera, use `clean camera [x]` to clean the camera, use `call-repair camera [x]` for other hardware or network issues. do not output useless information when use the commands. when the commands are executed and return some results, you should respond by just `ok`'
    conv.set_system_msg(system_msg)
    system_user = JointUser(modules=[BaseModule()])
    system_user.interact(conv)
