from typing import Any
from .mailbox import Sender, Receiver


class Agent:
    id: Any
    sender: Sender
    receiver: Receiver
