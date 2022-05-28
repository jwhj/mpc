from typing import List
from circuit import Gate, Wire


class Not(Gate):
    def __init__(self, input: Wire, output: Wire) -> None:
        super().__init__()
        self.inputs = [input, input]
        self.output = output

    def evaluate(self, input_bits: List[int]) -> int:
        return ~input_bits[0]


class And(Gate):
    def __init__(self, in_0: Wire, in_1: Wire, out: Wire) -> None:
        super().__init__()
        self.inputs = [in_0, in_1]
        self.output = out

    def evaluate(self, input_bits: List[int]) -> int:
        return input_bits[0] & input_bits[1]


class Or(Gate):
    def __init__(self, in_0: Wire, in_1: Wire, out: Wire) -> None:
        super().__init__()
        self.inputs = [in_0, in_1]
        self.output = out

    def evaluate(self, input_bits: List[int]) -> int:
        return input_bits[0] | input_bits[1]


class Xor(Gate):
    def __init__(self, in_0: Wire, in_1: Wire, out: Wire) -> None:
        super().__init__()
        self.inputs = [in_0, in_1]
        self.output = out

    def evaluate(self, input_bits: List[int]) -> int:
        return input_bits[0] ^ input_bits[1]
