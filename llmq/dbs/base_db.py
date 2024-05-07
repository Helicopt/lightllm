from abc import ABC


class BaseDbConn(ABC):
    '''
    This class defines the logics of how to connect and close a database connection.
    '''

    def __init__(self, db_cfg):
        self.db_cfg = db_cfg
        self.is_connected = False

    def connect(self):
        '''
        generate a connection object and return it, mark the connection status as connected
        '''
        if not self.is_connected:
            conn = self._connect()
            self.is_connected = conn is not None
            self.conn = conn
        return self.is_connected

    def close(self):
        '''
        close the last connection object and mark the connection status as disconnected
        '''
        if self.is_connected:
            self._close(self.conn)
            self.is_connected = False
            self.conn = None

    def _connect(self):
        '''
        should return a connection object
        '''
        raise NotImplementedError

    def _close(self, conn):
        '''
        should close the connection object
        '''
        raise NotImplementedError
