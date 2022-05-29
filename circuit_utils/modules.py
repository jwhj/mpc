from typing import List
from circuit import Circuit, Wire
from .gates import And, Xor, Or


class HalfAdder:
    def __init__(
        self,
        circuit: Circuit,
        in_0: Wire = None,
        in_1: Wire = None,
        out: Wire = None,
        carry: Wire = None,
    ) -> None:
        if in_0 is None:
            in_0 = Wire()
            circuit.add_wire(in_0)
        self.in_0 = in_0
        if in_1 is None:
            in_1 = Wire()
            circuit.add_wire(in_1)
        self.in_1 = in_1
        if out is None:
            out = Wire()
            circuit.add_wire(out)
        self.out = out
        if carry is None:
            carry = Wire()
            circuit.add_wire(carry)
        self.carry = carry

        circuit.add_gate(Xor(self.in_0, self.in_1, self.out))
        circuit.add_gate(And(self.in_0, self.in_1, self.carry))


class FullAdder:
    def __init__(
        self,
        circuit: Circuit,
        in_0: Wire = None,
        in_1: Wire = None,
        in_carry: Wire = None,
        out: Wire = None,
        carry: Wire = None,
    ) -> None:
        w1 = Wire()
        circuit.add_wire(w1)
        w2 = Wire()
        circuit.add_wire(w2)

        adder_1 = HalfAdder(circuit, in_0, in_1, w1, w2)
        self.in_0 = adder_1.in_0
        self.in_1 = adder_1.in_1

        w3 = Wire()
        circuit.add_wire(w3)
        adder_2 = HalfAdder(circuit, w1, in_carry, out, w3)
        self.in_carry = adder_2.in_1
        self.out = adder_2.out

        if carry is None:
            carry = Wire()
            circuit.add_wire(carry)
        self.carry = carry
        circuit.add_gate(Or(w2, w3, self.carry))


class Add:
    def __init__(
        self,
        circuit: Circuit,
        bit_length: int,
        in_0: List[Wire] = None,
        in_1: List[Wire] = None,
        out: List[Wire] = None,
    ) -> None:
        if in_0 is None:
            in_0 = [Wire() for _ in range(bit_length)]
            circuit.extend_wires(in_0)
        else:
            assert len(in_0) == bit_length
        if in_1 is None:
            in_1 = [Wire() for _ in range(bit_length)]
            circuit.extend_wires(in_1)
        else:
            assert len(in_1) == bit_length
        if out is None:
            out = [Wire() for _ in range(bit_length)]
            circuit.extend_wires(out)
        else:
            assert len(out) == bit_length
        self.in_0 = in_0
        self.in_1 = in_1
        self.out = out

        carry = Wire()
        circuit.add_wire(carry)
        HalfAdder(circuit, in_0[0], in_1[0], out[0], carry)
        for i in range(1, bit_length):
            tmp = Wire()
            circuit.add_wire(tmp)
            FullAdder(circuit, in_0[i], in_1[i], carry, out[i], tmp)
            carry = tmp
