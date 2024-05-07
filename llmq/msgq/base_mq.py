class BaseMessageQueue:

    def __init__(self, conn_str, **kwargs):
        self.conn_str = conn_str
        self.kwargs = kwargs
        self._queue = None

    def init(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def send(self, message):
        raise NotImplementedError

    def receive(self, blocking=True):
        raise NotImplementedError

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
