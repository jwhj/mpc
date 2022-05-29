import random
import unittest
from circuit import Circuit
from circuit_utils import int2bits, bits2int
from circuit_utils.modules import HalfAdder, FullAdder, Add


class ModulesTest(unittest.TestCase):
    def test_half_adder(self):
        circuit = Circuit()
        adder = HalfAdder(circuit)
        circuit.inputs = [adder.in_0, adder.in_1]
        circuit.outputs = [adder.out, adder.carry]
        for x in range(2):
            for y in range(2):
                u, v = circuit.evaluate([x, y])
                assert u == (x + y) % 2 and v == int(x + y > 1)

    def test_full_adder(self):
        circuit = Circuit()
        adder = FullAdder(circuit)
        circuit.inputs = [adder.in_0, adder.in_1, adder.in_carry]
        circuit.outputs = [adder.out, adder.carry]
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    u, v = circuit.evaluate([x, y, z])
                    assert u == (x + y + z) % 2 and v == int(
                        x + y + z > 1
                    ), f'{x} {y} {z}'

    def test_adder(self):
        bit_length = 128
        circuit = Circuit()
        adder = Add(circuit, bit_length)
        circuit.inputs = adder.in_0 + adder.in_1
        circuit.outputs = adder.out
        for _ in range(10):
            x = random.randint(0, (1 << bit_length) - 1)
            y = random.randint(0, (1 << bit_length) - 1)
            x_bits = int2bits(x, bit_length)
            y_bits = int2bits(y, bit_length)
            result = circuit.evaluate(x_bits + y_bits)
            assert bits2int(result) == (x + y) % (1 << bit_length)


if __name__ == '__main__':
    unittest.main()
