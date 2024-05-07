from .base_mq import BaseMessageQueue
import warnings
try:
    from .eventhub import EventHubQueue
except ImportError:
    warnings.warn(
        "EventHubQueue is not available. Please install azure-eventhub package.")
    EventHubQueue = None


def get_mq(mq_type, conn_str, **kwargs) -> BaseMessageQueue:
    if mq_type == 'eventhub':
        ret_class = EventHubQueue
    else:
        ret_class = BaseMessageQueue
    return ret_class(conn_str, **kwargs)
