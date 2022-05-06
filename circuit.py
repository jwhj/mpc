from typing import List, Optional


class Wire:
    input: Optional['Gate']
    outputs: List[Optional['Gate']]

    def __init__(self) -> None:
        self.outputs = []


class Gate:
    inputs: List[Wire]
    output: Wire

    def __init__(self) -> None:
        self.inputs = []

    def evaluate(self, inputs_bits: List[int]) -> int:
        pass


class Circuit:
    gates: List[Gate]
    wires: List[Wire]
    inputs: List[Wire]
    outputs: List[Wire]

    def __init__(self) -> None:
        self.gates = []
        self.inputs = []
        self.outputs = []

    def evaluate(self, input_bits: List[int]):
        pass
