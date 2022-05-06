from typing import List
from agent import Agent


def OT_Alice(agent: Agent, bob_id, messages: List[int]):
    assert len(messages) == 2
    pass


def OT_Bob(agent: Agent, alice_id, index: int):
    assert index in [0, 1]
    pass
