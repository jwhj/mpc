import csprng
import unittest
from circuit import Circuit, Wire
from circuit_utils import int2bits, bits2int
from circuit_utils.modules import HalfAdder, FullAdder, Add, Negate, Subtract


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
            x = csprng.randint(0, (1 << bit_length) - 1)
            y = csprng.randint(0, (1 << bit_length) - 1)
            x_bits = int2bits(x, bit_length)
            y_bits = int2bits(y, bit_length)
            result = circuit.evaluate(x_bits + y_bits)
            assert bits2int(result) == (x + y) % (1 << bit_length)

    def test_negate(self):
        bit_length = 128
        circuit = Circuit()
        one = Wire()
        circuit.add_wire(one)
        negate = Negate(circuit, bit_length, one)
        circuit.inputs = [one] + negate.in_0
        circuit.outputs = negate.out
        for _ in range(10):
            x = csprng.randint(0, (1 << bit_length) - 1)
            x_bits = int2bits(x, bit_length)
            result = circuit.evaluate([1] + x_bits)
            assert (bits2int(result) + x) % (1 << bit_length) == 0

    def test_subtract(self):
        bit_length = 128
        circuit = Circuit()
        one = Wire()
        circuit.add_wire(one)
        subtract = Subtract(circuit, bit_length, one)
        circuit.inputs = [one] + subtract.in_0 + subtract.in_1
        circuit.outputs = subtract.out
        for _ in range(10):
            x = csprng.randint(0, (1 << bit_length) - 1)
            y = csprng.randint(0, (1 << bit_length) - 1)
            x_bits = int2bits(x, bit_length)
            y_bits = int2bits(y, bit_length)
            result = circuit.evaluate([1] + x_bits + y_bits)
            assert (bits2int(result) - x + y) % (1 << bit_length) == 0


if __name__ == '__main__':
    unittest.main()
