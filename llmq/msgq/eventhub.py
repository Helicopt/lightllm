from threading import Thread
from multiprocessing import Queue
from azure.eventhub import EventHubProducerClient, EventHubConsumerClient, EventData, PartitionContext
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
from loguru import logger
from .base_mq import BaseMessageQueue


class EventHubQueue(BaseMessageQueue):

    def __init__(self, conn_str, producer=True, consumer=False, checkpoint=None, **kwargs):
        super().__init__(conn_str, **kwargs)
        self._local_queue = Queue()
        self.producer = producer
        self.consumer = consumer
        self.checkpoint = checkpoint

    def _on_event(self, ctx: PartitionContext, eventdata: EventData):
        logger.info(
            f"Received event: partition {ctx.partition_id} offset {eventdata.offset}")
        ctx.update_checkpoint(eventdata)
        logger.info('updated ckpt')
        self._local_queue.put(eventdata.body_as_str())
        logger.info('added to q')

    def _start_to_receive(self):
        self._queue_receive.receive(
            on_event=self._on_event, start_position='-1')

    def init(self):
        if self.consumer:
            logger.info('Running in consumer mode.')
            if self.checkpoint:
                self.kwargs['checkpoint_store'] = BlobCheckpointStore.from_connection_string(
                    *self.checkpoint)
            self._queue_receive = EventHubConsumerClient.from_connection_string(
                self.conn_str, consumer_group='$Default', **self.kwargs)
            self.p = Thread(target=self._start_to_receive)
            self.p.start()

    def __del__(self):
        # self.p.join()
        # self.p.close()
        if self.consumer:
            self._queue_receive.close()

    def connect(self):
        if self.producer:
            self._queue_send = EventHubProducerClient.from_connection_string(
                self.conn_str, **self.kwargs)

    def disconnect(self):
        if self.producer:
            self._queue_send.close()

    def send(self, message):
        if not self.producer:
            raise Exception("This queue is not a producer.")
        return self._queue_send.send_event(EventData(message))

    def receive(self, blocking=True):
        if not self.consumer:
            raise Exception("This queue is not a consumer.")
        return self._local_queue.get() if blocking else self._local_queue.get_nowait()
