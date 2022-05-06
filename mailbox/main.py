from typing import Tuple, Any
from abc import ABC


class Sender(ABC):
    id: Any

    def send(self, id, msg):
        pass


class Receiver(ABC):
    id: Any

    def receive(self) -> Tuple[Any, Any]:
        pass
