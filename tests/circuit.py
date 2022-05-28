import unittest
from circuit import Circuit, Wire, AndGate


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


if __name__ == '__main__':
    unittest.main()
