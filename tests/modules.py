import random
import unittest
from circuit import Circuit
from circuit_utils.modules import HalfAdder, FullAdder, Adder


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
        adder = Adder(circuit, bit_length)
        circuit.inputs = adder.in_0 + adder.in_1
        circuit.outputs = adder.out
        for _ in range(10):
            inputs = [0, 0]
            input_bits = [[], []]
            for i in range(2):
                tmp = random.randint(0, (1 << bit_length) - 1)
                inputs[i] = tmp
                for j in range(bit_length):
                    input_bits[i].append(tmp % 2)
                    tmp >>= 1
            outputs = circuit.evaluate(input_bits[0] + input_bits[1])
            result = sum([x * (1 << i) for i, x in enumerate(outputs)])
            assert result == ((inputs[0] + inputs[1]) & ((1 << bit_length) - 1))


if __name__ == '__main__':
    unittest.main()
