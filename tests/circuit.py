import unittest
from circuit import Circuit, Wire, AndGate
from circuit_utils.gates import Not


class CircuitTest(unittest.TestCase):
    def test_1(self):
        circuit = Circuit()
        wires = [Wire() for _ in range(5)]
        for w in wires:
            circuit.add_wire(w)

        g1 = AndGate(wires[0], wires[1], wires[2])
        circuit.add_gate(g1)
        g2 = AndGate(wires[2], wires[3], wires[4])
        circuit.add_gate(g2)
        circuit.inputs = [wires[0], wires[1], wires[3]]
        circuit.outputs = [wires[2], wires[4]]

        for x in range(2):
            for y in range(2):
                for z in range(2):
                    u, v = circuit.evaluate([x, y, z])
                    assert u == (x & y) and v == (x & y & z)

    def test_not(self):
        circuit = Circuit()
        w1 = Wire()
        circuit.add_wire(w1)
        w2 = Wire()
        circuit.add_wire(w2)

        circuit.add_gate(Not(w1, w2))
        circuit.inputs = [w1]
        circuit.outputs = [w2]

        for x in range(2):
            u = circuit.evaluate([x])
            assert x + u[0] == 1


if __name__ == '__main__':
    unittest.main()
