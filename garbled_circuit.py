from typing import List, Any
from agent import Agent
from circuit import Circuit


class GarbledCircuitProtocol:
    alice_id: Any
    bob_id: Any
    circuit: Circuit
    n_Alice_bits: int
    n_Bob_bits: int

    def alice(
        agent: Agent,
        input_bits: List[int],
    ):
        pass

    def bob(
        agent: Agent,
        input_bits: List[int],
    ):
        pass
