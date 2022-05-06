from typing import Dict, Any
from queue import Queue
from .main import Sender, Receiver

queues: Dict[Any, Queue] = {}


class SenderThread(Sender):
    def __init__(self, id):
        self.id = id

    def send(self, id, msg):
        assert id in queues, f"agent with id {id} not found"
        queues[id].put((self.id, msg))


class ReceiverThread(Receiver):
    def __init__(self, id) -> None:
        self.id = id
        if id not in queues:
            queues[id] = Queue()

    def receive(self):
        return queues[self.id].get()
