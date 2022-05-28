import imp
from typing import List, Optional
import queue


class Wire:
    input: Optional['Gate']
    outputs: List[Optional['Gate']]
    index: int

    def __init__(self) -> None:
        self.input = None
        self.outputs = []
        self.index = -1


class Gate:
    inputs: List[Wire]
    output: Wire
    index: int

    def __init__(self) -> None:
        self.inputs = []

    def evaluate(self, inputs_bits: List[int]) -> int:
        pass


class AndGate(Gate):
    def __init__(self, w_a, w_b, w_c) -> None:
        self.inputs = [w_a, w_b]
        self.output = w_c
        self.index = -1

    def evaluate(self, inputs_bits: List[int]) -> int:
        assert len(inputs_bits) == 2
        return inputs_bits[0] & inputs_bits[1]


class Circuit:
    gates: List[Gate]
    wires: List[Wire]
    inputs: List[Wire]
    outputs: List[Wire]

    # inputs代表每个输入bit对应到的wire，默认前若干个是a的bit，后面的是b的bit，inputs大小必须和input_bits大小相等（编号可以任意）

    def __init__(self) -> None:
        self.gates = []
        self.wires = []
        self.inputs = []
        self.outputs = []

    def evaluate(self, input_bits: List[int]):

        assert len(self.inputs) == len(input_bits)
        n = len(self.gates)
        m = len(self.wires)
        edges: List[List] = [[] for i in range(n)]
        in_deg: List[int] = [0] * n
        wire_ret: List[int] = [-1] * m
        for wire in self.wires:
            if wire.input is not None:
                for out_gate in wire.outputs:
                    if out_gate is not None:
                        edges[wire.input.index].append(out_gate.index)
                        in_deg[out_gate.index] += 1
        q = queue.Queue()
        for i in range(len(input_bits)):
            wire_ret[self.inputs[i].index] = input_bits[i]
            q.put(self.inputs[i])

        while not q.empty():
            wire = q.get()
            for out_gate in wire.outputs:
                if out_gate is not None:
                    in_deg[out_gate.index] -= 1
                    if in_deg[out_gate.index] == 0:
                        wire_ret[out_gate.output.index] = out_gate.evaluate(
                            [
                                wire_ret[input_wire.index]
                                for input_wire in out_gate.inputs
                            ]
                        )
                        q.put(out_gate.output)
        output_bits = [wire_ret[output_wire.index] for output_wire in self.outputs]

        return output_bits
