from typing import Any
from comm import Sender, Receiver


class Agent:
    id: Any
    sender: Sender
    receiver: Receiver
