from typing import List, Optional
import queue
import sys


class Wire:
    input: Optional['Gate']
    outputs: List[Optional['Gate']]
    index: int

    def __init__(self) -> None:
        self.input = None
        self.outputs = []
        self.index = None


class Gate:
    inputs: List[Wire]
    output: Wire
    index: int

    def __init__(self) -> None:
        self.inputs = []
        self.index = None

    def evaluate(self, input_bits: List[int]) -> int:
        pass


class AndGate(Gate):
    def __init__(self, w_a, w_b, w_c) -> None:
        self.inputs = [w_a, w_b]
        self.output = w_c
        self.index = -1

    def evaluate(self, input_bits: List[int]) -> int:
        print(
            'AndGate is deprecated. Use circuit_utils.gates.And instead.',
            file=sys.stderr,
        )
        assert len(input_bits) == 2
        return input_bits[0] & input_bits[1]


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

    def add_gate(self, g: Gate) -> int:
        g.index = len(self.gates)
        self.gates.append(g)
        for w in g.inputs:
            w.outputs.append(g)
        g.output.input = g
        return g.index

    def add_wire(self, w: Wire) -> int:
        w.index = len(self.wires)
        self.wires.append(w)
        return w.index

    def extend_wires(self, wires: List[Wire]) -> List[int]:
        return [self.add_wire(w) for w in wires]

    def evaluate(self, input_bits: List[int]):

        assert len(self.inputs) == len(input_bits)
        n = len(self.gates)
        m = len(self.wires)
        in_deg: List[int] = [0] * n
        wire_ret: List[int] = [-1] * m
        for wire in self.wires:
            for out_gate in wire.outputs:
                if out_gate is not None:
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
